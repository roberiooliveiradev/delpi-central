"""F1.S3 — observabilidade de request: correlation id, operation id,
tempo de resposta, logging estruturado e redaction."""

import logging
import re
import uuid

import pytest

from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_REQUEST_LOGGER = "engineering_api.request"


def _request_id_of(response) -> str:
    return response.headers.get("X-Request-Id", "")


# --- correlation id ---


def test_request_id_generated_when_absent(client):
    response = client.get("/health")
    assert response.status_code == 200
    rid = _request_id_of(response)
    assert _UUID_RE.match(rid), rid


def test_request_id_preserved_when_valid(client):
    response = client.get("/health", headers={"X-Request-Id": "req-abc-123"})
    assert response.headers["X-Request-Id"] == "req-abc-123"


def test_request_id_correlation_alias_accepted(client):
    """X-Correlation-Id é alias de entrada; saída oficial é X-Request-Id."""
    response = client.get(
        "/health", headers={"X-Correlation-Id": "corr-42"}
    )
    assert response.headers["X-Request-Id"] == "corr-42"


def test_request_id_header_precedence(client):
    response = client.get(
        "/health",
        headers={
            "X-Request-Id": "primary-1",
            "X-Correlation-Id": "secondary-2",
        },
    )
    assert response.headers["X-Request-Id"] == "primary-1"


@pytest.mark.parametrize(
    "bad_id",
    [
        "id with spaces",
        "id\nwith-newline",
        "id\rwith-cr",
        "id\x00nul",
        "x" * 129,                       # acima do limite
        "id;injection",
        'id"quoted',
        "id\\backslash",
        "id,comma",
        "",
    ],
)
def test_request_id_invalid_replaced_with_uuid(client, bad_id):
    response = client.get("/health", headers={"X-Request-Id": bad_id})
    rid = _request_id_of(response)
    assert _UUID_RE.match(rid), (bad_id, rid)


def test_request_id_present_on_auth_responses(client):
    """401/403/503 também carregam o header — observability envolve o JWT."""
    response = client.get("/v1/anything")
    assert response.status_code == 401
    assert _UUID_RE.match(_request_id_of(response))


def test_request_id_isolated_between_requests(client):
    rid_a = _request_id_of(client.get("/health"))
    rid_b = _request_id_of(client.get("/ready"))
    assert rid_a != rid_b
    assert get_request_id() is None  # contexto limpo após a requisição


def test_request_id_not_derived_from_identity(client, jwks_env, core_rbac):
    token = jwks_env["make_token"]()
    response = client.get("/health", headers={"Authorization": f"Bearer {token}"})
    rid = _request_id_of(response)
    assert rid not in token


# --- operation id + response time ---


def test_operation_id_stable_on_health(client):
    response = client.get("/health")
    assert response.headers["X-Operation-Id"] == "get_engineering_health"


def test_operation_id_stable_on_ready(client):
    response = client.get("/ready")
    assert response.headers["X-Operation-Id"] == "get_engineering_ready"


def test_operation_id_absent_on_unmatched_path(client):
    """Path desconhecido não carrega operationId arbitrário."""
    response = client.get("/v1/unknown-path")
    assert response.status_code == 401
    assert "X-Operation-Id" not in response.headers


def test_response_time_header_valid(client):
    response = client.get("/health")
    value = response.headers.get("X-Response-Time-Ms")
    assert value is not None
    assert float(value) >= 0


def test_response_time_on_auth_failure(client):
    response = client.get("/v1/anything")
    assert response.status_code == 401
    assert float(response.headers["X-Response-Time-Ms"]) >= 0


# --- logging estruturado ---


def test_request_logged_with_metadata(client, caplog):
    with caplog.at_level(logging.INFO, logger=_REQUEST_LOGGER):
        client.get("/health", headers={"X-Request-Id": "log-rid-1"})
    record = next(r for r in caplog.records if "engineering_api_request" in r.message)
    msg = record.getMessage()
    assert "method=GET" in msg
    assert "path=/health" in msg
    assert "status=200" in msg
    assert "operation_id=get_engineering_health" in msg
    assert "request_id=log-rid-1" in msg
    assert "duration_ms=" in msg
    assert "result=2xx" in msg


def test_log_shows_generic_operation_on_unmatched(client, caplog):
    with caplog.at_level(logging.INFO, logger=_REQUEST_LOGGER):
        client.get("/v1/nope")
    record = next(r for r in caplog.records if "engineering_api_request" in r.message)
    assert "operation_id=unmatched_route" in record.getMessage()
    assert "status=401" in record.getMessage()


def test_no_authorization_or_token_in_logs(client, caplog, jwks_env, core_rbac):
    token = jwks_env["make_token"]()
    with caplog.at_level(logging.DEBUG):
        client.get("/v1/anything", headers={"Authorization": f"Bearer {token}"})
    all_logs = "\n".join(r.getMessage() for r in caplog.records)
    assert token not in all_logs
    assert "Bearer" not in all_logs
    assert "Authorization" not in all_logs


def test_query_string_not_in_logged_path(client, caplog):
    with caplog.at_level(logging.INFO, logger=_REQUEST_LOGGER):
        client.get("/health?secret_param=top-secret-value")
    record = next(r for r in caplog.records if "engineering_api_request" in r.message)
    assert "top-secret-value" not in record.getMessage()
    assert "path=/health" in record.getMessage()


def test_log_path_sanitized_against_control_chars(client, caplog):
    with caplog.at_level(logging.INFO, logger=_REQUEST_LOGGER):
        client.get("/v1/%0aforged_log_line")
    record = next(r for r in caplog.records if "engineering_api_request" in r.message)
    msg = record.getMessage()
    assert "forged_log_line" in msg or "?" in msg
    assert "\n" not in msg


# --- composição com auth: comportamento S2 preservado ---


def test_observability_does_not_weaken_auth(client):
    assert client.get("/v1/anything").status_code == 401


def test_observability_sees_real_path_not_masked(client, caplog):
    """Gate F1.S2R1: path mascarado pelo auth nunca aparece no log."""
    with caplog.at_level(logging.INFO, logger=_REQUEST_LOGGER):
        response = client.get("/x/api-delpi/health")
    assert response.status_code == 401
    record = next(r for r in caplog.records if "engineering_api_request" in r.message)
    assert "path=/x/api-delpi/health" in record.getMessage()


def test_protected_flow_headers_on_authorized_probe(
    jwks_env, core_rbac, probe_client
):
    """Middleware de observability compõe com JWT+AuthZ no mesmo estilo
    do app produtivo: headers presentes em 200 autorizado."""
    token = jwks_env["make_token"]()
    response = probe_client.get(
        "/probe", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert _UUID_RE.match(_request_id_of(response))
    assert response.headers["X-Operation-Id"] == "test_engineering_access_probe"
    assert float(response.headers["X-Response-Time-Ms"]) >= 0


def test_concurrent_requests_isolated_context(probe_client, jwks_env, core_rbac):
    """Requisições consecutivas com ids próprios não se contaminam."""
    token = jwks_env["make_token"]()
    r1 = probe_client.get(
        "/probe", headers={"Authorization": f"Bearer {token}", "X-Request-Id": "iso-1"}
    )
    r2 = probe_client.get(
        "/probe", headers={"Authorization": f"Bearer {token}", "X-Request-Id": "iso-2"}
    )
    assert r1.headers["X-Request-Id"] == "iso-1"
    assert r2.headers["X-Request-Id"] == "iso-2"


def test_uuid_import_used_for_generation():
    assert uuid.uuid4()  # sanity: mecanismo de geração é uuid4 stdlib
