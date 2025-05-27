import sys, os, time
from midd4vc_client import Midd4VCClient
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
            # Importa dinamicamente o módulo de tarefas
            tasks_module = importlib.import_module("tasks.tasks")
            func = getattr(tasks_module, function_name)

            # Executa a função com os argumentos fornecidos
            result_value = func(*args)
            print(f"[Vehicle {self.vehicle_id}] Task {task['task_id']} executed with result: {result_value}")
            
            return {
                "task_id": task["task_id"],
                "vehicle_id": self.vehicle_id,
                "result": result_value
            }
        except (AttributeError, ImportError, TypeError) as e:
            # Se ocorrer algum erro ao executar a tarefa, captura e exibe
            print(f"[Vehicle {self.vehicle_id}] Error executing function '{function_name}': {e}")
            return {
                "task_id": task["task_id"],
                "vehicle_id": self.vehicle_id,
                "error": f"Function execution failed: {str(e)}"
            }

if __name__ == "__main__":
    # Exemplo de como instanciar múltiplos veículos
    vehicle = Vehicle(vehicle_id="veh123", model="ModelX", make="MakeY", year=2020)
    
    # Inicializa o cliente Midd4VC para o veículo
    vc = Midd4VCClient(role="vehicle", client_id="veh123")
    vc.set_task_handler(vehicle.task_handler)
    
    # Inicia o cliente e começa a ouvir tarefas
    vc.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping vehicle...")
        vc.stop()
