import threading
import time
import random
import uuid
from midd4vc_client import Midd4VCClient

class ApplicationClient:
    def __init__(self, client_id, role="client"):
        self.client = Midd4VCClient(role=role, client_id=client_id)
        self.client.start()
        self._running = True

    def send_task_periodically(self):
        while self._running:
            # Gera uma tarefa aleatória com argumentos aleatórios
            task = {
                "task_id": str(uuid.uuid4()),
                "function": "factorial",  # Exemplo de função
                "args": [random.randint(1, 10)]
            }

            # 10% de chance de falha ao enviar a tarefa
            failure_chance = random.random()
            if failure_chance < 0.1:  # 10% de chance de falha
                print(f"[Client {self.client.client_id}] Simulating task failure!")
                continue  # Ignora esta tarefa e tenta a próxima

            print(f"[Client {self.client.client_id}] Sending task {task['task_id']} with arguments {task['args']}")
            self.client.submit_task(task)

            # Espera aleatória entre 1 e 3 segundos antes de enviar a próxima tarefa
            time.sleep(random.randint(1, 3))  # Pode ajustar os limites para simular diferentes cargas

    def stop(self):
        self._running = False
        self.client.stop()

def start_multiple_clients(num_clients):
    clients = []
    threads = []
    
    # Criar e iniciar os clientes em threads separadas
    for i in range(num_clients):
        client_id = f"client_{i+1}"
        app_client = ApplicationClient(client_id=client_id)
        clients.append(app_client)

        # Inicia a thread para enviar as tarefas
        thread = threading.Thread(target=app_client.send_task_periodically)
        thread.start()
        threads.append(thread)

    # Simulação contínua até o comando de parada
    try:
        input("Press Enter to stop the load simulation...\n")  # Aguarda o usuário pressionar Enter para parar

    except KeyboardInterrupt:
        print("Simulation interrupted")

    # Para todos os clientes após o comando de parada
    for client in clients:
        client.stop()

    # Espera todos os threads terminarem antes de sair
    for thread in threads:
        thread.join()

# Simula 50 clientes (ajuste o número conforme necessário)
start_multiple_clients(2)  # Aumente para 100 ou mais dependendo da sua necessidade de carga
