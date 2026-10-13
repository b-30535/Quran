from fastapi.testclient import TestClient

from app.main import app


def test_prayer_logs_require_authentication():
    with TestClient(app) as client:
        response = client.put(
            "/api/v1/prayers/logs",
            json={
                "prayer_date": "2026-10-13",
                "prayer": "fajr",
                "status": "on_time",
                "note": None,
            },
        )
    assert response.status_code == 401


def test_prayer_log_rejects_unknown_prayer():
    with TestClient(app) as client:
        response = client.put(
            "/api/v1/prayers/logs",
            json={
                "prayer_date": "2026-10-13",
                "prayer": "midnight",
                "status": "on_time",
            },
        )
    assert response.status_code == 422


def test_prayer_log_rejects_unknown_status():
    with TestClient(app) as client:
        response = client.put(
            "/api/v1/prayers/logs",
            json={
                "prayer_date": "2026-10-13",
                "prayer": "fajr",
                "status": "perfect",
            },
        )
    assert response.status_code == 422


def test_prayer_history_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/prayers/logs",
            params={"start_date": "2026-10-01", "end_date": "2026-10-13"},
        )
    assert response.status_code == 401
