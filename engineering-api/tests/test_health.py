def test_health_returns_online(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "service": "engineering-api",
    }


def test_ready_returns_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["service"] == "engineering-api"


def test_openapi_exposes_stable_operation_ids(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    paths = spec["paths"]
    assert paths["/health"]["get"]["operationId"] == "get_engineering_health"
    assert paths["/ready"]["get"]["operationId"] == "get_engineering_ready"


def test_only_authorized_business_routes_exposed(client):
    """Superfície autorizada: health/ready + Home (F2a). Qualquer rota de
    negócio nova exige revisão deste contrato."""
    spec = client.get("/openapi.json").json()
    allowed = {"/health", "/ready", "/v1/home"}
    assert set(spec["paths"].keys()) == allowed


def test_docs_ui_disabled(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404


def test_trailing_slash_not_redirected(client):
    response = client.get("/health/", follow_redirects=False)
    assert response.status_code == 404
