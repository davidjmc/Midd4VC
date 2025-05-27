import sys, os, time
from Midd4VCClient import Midd4VCClient
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tasks')))

class Vehicle:
    def __init__(self, vehicle_id, model, make, year):
        self.vehicle_id = vehicle_id
        self.model = model
        self.make = make
        self.year = year
    
    def task_handler(self, task):
        function_name = task.get("function")
        args = task.get("args", [])

        try:
            # Tenta importar a função dinamicamente do módulo tasks.tasks
            tasks_module = importlib.import_module("tasks.tasks")
            func = getattr(tasks_module, function_name)

            result_value = func(*args)
            return {
                "task_id": task["task_id"],
                "vehicle_id": self.vehicle_id,
                "result": result_value
            }
        except (AttributeError, ImportError, TypeError) as e:
            print(f"[Vehicle] Erro ao executar função '{function_name}': {e}")
            return {
                "task_id": task["task_id"],
                "vehicle_id": self.vehicle_id,
                "error": f"Function execution failed: {str(e)}"
            }

if __name__ == "__main__":
    vehicle = Vehicle(vehicle_id="veh123", model="ModelX", make="MakeY", year=2020)
    vc = Midd4VCClient(role="vehicle", client_id="veh123")
    vc.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping vehicle...")
        vc.stop()
