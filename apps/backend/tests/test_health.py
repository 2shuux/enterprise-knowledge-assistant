from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok():
    client = TestClient(create_app())
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "X-Request-ID" in resp.headers  # middleware is wired


def test_unknown_route_is_json_404():
    client = TestClient(create_app())
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
