import sys
import os
import time
import importlib
from multiprocessing import Process
from Midd4VCClient import Midd4VCClient

# Adiciona o caminho para a pasta tasks
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tasks')))

class Vehicle:
    def __init__(self, vehicle_id, model, make, year):
        self.vehicle_id = vehicle_id
        self.model = model
        self.make = make
        self.year = year
    
    def task_handler(self, task):
        if self.vehicle_id == "veh1":
            print(f"[{self.vehicle_id}] Delay artificial de 1s para teste")
            time.sleep(1)  # delay só para o veículo 1

        function_name = task.get("function")
        args = task.get("args", [])

        try:
            tasks_module = importlib.import_module("tasks")
            func = getattr(tasks_module, function_name)
            result_value = func(*args)
            return {
                "task_id": task["task_id"],
                "vehicle_id": self.vehicle_id,
                "result": result_value
            }
        except (AttributeError, ImportError, TypeError) as e:
            print(f"[Vehicle {self.vehicle_id}] Erro ao executar função '{function_name}': {e}")
            return {
                "task_id": task.get("task_id", "unknown"),
                "vehicle_id": self.vehicle_id,
                "error": f"Function execution failed: {str(e)}"
            }

def run_vehicle(vehicle_id, model, make, year):
    vehicle = Vehicle(vehicle_id, model, make, year)
    vc = Midd4VCClient(role="vehicle", client_id=vehicle.vehicle_id, model=vehicle.model, make=vehicle.make, year=vehicle.year)
    vc.set_task_handler(vehicle.task_handler)
    vc.start()
    print(f"[Vehicle {vehicle.vehicle_id}] iniciado.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"[Vehicle {vehicle.vehicle_id}] Parando...")
        vc.stop()

if __name__ == "__main__":
    vehicles_info = [
        ("veh001", "ModelA", "MakeX", 2018),
        ("veh002", "ModelB", "MakeY", 2019),
        ("veh003", "ModelC", "MakeZ", 2020),
    ]

    processes = []
    for vid, model, make, year in vehicles_info:
        p = Process(target=run_vehicle, args=(vid, model, make, year))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Parando todos os veículos...")
        for p in processes:
            p.terminate()
