import time
import threading
from Midd4VCClient import Midd4VCClient
from jobs import job_catalog

class Vehicle:
    def __init__(self, vehicle_id, model, make, year):
        self.vehicle_id = vehicle_id
        self.model = model
        self.make = make
        self.year = year

    def job_handler(self, job):
        function_name = job.get("function")
        args = job.get("args", [])

        try:
            func = job_catalog.JOBS_CATALOG.get(function_name)
            result_value = func(*args)
            return {
                "job_id": job["job_id"],
                "vehicle_id": self.vehicle_id,
                "result": result_value
            }
        except (AttributeError, ImportError, TypeError) as e:
            print(f"[Vehicle] Function execution failed: '{function_name}': {e}")
            return {
                "job_id": job.get("job_id", "unknown"),
                "vehicle_id": self.vehicle_id,
                "error": f"Function execution failed: {str(e)}"
            }

def run_vehicle(vehicle_id):
    vehicle = Vehicle(vehicle_id=vehicle_id, model="ModelX", make="MakeY", year=2020)
    vc = Midd4VCClient(role="vehicle", client_id=vehicle.vehicle_id, model=vehicle.model, make=vehicle.make, year=vehicle.year)
    vc.set_job_handler(vehicle.job_handler)
    vc.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print(f"Stopping vehicle {vehicle_id}...")
        vc.stop()

if __name__ == "__main__":
    vehicle_ids = [f"veh{i}" for i in range(1, 6)]  # 500 vehicles
    threads = []

    for vid in vehicle_ids:
        t = threading.Thread(target=run_vehicle, args=(vid,))
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("Stopping all vehicles...")
        # Threads não tem método stop, então precisa de outra estratégia para parar (por exemplo, flags)
