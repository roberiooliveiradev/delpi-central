# app/tests/http/test_health_http.py

def test_health_endpoint(client):
    response = client.get("/core-api/health")
    assert response.status_code == 200
    assert response.json["status"] == "Api rodando!"