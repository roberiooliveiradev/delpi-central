# app/tests/test_health_controller.py

def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "Api rodando!"}