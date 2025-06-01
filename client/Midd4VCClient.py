import json
import time
import threading
import os
from uuid import uuid4
from jobs import job_catalog

import paho.mqtt.client as mqtt

TOPIC_VEHICLE_REGISTER = "vc/vehicle/{vehicle_id}/register/request"
TOPIC_JOB_ASSIGN = "vc/vehicle/{vehicle_id}/job/assign"
TOPIC_JOB_SUBMIT = "vc/client/{client_id}/job/submit"
TOPIC_JOB_RESULT = "vc/client/{client_id}/job/result"

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))

class Midd4VCClient:
    def __init__(self, role, client_id, model=None, make=None, year=None):
        self.client_id = client_id
        self.role = role
        self.client = mqtt.Client(client_id=self.client_id, clean_session=False)
        self.client.on_message = self._internal_on_message
        self.client.on_connect = self._on_connect       
        self.client.on_disconnect = self._on_disconnect 
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        
        self.result_handler = None
        self.job_handler = None
        self.on_message_callback = None
        
        self.processed_jobs = set()
        self.running = False

        if self.role == "vehicle":
            self.info = {
                "vehicle_id": self.client_id,
                "model": model or "generic",
                "make": make or "generic",
                "year": year or 2000,
            }

    def set_result_handler(self, handler_fn):
        self.result_handler = handler_fn

    def set_job_handler(self, handler_fn):
        self.job_handler = handler_fn
    
    def set_on_message_callback(self, callback):
        self.on_message_callback = callback
       
    def start(self):
        try:
            self.client.connect(BROKER, PORT, 60)
        except Exception as e:
            print(f"[{self.role.capitalize()} {self.client_id}] Error connecting to MQTT: {e}")
            return
        
        self.client.loop_start()
        self.running = True

        if self.role == "client":
            self.client.subscribe(TOPIC_JOB_RESULT.format(client_id=self.client_id), qos=0)
            #print("[Client] Started and listening for job results...")

        elif self.role == "vehicle":
            self.client.subscribe(TOPIC_JOB_ASSIGN.format(vehicle_id=self.client_id), qos=0) 
            time.sleep(1)
            self.register()

        print(f"[{self.role.capitalize()} {self.client_id}] Started.")

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print(f"[{self.role.capitalize()} {self.client_id}] Stopped.")

    def register(self):
        if self.role == "vehicle":
            self.client.publish(TOPIC_VEHICLE_REGISTER, json.dumps(self.info), qos=0)
            print(f"[Vehicle {self.client_id}] Registring...")

    def submit_job(self, job):
        if "job_id" not in job:
            job["job_id"] = str(uuid4())
        job["client_id"] = self.client_id
        #print(f"[Client] Submitting job {job['job_id']}")
        self.client.publish(TOPIC_JOB_SUBMIT, json.dumps(job), qos=0)
        return job["job_id"]
    
    def _internal_on_message(self, client, userdata, msg):
        if self.on_message_callback:
            self.on_message_callback(client, userdata, msg)
        else:
            self.on_message(client, userdata, msg)
    
    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            print(f"[{self.role.capitalize()} {self.client_id}] Invalid JSON message: {payload}")
            return

        if self.role == "client":
            if self.result_handler:
                result = {
                    'job_id': data['job_id'],
                    'vehicle_id': data['vehicle_id'],
                    'result': data['result']
                }
                # self.result_handler(data)
                self.result_handler(result)
            else:
                print(f"[Client {self.client_id}] Result received: {data}")
        elif self.role == "vehicle":
            threading.Thread(target=self.execute_job, args=(data,), daemon=True).start()
    
    def execute_job(self, job):
        if not self.client.is_connected():
            print(f"[Vehicle {self.client_id}] Cannot execute job. MQTT client not connected.")
            return

        job_id = job.get("job_id")
        client_id = job.get("client_id")

        if job_id is None:
            print(f"[Vehicle {self.client_id}] Job received without job_id, ignoring.")
            return

        if job_id in self.processed_jobs:
            print(f"[Vehicle {self.client_id}] Duplicate job {job_id} ignored.")
            return
        
        self.processed_jobs.add(job_id)

        if client_id is None:
            print(f"[Vehicle {self.client_id}] Warning: client_id missing in job. Result will not be sent.")
            return

        # print(f"[Vehicle {self.client_id}] Executando tarefa {job_id} ({job.get('function')}) com args {job.get('args', [])}")
        print(f"[Vehicle {self.client_id}] Executing job {job_id}.")

        
        if self.job_handler:
            result = self.job_handler(job)
        else:
            function_name = job.get("function")
            args = job.get("args", [])
            try:
                func = job_catalog.JOBS_CATALOG.get(function_name)
                print(func)
                result_value = func(*args)
                result = {
                    "job_id": job_id,
                    "vehicle_id": self.client_id,
                    "result": result_value,
                }
            except Exception as e:
                result = {
                    "job_id": job_id,
                    "vehicle_id": self.client_id,
                    "error": f"Error executing job: {str(e)}"
                }

        self.client.publish(TOPIC_JOB_RESULT.format(client_id=client_id), json.dumps(result), qos=0)
    
    def _on_connect(self, client, userdata, flags, rc):
        print(f"[{self.role.capitalize()} {self.client_id}] Connected to broker with code: {rc}")
        if rc == 0:
            if self.role == "client":
                self.client.subscribe(TOPIC_JOB_RESULT.format(client_id=self.client_id), qos=0)
            elif self.role == "vehicle":
                self.client.subscribe(TOPIC_JOB_ASSIGN.format(vehicle_id=self.client_id), qos=0)
                print(f"[Vehicle {self.client_id}] Re-subscribed to topic: {TOPIC_JOB_ASSIGN.format(vehicle_id=self.client_id)}")
        else:
            print(f"[{self.role.capitalize()} {self.client_id}] Connection error: code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[{self.role.capitalize()} {self.client_id}] Disconnected from broker with code: {rc}")
        if self.running and rc != 0:
            print(f"[{self.role.capitalize()} {self.client_id}] Trying to reconnect...")
            try:
                self.client.reconnect()
            except Exception as e:
                print(f"[{self.role.capitalize()} {self.client_id}] Reconnection failed: {e}")
