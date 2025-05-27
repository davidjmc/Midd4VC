from Midd4VCClient import Midd4VCClient
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
        while True:
            task = {
                "task_id": str(uuid.uuid4()),
                "function": "factorial",
                "args": [random.randint(1, 10)]  
            }

            print(f"[ApplicationClient] Enviando tarefa {task['task_id']} com argumento {task['args'][0]}")
            self.client.submit_task(task)

            wait_time = random.uniform(min_time, max_time)  # Intervalo aleatório entre 2 e 5 segundos
            print(f"[ApplicationClient] Aguardando {wait_time:.2f} segundos antes de enviar a próxima tarefa...")
            time.sleep(wait_time)

if __name__ == "__main__":
    app_client = ApplicationClient(client_id="application123")
    app_client.start()

    try:
        app_client.send_task_periodically(min_time=3, max_time=6)  # Enviar tarefas com intervalo aleatório entre 3s e 6s
    except KeyboardInterrupt:
        print("[ApplicationClient] Parando o cliente de aplicação...")
        app_client.stop()
    