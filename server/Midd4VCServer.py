import os
import json
import time
import paho.mqtt.client as mqtt
from Midd4VCEngine import Midd4VCEngine

TOPIC_VEHICLE_REGISTER = "vc/vehicle/register"
TOPIC_TASK_SUBMIT = "vc/task/submit"
#TOPIC_TASK_ASSIGN = "vc/task/assign"
TOPIC_TASK_ASSIGN = "vc/vehicle/{vehicle_id}/task/assign"
TOPIC_TASK_RESULT = "vc/task/result"

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))

class Midd4VCServer:
    def __init__(self):
        self.engine = Midd4VCEngine()
        self.client = mqtt.Client("Midd4VCServer")
        self.engine.set_mqtt_client(self.client)
    
        self.client.on_connect = self.on_connect
        self.client.on_message = self._internal_on_message
        self.client.on_disconnect = self.on_disconnect
        self.on_message_callback = None

    def on_connect(self, client, userdata, flags, rc):
        print(f"[{self.client._client_id.decode()}] Connected with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        print(f"[{self.client._client_id.decode()}] Disconnected with result code {rc}")
        if rc != 0:  # Se a desconexão não foi normal, tentamos reconectar
            print("[Midd4VCServer] Reconnecting...")
            self.connect()  # Tentar reconectar

    def start(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

        self.client.subscribe(TOPIC_VEHICLE_REGISTER); print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_VEHICLE_REGISTER}")
        self.client.subscribe(TOPIC_TASK_SUBMIT); print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_TASK_SUBMIT}")
        self.client.subscribe(TOPIC_TASK_RESULT); print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_TASK_RESULT}")
        print("[Midd4VCServer] Server started and subscribed to topics.")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            print(f"[Midd4VCServer] Received on {msg.topic}: {payload}")

            if msg.topic == TOPIC_VEHICLE_REGISTER:
                vehicle_info = json.loads(payload)
                self.engine.register_vehicle(vehicle_info)

            elif msg.topic == TOPIC_TASK_SUBMIT:
                task = json.loads(payload)
                self.engine.submit_task(task)

            elif msg.topic == TOPIC_TASK_RESULT:
                result = json.loads(payload)
                self.engine.task_completed(result)
        except Exception as e:
            print(f"[Midd4VCServer] Error processing message: {str(e)}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("[Midd4VCServer] Server stopped.")

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
        print("[Midd4VCServer] Stopping server...")
        server.stop()
