# app/tests/http/test_dashboard_http.py

def test_dashboard_authenticated(client, superadmin_user):
    response = client.get("/core-api/dashboard")
    assert response.status_code == 200
    assert "appsCount" in response.json