from midd4vc_client import Midd4VCClient
import uuid
import time
import random
import threading

class ApplicationClient:
    def __init__(self, client_id, role="client"):
        self.client = Midd4VCClient(role=role, client_id=client_id)

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()

    def send_task_periodically(self, min_time=2, max_time=5):
        """Envia tarefas periodicamente com intervalo aleatório entre 2 a 5 segundos."""
        while True:
            task = {
                "task_id": str(uuid.uuid4()),
                "function": "factorial",
                "args": [random.randint(1, 10)]  # Argumento aleatório
            }

            print(f"[ApplicationClient] Enviando tarefa {task['task_id']} com argumento {task['args'][0]}")
            self.client.submit_task(task)

            wait_time = random.uniform(min_time, max_time)  # Intervalo aleatório entre 2 e 5 segundos
            print(f"[ApplicationClient] Aguardando {wait_time:.2f} segundos antes de enviar a próxima tarefa...")
            time.sleep(wait_time)

def random_task():
    """Função para criar uma tarefa com ID único e parâmetros aleatórios."""
    return {
        "task_id": str(uuid.uuid4()),  # Gera um ID único para cada tarefa
        "function": "factorial",       # Função de exemplo (pode ser qualquer uma)
        "args": [random.randint(1, 10)]  # Argumentos aleatórios (número entre 1 e 10)
    }

def random_interval(min=2, max=5):
    return random.uniform(min, max)

def application(client_id):
    client = Midd4VCClient(role="client", client_id="client123")
    client.start()

    while True:
        task = random_task()
        print(f"[Client {client_id}] Sending task {task['task_id']} with argument {task['args']}")

        client.submit_task(task)

        while client.running:
            client.client.loop()

if __name__ == "__main__":
    app_client = ApplicationClient(client_id="application123")
    app_client.start()

    try:
        app_client.send_task_periodically(min_time=3, max_time=6)  # Enviar tarefas com intervalo aleatório entre 3s e 6s
    except KeyboardInterrupt:
        print("[ApplicationClient] Parando o cliente de aplicação...")
        app_client.stop()
    