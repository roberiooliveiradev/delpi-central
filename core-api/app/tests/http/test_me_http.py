# app/tests/http/test_me_http.py

def test_me_requires_auth(client):
    # Não criamos usuário aqui
    response = client.get("/core-api/me")
    assert response.status_code == 401


def test_me_returns_user(client, superadmin_user):
    response = client.get("/core-api/me")
    assert response.status_code == 200
    assert response.json["email"] == "admin@test.com"