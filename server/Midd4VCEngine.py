import json

class Midd4VCEngine:
    def __init__(self):
        self.vehicles = {}  # vehicle_id -> info
        self.tasks_queue = []  # lista de tarefas pendentes
        self.tasks_in_progress = {}  # task_id -> vehicle_id
        self.mqtt_client = None  # será setado pelo servidor

    def set_mqtt_client(self, mqtt_client):
        self.mqtt_client = mqtt_client

    def register_vehicle(self, vehicle_info):
        vehicle_id = vehicle_info["vehicle_id"]
        
        if vehicle_id in self.vehicles:
            print(f"[Midd4VCServer] Vehicle {vehicle_id} already registered.")
            return
        
        self.vehicles[vehicle_id] = vehicle_info
        print(f"[Midd4VCServer] Vehicle registered: {vehicle_id}")
        self.mqtt_client.publish(f"vc/vehicle/{vehicle_id}/register/response", "Registration Successful", qos=0)
        self.try_assign_tasks()

    def submit_task(self, task):
        if "task_id" not in task or "function" not in task:
            print(f"[Midd4VCServer] Invalid task format: {task}")
            return

        self.tasks_queue.append(task)
        print(f"[Midd4VCServer] Task received: {task['task_id']}")
        self.try_assign_tasks()

    def task_completed(self, result):
        task_id = result["task_id"]
        vehicle_id = result["vehicle_id"]
        print(f"[Midd4VCServer] Task {task_id} completed by vehicle {vehicle_id}")

        if task_id in self.tasks_in_progress:
            del self.tasks_in_progress[task_id]
        else:
            print(f"[Midd4VCServer] Task {task_id} not found in progress for vehicle {vehicle_id}")
            
        self.try_assign_tasks()

    def try_assign_tasks(self):
        available_vehicles = [
            vehicle_id for vehicle_id in self.vehicles
            if vehicle_id not in self.tasks_in_progress.values()
        ]

        while available_vehicles and self.tasks_queue:
            vehicle_id = available_vehicles.pop(0)
            task = self.tasks_queue.pop(0)
            task_id = task["task_id"]

            self.tasks_in_progress[task_id] = vehicle_id
            print(f"[Midd4VCServer] Assigning task {task_id} to vehicle {vehicle_id}")

            if self.mqtt_client:
                self.mqtt_client.publish(f"vc/vehicle/{vehicle_id}/task/assign", json.dumps(task), qos=0)
            else: 
                print(f"[Midd4VCServer] MQTT client not set. Cannot assign task {task_id}.")
