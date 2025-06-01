import time
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
            # jobs_module = importlib.import_module("jobs")
            # func = getattr(jobs_module, function_name)
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

if __name__ == "__main__":
    vehicle = Vehicle(vehicle_id="veh1", model="ModelX", make="MakeY", year=2020)
    vc = Midd4VCClient(role="vehicle", client_id=vehicle.vehicle_id, model=vehicle.model, make=vehicle.make, year=vehicle.year)
    vc.set_job_handler(vehicle.job_handler)
    vc.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopping vehicle...")
        vc.stop()
