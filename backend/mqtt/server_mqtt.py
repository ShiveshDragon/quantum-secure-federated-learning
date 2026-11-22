import paho.mqtt.client as mqtt
from .payload import serialize_message, global_model_topic


class FLServerMQTT:
    def __init__(self, host="localhost", port=1883):
        self.host, self.port = host, port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def connect(self):
        self.client.connect(self.host, self.port)

    def publish_global_model(self, message):
        return self.client.publish(global_model_topic(), serialize_message(message), qos=1)

    def subscribe_updates(self, callback, client_ids):
        for cid in client_ids:
            self.client.subscribe(f"iot/fl/{cid}/update", qos=1)
        self.client.on_message = callback
