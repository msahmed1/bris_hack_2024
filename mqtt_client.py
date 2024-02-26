import paho.mqtt.client as mqtt
import threading

# MQTT setup
broker_address = 'localhost'  # Define broker address
port = 1883  # Default MQTT port
keepalive = 60  # Keepalive interval
MQTT_TOPIC = "userInput"
topics = ["userInput", "acknowldege"] 


class MQTTClient:
    def __init__(self):
        self.latest_messages = {"userInput": None, "acknowledge": None}
        self.mqtt_client = mqtt.Client()

        # Assign event callbacks
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Connect to the MQTT broker
        self.mqtt_client.connect(broker_address, port, keepalive)

        # Start the loop in a separate thread
        threading.Thread(target=self.mqtt_client.loop_forever).start()

    def publish_state(self, topic, message):
        # print(f"Publishing message: {message} to topic: {topic}")
        if topic in self.latest_messages:  # Check if it's a valid topic
            self.mqtt_client.publish(topic, message)
        else:
            print(f"Invalid topic: {topic}")

    def on_connect(self, client, userdata, flags, rc):
        # print("Connected with result code " + str(rc))
        for topic in topics:
            self.mqtt_client.subscribe(topic)
    
    def on_message(self, client, userdata, msg):
        self.latest_messages[msg.topic] = msg.payload.decode('utf-8')
        # print(f"Message received: {msg.payload.decode('utf-8')}")

    def get_latest_message(self, topic):
        if topic in self.latest_messages:
            latest_message = self.latest_messages[topic]
            # print(f"in get_latest_message for {topic}, latest_message: {latest_message}")
            return latest_message
        else:
            # print(f"Invalid topic: {topic}")
            return None

    def disconnect(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
