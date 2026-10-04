from fastapi.testclient import TestClient
from rbac.main import app

client = TestClient(app)


def test_pass_and_fail():
    good = client.post("/check", json={'role': 'member', 'action': 'create'}).json()
    assert good["passed"] is True
    assert good["applied"] is False
    bad = client.post("/check", json={'role': 'viewer', 'action': 'delete'}).json()
    assert bad["passed"] is False
    assert "forbidden" in bad["failed"]
