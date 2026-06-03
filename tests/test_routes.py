def test_dashboard_returns_200(flask_client):
    response = flask_client.get("/")
    assert response.status_code == 200


def test_dashboard_contains_signal_names(flask_client):
    response = flask_client.get("/")
    html = response.data.decode()
    assert "Test PASS" in html
    assert "Test FAIL" in html


def test_history_returns_200(flask_client):
    response = flask_client.get("/history")
    assert response.status_code == 200


def test_fix_unknown_signal_returns_404(flask_client):
    response = flask_client.post("/fix/Nonexistent%20Signal")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_fix_wrong_origin_returns_403(flask_client):
    response = flask_client.post(
        "/fix/Application%20Firewall",
        headers={"Origin": "http://evil.example.com"},
    )
    assert response.status_code == 403


def test_security_headers_present(flask_client):
    response = flask_client.get("/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "script-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("Referrer-Policy") == "no-referrer"
