from multiprocessing import Process
import uuid
import time
import random
from Midd4VCClient import Midd4VCClient

class ApplicationClient:
    def __init__(self, client_id, role="client"):
        self.client = Midd4VCClient(role=role, client_id=client_id)
        self.client.set_result_handler(self.on_job_result)

    def on_job_result(self, data):
        print(f"[{self.client.client_id}] Results: {data}")

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()

    def send_job_periodically(self, min_time=2, max_time=5):
        try:
            while True:

                job = {
                    "job_id": str(uuid.uuid4()),
                    "function": "math.factorial",
                    "args": [random.randint(1, 10)]
                }

                print(f"[{self.client.client_id}] Submitting job: {job['job_id']} with args: {job['args'][0]}")
                self.client.submit_job(job)

                wait_time = random.uniform(min_time, max_time)
                time.sleep(wait_time)

        except KeyboardInterrupt:
            print(f"[{self.client.client_id}] stopping...")

def run_app(client_id):
    app_client = ApplicationClient(client_id=client_id)
    app_client.start()
    app_client.send_job_periodically(min_time=5, max_time=10)
    app_client.stop()

if __name__ == "__main__":
    client_ids = [f"Application_{i}" for i in range(1, 11)]  
    processes = []

    for cid in client_ids:
        p = Process(target=run_app, args=(cid,))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Stopping all applications...")
        for p in processes:
            p.terminate()
