import os
import json
import time
import paho.mqtt.client as mqtt
from Midd4VCEngine import Midd4VCEngine

TOPIC_VEHICLE_REGISTER = "vc/vehicle/+/register/request"
TOPIC_JOB_SUBMIT = "vc/client/+/job/submit"
TOPIC_JOB_ASSIGN = "vc/vehicle/{vehicle_id}/job/assign"
TOPIC_JOB_RESULT = "vc/client/+/job/result"


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
        if rc != 0:
            try:
                self.client.reconnect()
            except Exception as e:
                print(f"[Midd4VCServer] Reconnect failed: {e}")

    def start(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

        self.client.subscribe(TOPIC_VEHICLE_REGISTER, qos=0); #print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_VEHICLE_REGISTER}")
        self.client.subscribe(TOPIC_JOB_SUBMIT, qos=0); #print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_JOB_SUBMIT}")
        self.client.subscribe(TOPIC_JOB_RESULT, qos=0); #print(f"[{self.client._client_id.decode()}] Subscribed to {TOPIC_JOB_RESULT}")
        print("[Midd4VCServer] Server started and subscribed to topics.")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            #print(f"[Midd4VCServer] Received on {msg.topic}: {payload}")

            if msg.topic.endswith("register/request"):
                vehicle_info = json.loads(payload)
                self.engine.register_vehicle(vehicle_info)

            elif msg.topic.endswith("job/submit"):
                job = json.loads(payload)
                self.engine.submit_job(job)

            elif msg.topic.endswith("job/result"):
                result = json.loads(payload)
                self.engine.job_completed(result)
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
        # print("[Midd4VCServer] Stopping server...")
        server.stop()
