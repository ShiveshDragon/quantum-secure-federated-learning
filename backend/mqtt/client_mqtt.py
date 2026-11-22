"""Optional MQTT transport adapter. Core experiments do not require a broker."""
import paho.mqtt.client as mqtt
from .payload import serialize_message, update_topic, global_model_topic


class IoTClientMQTT:
    def __init__(self, client_id, host="localhost", port=1883):
        self.client_id, self.host, self.port = client_id, host, port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)

    def connect(self):
        self.client.connect(self.host, self.port)

    def publish_update(self, message):
        return self.client.publish(update_topic(self.client_id), serialize_message(message), qos=1)

    def subscribe_global(self, callback):
        self.client.subscribe(global_model_topic(), qos=1)
        self.client.message_callback_add(global_model_topic(), callback)
