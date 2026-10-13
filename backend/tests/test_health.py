from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Noor Al-Quran API"


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_does_not_expose_secrets():
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] in {"ready", "degraded"}
    assert "mongodb_uri" not in response.text.lower()


def test_register_rejects_short_password():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={"display_name": "Demo User", "email": "demo@example.com", "password": "short"},
        )
    assert response.status_code == 422


def test_profile_requires_bearer_token():
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
