from Midd4VCClient import Midd4VCClient
import uuid
import time
import random
import threading

class ApplicationClient:
    def __init__(self, client_id, role="client"):
        self.client = Midd4VCClient(role=role, client_id=client_id)
        self.client.set_result_handler(self.on_job_result)  # Define o handler de resultado
        self.client_id = client_id

    def on_job_result(self, data):
        print(f"[{self.client_id}] Results: {data}")

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()

    def send_job_periodically(self, min_time=2, max_time=5):
        while True:
            job = {
                "job_id": str(uuid.uuid4()),
                "function": "math.factorial",
                "args": [random.randint(1, 10)]
            }

            print(f"[{self.client_id}] Submitting job: {job['job_id']} with args: {job['args'][0]}")
            self.client.submit_job(job)

            wait_time = random.uniform(min_time, max_time)
            #print(f"[ApplicationClient] Aguardando {wait_time:.2f} segundos antes de enviar a próxima tarefa...")
            time.sleep(wait_time)

if __name__ == "__main__":
    app_client = ApplicationClient(client_id="Application123")
    app_client.start()

    try:
        app_client.send_job_periodically(min_time=3, max_time=6)
    except KeyboardInterrupt:
        #print("[ApplicationClient] Parando o cliente de aplicação...")
        app_client.stop()
