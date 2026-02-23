import paho.mqtt.client as mqtt

MY_ID = "ThisIsUniqueToMe"
mqttBroker = "broker.emqx.io" 

def on_message(client, userdata, message):
    print(f"Received message: {message.payload.decode()} on topic {message.topic}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Thermostat_Listener_123")
client.on_message = on_message

client.connect(mqttBroker)

client.subscribe(f"{MY_ID}/thermostat/#")
client.subscribe(f"{MY_ID}/camera/#")

print("Waiting for data... (Press Ctrl+C to stop)")

client.loop_forever()