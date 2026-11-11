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


# Superfície autorizada de rotas de negócio — fonte única compartilhada
# com test_auth_middleware (probe ausente ⇒ mesmo conjunto). Qualquer
# rota nova exige revisão explícita deste contrato.
ALLOWED_BUSINESS_PATHS = {
        "/health",
        "/ready",
        "/v1/home",
        "/v1/overview",
        "/v1/lmps",
        "/v1/lmps/summary",
        "/v1/lmps/goal-context",
        "/v1/lmps/department-idd",
        "/v1/lmps/nonconformities/streak",
        "/v1/lmps/{sale_number}",
        "/v1/lmps/{sale_number}/history/events",
        "/v1/lmps/{sale_number}/history/flow",
        "/v1/products",
        "/v1/products/filter-options",
        "/v1/products/{product_code}",
        "/v1/products/{product_code}/structure",
        "/v1/products/{product_code}/parents",
        "/v1/products/{product_code}/suppliers",
        "/v1/products/{product_code}/drawing",
        "/v1/products/{product_code}/drawing/pdf",
        "/v1/products/{product_code}/purchase-price-history",
        "/public/characters/{character_id}/avatar/{filename}",
        "/v1/nonconformities",
        "/v1/nonconformities/{record_id}",
        "/v1/nonconformities/{record_id}/history",
        "/v1/nonconformities/{record_id}/context",
        "/v1/nonconformities/indicators",
        "/v1/nonconformities/problem-tags",
        "/v1/nonconformities/export",
        "/v1/nonconformities/import",
        "/v1/nonconformities/prepare",
        # PRC-C2/C3 — Product Registration (18 operações do contrato §4).
        "/v1/product-registration/intake/requests",
        "/v1/product-registration/requests",
        "/v1/product-registration/requests/{request_id}",
        "/v1/product-registration/requests/{request_id}/timeline",
        "/v1/product-registration/requests/{request_id}/draft",
        "/v1/product-registration/requests/{request_id}/actions/start",
        "/v1/product-registration/requests/{request_id}/actions/resume",
        "/v1/product-registration/requests/{request_id}/actions/submit-review",
        "/v1/product-registration/requests/{request_id}/actions/return-to-attendance",
        "/v1/product-registration/requests/{request_id}/actions/request-information",
        # D16 / D16-REF-01 — bandeiras de acompanhamento.
        "/v1/product-registration/flags",
        "/v1/product-registration/flags/summary",
        "/v1/product-registration/requests/{request_id}/flags",
        "/v1/product-registration/requests/{request_id}/flags/{flag_id}",
        "/v1/product-registration/requests/{request_id}/flags/{flag_id}/actions/resolve",
        "/v1/product-registration/requests/{request_id}/flags/{flag_id}/actions/reopen",
        # PRC-REF-019 — rodadas de esclarecimento.
        "/v1/product-registration/requests/{request_id}/information-rounds",
        "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}",
        "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/answers",
        "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/actions/submit-answers",
        "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/actions/request-follow-up",
        "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/questions/{question_id}/actions/accept",
        "/v1/product-registration/requests/{request_id}/actions/reject",
        "/v1/product-registration/requests/{request_id}/actions/complete",
        # PRC-REF-022/REF-023 — devolução para correção, anexos e
        # divergência de rota (inclui FIX-08 draft/returned-fields).
        "/v1/product-registration/requests/{request_id}/actions/return-for-correction",
        "/v1/product-registration/requests/{request_id}/actions/resubmit-correction",
        "/v1/product-registration/requests/{request_id}/actions/route-divergence",
        "/v1/product-registration/requests/{request_id}/returned-fields",
        "/v1/product-registration/requests/{request_id}/correction-returns",
        "/v1/product-registration/requests/{request_id}/correction-returns/{return_id}",
        "/v1/product-registration/requests/{request_id}/attachments",
        "/v1/product-registration/requests/{request_id}/attachments/{attachment_id}/download",
        "/v1/product-registration/requests/{request_id}/actions/verify-and-complete",
        "/v1/product-registration/requests/{request_id}/verifications",
        "/v1/product-registration/technical-records/{record_id}",
        "/v1/product-registration/technical-records/{record_id}/revisions",
        "/v1/product-registration/technical-records/{record_id}/revisions/{revision_number}",
        "/v1/product-registration/reference-data",
        "/v1/product-registration/reference-data/products/{official_code}/edit-context",
        "/v1/product-registration/reference-data/catalogs/{catalog}",
        "/v1/product-registration/reference-data/suppliers/search",
        "/v1/product-registration/outbound/requests",
        "/v1/product-registration/outbound/requests/{request_id}",
}


def test_only_authorized_business_routes_exposed(client):
    """Superfície autorizada: health/ready + Home (F2a) + Overview
    (F3.OVERVIEW) + LMP funcional (G3: E-LMP-01/03). Qualquer rota de
    negócio nova exige revisão deste contrato."""
    spec = client.get("/openapi.json").json()
    assert set(spec["paths"].keys()) == ALLOWED_BUSINESS_PATHS


def test_docs_ui_disabled(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404


def test_trailing_slash_not_redirected(client):
    response = client.get("/health/", follow_redirects=False)
    assert response.status_code == 404
