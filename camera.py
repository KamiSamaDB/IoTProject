import paho.mqtt.client as mqtt
import time

MY_ID = "ThisIsUniqueToMe"
mqttBroker = "broker.emqx.io" 
count = 1

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Camera_Unique_ID_456")

try:
    client.connect(mqttBroker, 1883, 60)
    print(f"Connected to {mqttBroker}")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit()

while True:

    client.publish(f"{MY_ID}/camera/snapshots", f"snapshot{count}.png")
    
    client.loop() 
    
    print("Data sent...")
    count += 1
    time.sleep(4)