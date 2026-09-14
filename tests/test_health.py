"""
Health endpoint tests for the GitHub Issues Service.

Purpose:
    Verify that the service health endpoint is available and operating
    correctly.

Expected behavior:
    A request to /healthz should return HTTP 200 and a JSON response
    containing {"status": "ok"}.

Testing approach:
    The shared TestClient fixture from conftest.py is used to call the
    application without starting an external server.

Author: Juilee Giramkar
"""
def test_healthz_returns_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
