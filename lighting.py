import paho.mqtt.client as mqtt
import time

MY_ID = "ThisIsUniqueToMe"
mqttBroker = "broker.emqx.io" 

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Bedroom_Tubelight1")

try:
    client.connect(mqttBroker, 1883, 60)
    print(f"Connected to {mqttBroker}")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit()

while True:
    client.publish(f"{MY_ID}/lighting/status", "on")
    client.publish(f"{MY_ID}/lighting/brightness", "80")
    client.publish(f"{MY_ID}/lighting/color", "white")
    
    client.loop() 
    
    print("Data sent...")
    time.sleep(4)