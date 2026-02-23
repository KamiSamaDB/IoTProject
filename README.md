# IoT Access Control

A web-based access control panel for MQTT IoT devices. A FastAPI backend manages independent subscriber clients, each with per-publisher permissions that can be toggled live from the browser. Incoming messages are streamed in real-time via WebSocket to a feed display.

---

## Project Structure

```
.
├── backend.py          # FastAPI server + MQTT subscriber clients
├── thermostat.py       # Publisher: temperature, humidity, mode
├── camera.py           # Publisher: camera snapshots
├── insurance.py        # Standalone subscriber (legacy reference)
├── localmonitor.py     # Standalone subscriber (legacy reference)
├── static/
│   └── index.html      # Frontend (single-page app)
└── requirements.txt
```

---

## Prerequisites

- Python 3.11 or higher
- Internet access (connects to the public broker `broker.emqx.io`)

---

## Setup

### 1. Create a virtual environment

**Windows**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```
pip install fastapi "uvicorn[standard]" paho-mqtt python-multipart
```

Or by using `requirements.txt`:

```
pip install -r requirements.txt
```

---

## Running the Application

All three processes need to run simultaneously, each in its own terminal.

### Terminal 1 — Thermostat publisher

**Windows**
```powershell
.venv\Scripts\python thermostat.py
```

**macOS / Linux**
```bash
.venv/bin/python thermostat.py
```

### Terminal 2 — Camera publisher

**Windows**
```powershell
.venv\Scripts\python camera.py
```

**macOS / Linux**
```bash
.venv/bin/python camera.py
```

### Terminal 3 — Backend server

**Windows**
```powershell
.venv\Scripts\python backend.py
```

**macOS / Linux**
```bash
.venv/bin/python backend.py
```

Then open http://localhost:8000 in a browser.

---

## Usage

**Access Permissions table** — rows are publishers (thermostat, camera), columns are subscribers (localmonitor, insurance). Each cell is a toggle button. Clicking it grants or revokes that subscriber's ability to receive messages from that publisher in real time.

**Live Data Feed** — select a subscriber using the buttons below the permissions table to view their incoming message stream. Use the publisher filter pills to narrow the feed to a specific data source. The feed updates live without polling.

---

## How It Works

- Each subscriber party (localmonitor, insurance) is represented by a dedicated `paho-mqtt` client in the backend. When access to a publisher is granted, the client subscribes to that topic wildcard; when revoked, it unsubscribes immediately.
- The FastAPI server exposes REST endpoints (`/api/state`, `/api/config`, `/api/toggle/{subscriber}/{publisher}`) for reading and modifying the permission matrix.
- A single WebSocket endpoint (`/ws`) broadcasts all received MQTT messages to connected browsers. The frontend filters display client-side based on the active subscriber view and publisher filters.

---

## Configuration

To change the MQTT broker or device ID, edit the constants at the top of `backend.py`, `thermostat.py`, and `camera.py`:

```python
MY_ID    = "ThisIsUniqueToMe"   # Namespace prefix for all topics
BROKER   = "broker.emqx.io"    # MQTT broker hostname
```

To add a new publisher, add an entry to the `PUBLISHERS` dict in `backend.py`:

```python
PUBLISHERS: dict[str, str] = {
    "thermostat": f"{MY_ID}/thermostat/#",
    "camera":     f"{MY_ID}/camera/#",
    "new_device": f"{MY_ID}/new_device/#",   # add here
}
```

To add a new subscriber, add an entry to the `SUBSCRIBERS` dict in `backend.py`:

```python
SUBSCRIBERS: dict[str, SubscriberClient] = {
    "localmonitor": SubscriberClient("localmonitor", "LocalMonitor_ACL_7f3a"),
    "insurance":    SubscriberClient("insurance",    "Insurance_ACL_9b2c"),
    "newparty":     SubscriberClient("newparty",     "NewParty_ACL_xxxx"),  # add here
}
```

Both the permission matrix and the feed selector update automatically on next page load.
