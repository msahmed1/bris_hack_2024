import paho.mqtt.client as mqtt
import threading

# MQTT setup
broker_address = 'localhost'  # Define broker address
port = 1883  # Default MQTT port
keepalive = 60  # Keepalive interval
MQTT_TOPIC = "userInput"


class MQTTClient:
    def __init__(self):
        self.mqtt_client = mqtt.Client()

        # Assign event callbacks
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Connect to the MQTT broker
        self.mqtt_client.connect(broker_address, port, keepalive)

        # Start the loop in a separate thread
        threading.Thread(target=self.mqtt_client.loop_forever).start()

    def publish_state(self, message):
        self.mqtt_client.publish("robot/userInput", message)

    # Subscribe to the desired topic upon connecting with the broker
    def on_connect(self, client, userdata, flags, rc):
        # print("Connected with result code " + str(rc))
        self.mqtt_client.subscribe(MQTT_TOPIC)

    # Define on_message event Handler
    def on_message(self, msg):
        # print(f"Message received: Topic: {msg.topic}, Message: {str(msg.payload.decode('utf-8'))}")
        message = str(msg.payload.decode('utf-8'))
        if message == "up":
            return "up"
        elif message == "down":
            return "down"

    def disconnect(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
