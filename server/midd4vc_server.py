import os
import json
import time
import paho.mqtt.client as mqtt
from middleware import MiddlewareCore

TOPIC_VEHICLE_REGISTER = "vc/vehicle/register"
TOPIC_TASK_SUBMIT = "vc/task/submit"
TOPIC_TASK_ASSIGN = "vc/task/assign"
TOPIC_TASK_RESULT = "vc/task/result"

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))

class Midd4VCServer:
    def __init__(self):
        self.core = MiddlewareCore()
        self.client = mqtt.Client("Midd4VCServer")
        self.core.set_mqtt_client(self.client)

        self.client.on_connect = self.on_connect
        self.client.on_message = self._internal_on_message
        self.on_message_callback = None

    def connect(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[{self.client._client_id.decode()}] Connected with result code {rc}")

    def start(self):
        self.connect()
        self.client.subscribe(TOPIC_VEHICLE_REGISTER)
        print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_VEHICLE_REGISTER}")
        self.client.subscribe(TOPIC_TASK_SUBMIT)
        print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_TASK_SUBMIT}")
        self.client.subscribe(TOPIC_TASK_RESULT)
        print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_TASK_RESULT}")
        print("[Midd4VCServer] Server started and listening...")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"[Midd4VCServer] Received on {msg.topic}: {payload}")

        if msg.topic == TOPIC_VEHICLE_REGISTER:
            vehicle_info = json.loads(payload)
            self.core.register_vehicle(vehicle_info)

        elif msg.topic == TOPIC_TASK_SUBMIT:
            task = json.loads(payload)
            self.core.submit_task(task)

        elif msg.topic == TOPIC_TASK_RESULT:
            result = json.loads(payload)
            self.core.task_completed(result)

    def stop(self):
        self.client.disconnect()

    def set_on_message_callback(self, callback):
        self.on_message_callback = callback

    def _internal_on_message(self, client, userdata, msg):
        if self.on_message_callback:
            self.on_message_callback(client, userdata, msg)
        else:
            self.on_message(client, userdata, msg)

if __name__ == "__main__":
    server = Midd4VCServer()
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down Midd4VCServer...")
        server.stop()
