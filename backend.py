import asyncio
import threading
from contextlib import asynccontextmanager
from typing import Set

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

MY_ID = "ThisIsUniqueToMe"
BROKER = "broker.emqx.io"

PUBLISHERS: dict[str, str] = {
    "thermostat": f"{MY_ID}/thermostat/#",
    "camera":     f"{MY_ID}/camera/#",
    "lighting":   f"{MY_ID}/lighting/#",
}


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, payload: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


class SubscriberClient:
    """One MQTT client per subscriber party.
    Tracks enabled access per publisher independently.
    """

    def __init__(self, name: str, client_id: str):
        self.name = name
        self.client_id = client_id
        # { publisher_name: bool }
        self.access: dict[str, bool] = {pub: False for pub in PUBLISHERS}
        self._client: mqtt.Client | None = None
        self._connected = False
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue | None = None


    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connected = True
            for pub, enabled in self.access.items():
                if enabled:
                    client.subscribe(PUBLISHERS[pub])

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected = False

    def _on_message(self, client, userdata, message):
        if self._loop and self._queue:
            publisher = "unknown"
            for pub, topic_filter in PUBLISHERS.items():
                prefix = topic_filter.rstrip("/#")
                if message.topic.startswith(prefix):
                    publisher = pub
                    break
            msg = {
                "subscriber": self.name,
                "publisher":  publisher,
                "topic":      message.topic,
                "payload":    message.payload.decode("utf-8", errors="replace"),
            }
            asyncio.run_coroutine_threadsafe(self._queue.put(msg), self._loop)


    def start(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue):
        self._loop = loop
        self._queue = queue
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        try:
            self._client.connect(BROKER, 1883, 60)
            self._client.loop_start()
        except Exception as exc:
            print(f"[{self.name}] MQTT connect error: {exc}")

    def stop(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()


    def set_publisher_access(self, publisher: str, enabled: bool):
        with self._lock:
            self.access[publisher] = enabled
            if not self._connected or not self._client:
                return
            topic = PUBLISHERS[publisher]
            if enabled:
                self._client.subscribe(topic)
            else:
                self._client.unsubscribe(topic)



SUBSCRIBERS: dict[str, SubscriberClient] = {
    "localmonitor":   SubscriberClient("localmonitor",   "LocalMonitor_ACL_7f3a"),
    "insurance":      SubscriberClient("insurance",      "Insurance_ACL_9b2c"),
    "fire_department": SubscriberClient("fire_department", "FireDepartment_ACL_5c4d"),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    for sub in SUBSCRIBERS.values():
        sub.start(loop, queue)

    task = asyncio.create_task(_broadcast_loop(queue))
    yield
    task.cancel()
    for sub in SUBSCRIBERS.values():
        sub.stop()


async def _broadcast_loop(queue: asyncio.Queue):
    while True:
        msg = await queue.get()
        await manager.broadcast(msg)



app = FastAPI(title="IoT Access Control", lifespan=lifespan)


@app.get("/api/state")
def get_state():
    """Return full access matrix: { subscriber: { publisher: bool } }"""
    return {
        name: dict(sub.access)
        for name, sub in SUBSCRIBERS.items()
    }


@app.get("/api/config")
def get_config():
    """Return static list of subscribers and publishers for the UI."""
    return {
        "subscribers": list(SUBSCRIBERS.keys()),
        "publishers":  list(PUBLISHERS.keys()),
    }


@app.post("/api/toggle/{subscriber}/{publisher}")
def toggle_access(subscriber: str, publisher: str):
    if subscriber not in SUBSCRIBERS:
        return {"error": f"Unknown subscriber '{subscriber}'"}
    if publisher not in PUBLISHERS:
        return {"error": f"Unknown publisher '{publisher}'"}
    sub = SUBSCRIBERS[subscriber]
    new_state = not sub.access[publisher]
    sub.set_publisher_access(publisher, new_state)
    return {"subscriber": subscriber, "publisher": publisher, "enabled": new_state}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=False)
