import json
import time
import threading
import importlib
import sys, os
from uuid import uuid4

import paho.mqtt.client as mqtt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tasks')))

# topics
TOPIC_REGISTER = "vc/vehicle/register"
TOPIC_ASSIGN = "vc/vehicle/{vehicle_id}/task/assign"
TOPIC_TASK_SUBMIT = "vc/task/submit"
TOPIC_TASK_RESULT = "vc/task/result"

# settings
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))

class Midd4VCClient:
    def __init__(self, role, client_id, model=None, make=None, year=None):
        self.client_id = client_id
        self.client = mqtt.Client(client_id=self.client_id, clean_session=False)  # Garantir clean_session=False
        self.client.on_message = self._internal_on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        self.result_handler = None
        self.on_message_callback = None


        self.tasks_module = importlib.import_module("tasks")
        self.running = False

        self.role = role
        if self.role == "vehicle":
            self.info = {
                "vehicle_id": self.client_id,
                "model": model or "generic",
                "make": make or "generic",
                "year": year or 2000,
            }

    def set_result_handler(self, handler_fn):
        self.result_handler = handler_fn
    
    def start(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()
        self.running = True

        if self.role == "client":
            self.client.subscribe(TOPIC_TASK_RESULT, qos=0)
            print("[Client] Started and listening for task results...")
        elif self.role == "vehicle":
            self.client.subscribe(TOPIC_ASSIGN.format(vehicle_id=self.client_id), qos=0) 
            time.sleep(1)
            self.register()

        print(f"[{self.role.capitalize()} {self.client_id}] Started.")

    def stop(self):
        self.running = False
        self.client.disconnect()
        print(f"[{self.role.capitalize()} {self.client_id}] Stopped.")

    def register(self):
        self.client.publish(TOPIC_REGISTER, json.dumps(self.info), qos=0)

    def submit_task(self, task):
        if "task_id" not in task:
            task["task_id"] = str(uuid4())
        print(f"[Client] Submitting task {task['task_id']}")
        self.client.publish(TOPIC_TASK_SUBMIT, json.dumps(task), qos=0)
        return task["task_id"]

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        data = json.loads(payload)

        if self.role == "client":
            print(f"[Client {self.client_id}] Received message on {msg.topic}: {data}")
            if self.result_handler:
                self.result_handler(data)
        elif self.role == "vehicle":
            threading.Thread(target=self.execute_task, args=(data,)).start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        if self.role == "client":
            self.client.subscribe(TOPIC_TASK_RESULT, qos=0)  # Garantir QoS 1
        elif self.role == "vehicle":
            # Após reconectar, re-assinar o tópico corretamente
            self.client.subscribe(TOPIC_ASSIGN.format(vehicle_id=self.client_id), qos=0)  # Garantir QoS 1
            print(f"[Vehicle {self.client_id}] Re-subscribed to {TOPIC_ASSIGN.format(vehicle_id=self.client_id)}")

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected with result code {rc}")
        if self.running:
            print("Attempting to reconnect...")
            self.client.reconnect()

    def execute_task(self, task):
        # Verifique se a conexão MQTT está ativa antes de tentar executar a tarefa
        if not self.client.is_connected():
            print(f"[Vehicle {self.client_id}] Unable to execute task. MQTT client is not connected.")
            return
    
        task_id = task.get("task_id")
        function_name = task.get("function")
        args = task.get("args", [])

        # Validar se a função e os argumentos estão presentes
        if not function_name:
            print(f"[Vehicle {self.client_id}] Error: No function specified in the task.")
            return

        print(f"[Vehicle {self.client_id}] Executing task {task_id} ({function_name}) with args {args}")

        try:
            func = getattr(self.tasks_module, function_name)
            result_value = func(*args)
        except Exception as e:
            result_value = f"Error executing task: {str(e)}"

        result = {
            "task_id": task_id,
            "vehicle_id": self.client_id,
            "result": result_value,
        }

        self.client.publish(TOPIC_TASK_RESULT, json.dumps(result), qos=0)  # Garantir QoS 1 para entrega de resultados

    def set_task_handler(self, handler_fn):
        self.task_handler = handler_fn
    
    def set_on_message_callback(self, callback):
        self.on_message_callback = callback

    def _internal_on_message(self, client, userdata, msg):
        if self.on_message_callback:
            self.on_message_callback(client, userdata, msg)
        else:
            self.on_message(client, userdata, msg)
