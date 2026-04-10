import sys
import time
from fastapi.testclient import TestClient
sys.path.append('D:\\gocharaUPDATED\\Backend')
from main import app

client = TestClient(app)

print("Starting benchmark of FastAPI Endpoint...")
start = time.time()
response = client.post(
    "/api/gochara/south-indian",
    json={
        "date": "2026-03-21",
        "time": "11:21:10",
        "place": "Bhongir, India",
        "latitude": 17.51083,
        "longitude": 78.88889,
        "timezone": ""
    }
)
dur = time.time() - start
print(f"Status: {response.status_code}")
print(f"Response Time: {dur:.4f}s")
