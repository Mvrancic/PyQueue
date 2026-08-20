from fastapi.testclient import TestClient
from src.pyqueue.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# More complex integration tests would require DB mocking or a test DB container.
# For MVP, we rely on functional verification and simple health check here.
