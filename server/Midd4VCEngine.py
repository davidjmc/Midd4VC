import json

class Midd4VCEngine:
    def __init__(self):
        self.vehicles = {}  # vehicle_id -> info
        self.jobs_queue = []  # lista de tarefas pendentes
        self.jobs_in_progress = {}  # job_id -> vehicle_id
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
        self.mqtt_client.publish(f"vc/vehicle/{vehicle_id}/register/response", "Registration Successful", qos=1)
        self.try_assign_jobs()

    def submit_job(self, job):
        if "job_id" not in job or "function" not in job or "client_id" not in job:
            print(f"[Midd4VCServer] Invalid job format: {job}")
            return

        self.jobs_queue.append(job)
        print(f"[Midd4VCServer] job received: {job['job_id']}")
        self.try_assign_jobs()

    def job_completed(self, result):
        job_id = result["job_id"]
        vehicle_id = result["vehicle_id"]
        client_id = result.get("client_id")
        print(f"[Midd4VCServer] job {job_id} completed by vehicle {vehicle_id}")

        if job_id in self.jobs_in_progress:
            del self.jobs_in_progress[job_id]
        else:
            print(f"[Midd4VCServer] job {job_id} not found in progress for vehicle {vehicle_id}")
            
        if self.mqtt_client and client_id:
            # topic = f"vc/application/{client_id}/job/result"
            topic = f"vc/client/{client_id}/job/result"
            self.mqtt_client.publish(topic, json.dumps(result), qos=1)
            print(f"[Midd4VCServer] Result sent to application {client_id} on topic {topic}")
        #else:
            #print(f"[Midd4VCServer] MQTT client not set or app_id missing. Cannot send result for job {job_id}")
    
        self.try_assign_jobs()

    def try_assign_jobs(self):
        available_vehicles = [
            vehicle_id for vehicle_id in self.vehicles
            if vehicle_id not in self.jobs_in_progress.values()
        ]

        while available_vehicles and self.jobs_queue:
            vehicle_id = available_vehicles.pop(0)
            job = self.jobs_queue.pop(0)
            job_id = job["job_id"]

            self.jobs_in_progress[job_id] = vehicle_id
            print(f"[Midd4VCServer] Assigning job {job_id} to vehicle {vehicle_id}")

            if self.mqtt_client:
                self.mqtt_client.publish(f"vc/vehicle/{vehicle_id}/job/assign", json.dumps(job), qos=0)
            else: 
                print(f"[Midd4VCServer] MQTT client not set. Cannot assign job {job_id}.")
