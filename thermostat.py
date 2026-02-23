import paho.mqtt.client as mqtt
import time

MY_ID = "ThisIsUniqueToMe"
mqttBroker = "broker.emqx.io" 

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Thermostat_Unique_ID_123")

try:
    client.connect(mqttBroker, 1883, 60)
    print(f"Connected to {mqttBroker}")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit()

while True:
    client.publish(f"{MY_ID}/thermostat/temp", "22")
    client.publish(f"{MY_ID}/thermostat/humidity", "60")
    client.publish(f"{MY_ID}/thermostat/mode", "cool")
    
    client.loop() 
    
    print("Data sent...")
    time.sleep(4)