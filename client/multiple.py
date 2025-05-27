import sys
import os
import time
import threading
from midd4vc_client import Midd4VCClient
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tasks')))

# Classe que representa o Veículo
class Vehicle:
    def __init__(self, vehicle_id, model, make, year):
        self.vehicle_id = vehicle_id
        self.model = model
        self.make = make
        self.year = year
    
    def task_handler(self, task):
        """
        Processa a tarefa recebida e retorna o resultado.
        """
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

# Função para iniciar múltiplos veículos
def start_multiple_vehicles(num_vehicles):
    vehicle_clients = []
    
    # Cria e inicia os veículos
    for i in range(num_vehicles):
        vehicle_id = f"veh{str(i+1)}"
        vehicle = Vehicle(vehicle_id=vehicle_id, model="ModelX", make="MakeY", year=2020)
        vc = Midd4VCClient(role="vehicle", client_id=vehicle_id)
        vc.set_task_handler(vehicle.task_handler)
        vehicle_clients.append(vc)
        vc.start()

    return vehicle_clients

# Função para parar todos os veículos
def stop_all_vehicles(vehicle_clients):
    for vc in vehicle_clients:
        vc.stop()

# Função principal para iniciar veículos e aguardar tarefas
def main():
    num_vehicles = 3  # Quantidade de veículos que você quer simular
    print(f"Starting {num_vehicles} vehicles...")

    # Inicia os veículos
    vehicle_clients = start_multiple_vehicles(num_vehicles)

    try:
        # Fica aguardando tarefas indefinidamente
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping all vehicles...")
        # Para todos os veículos
        stop_all_vehicles(vehicle_clients)

if __name__ == "__main__":
    main()
