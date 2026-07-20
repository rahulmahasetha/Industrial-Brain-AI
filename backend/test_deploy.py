import requests
import time

url = "https://industrial-brain-ai-zad4.onrender.com/api/internal/migrate-batch"

for i in range(30):
    resp = requests.post(url)
    if resp.status_code != 404:
        print("Endpoint is live!")
        break
    print(f"Attempt {i+1}: Still deploying...")
    time.sleep(10)
