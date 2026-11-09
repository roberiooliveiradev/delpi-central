"""PRC-REF-021 — encaminhamento governado de divergências.

Registra decisão por item sem alterar field_results/MATCH; REQUESTER_CORRECTION
permanece PENDING_OWNER (sem escrita estruturada do solicitante).
"""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    _get,
    _post,
    _submit_create,
    _token,
    prc_service_repo,
)

ANALYST_SUB = "analyst-1"
REQUESTER_SUB = "user-1"


def _base(rid: str) -> str:
    return f"/v1/product-registration/requests/{rid}"


def _open_in_progress(client, jwks_env, core_rbac, prc_service_repo):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=REQUESTER_SUB))
    rid = _submit_create(
        client, jwks_env, core_rbac, sub=REQUESTER_SUB
    ).json()["data"]["requestId"]
    tok = _token(jwks_env, ANALYST_SUB)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=ANALYST_SUB))
    resp = _post(
        client,
        f"{_base(rid)}/actions/start",
        tok,
        json={"expectedVersion": 1},
    )
    assert resp.status_code == 200, resp.text
    ver = prc_service_repo["repo"].insert_verification(
        request_id=rid,
        verification={
            "id": "11111111-1111-1111-1111-111111111111",
            "official_product_code": "10080022",
            "requested_by_subject": ANALYST_SUB,
            "checked_at": "2026-11-09T18:00:00+00:00",
            "official_source": "api-delpi",
            "result": "mismatched",
            "expected_fields": ["description", "unit"],
            "field_results": {
                "description": {
                    "result": "mismatched",
                    "expected": "A",
                    "observed": "B",
                },
                "unit": {
                    "result": "mismatched",
                    "expected": "UN",
                    "observed": "PC",
                },
            },
            "evidence_fingerprint": "fp-ref021",
            "correlation_id": "corr-ref021",
            "error_code": None,
        },
    )
    detail = _get(
        client, f"{_base(rid)}", tok
    ).json()["data"]
    return rid, tok, ver["id"], int(detail["caseVersion"])


@pytest.mark.usefixtures("prc_service_repo")
def test_route_divergence_records_without_match_change(
    client, jwks_env, core_rbac, prc_service_repo,
):
    rid, tok, vid, version = _open_in_progress(
        client, jwks_env, core_rbac, prc_service_repo
    )
    resp = _post(
        client,
        f"{_base(rid)}/actions/route-divergence",
        tok,
        json={
            "expectedVersion": version,
            "verificationId": vid,
            "targetType": "FIELD",
            "targetPath": "unit",
            "decision": "ERP_MANUAL_CORRECTION",
            "reason": "Operador TOTVS ajustará a unidade.",
        },
        headers={"Idempotency-Key": "ref021-erp-1"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["routing"]["decision"] == "ERP_MANUAL_CORRECTION"
    assert body["routing"]["targetKey"] == "FIELD:unit"
    assert body["routing"]["routingStatus"] == "recorded_external"
    assert body["requesterWrite"] is None
    assert body["caseVersion"] == version + 1

    listed = _get(
        client, f"{_base(rid)}/verifications", tok
    ).json()["data"]
    assert listed["items"][0]["field_results"]["unit"]["result"] == "mismatched"
    assert any(
        r["decision"] == "ERP_MANUAL_CORRECTION" and r["targetKey"] == "FIELD:unit"
        for r in listed["routings"]
    )


@pytest.mark.usefixtures("prc_service_repo")
def test_requester_correction_is_pending_owner(
    client, jwks_env, core_rbac, prc_service_repo,
):
    rid, tok, vid, version = _open_in_progress(
        client, jwks_env, core_rbac, prc_service_repo
    )
    resp = _post(
        client,
        f"{_base(rid)}/actions/route-divergence",
        tok,
        json={
            "expectedVersion": version,
            "verificationId": vid,
            "targetType": "FIELD",
            "targetPath": "description",
            "decision": "REQUESTER_CORRECTION",
            "reason": "Solicitante deve confirmar a descrição.",
        },
        headers={"Idempotency-Key": "ref021-req-1"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["requesterWrite"]["status"] == "PENDING_OWNER"
    assert body["requesterWrite"]["code"] == "ARCHITECTURE_DECISION_REQUIRED"
    assert body["routing"]["routingStatus"] == "pending_owner"


@pytest.mark.usefixtures("prc_service_repo")
def test_multiple_routings_same_case(
    client, jwks_env, core_rbac, prc_service_repo,
):
    rid, tok, vid, version = _open_in_progress(
        client, jwks_env, core_rbac, prc_service_repo
    )
    first = _post(
        client,
        f"{_base(rid)}/actions/route-divergence",
        tok,
        json={
            "expectedVersion": version,
            "verificationId": vid,
            "targetType": "FIELD",
            "targetPath": "unit",
            "decision": "ERP_MANUAL_CORRECTION",
            "reason": "Ajuste TOTVS da unidade.",
        },
        headers={"Idempotency-Key": "ref021-m1"},
    )
    assert first.status_code == 200, first.text
    v2 = first.json()["data"]["caseVersion"]
    second = _post(
        client,
        f"{_base(rid)}/actions/route-divergence",
        tok,
        json={
            "expectedVersion": v2,
            "verificationId": vid,
            "targetType": "SUPPLIER_LINK",
            "targetPath": "suppliers",
            "supplierKey": {"supplierCode": "000123", "store": "01"},
            "targetAttribute": "partNumber",
            "decision": "NEEDS_CLARIFICATION",
            "reason": "Confirmar PN antes de decidir.",
        },
        headers={"Idempotency-Key": "ref021-m2"},
    )
    assert second.status_code == 200, second.text
    listed = _get(
        client, f"{_base(rid)}/verifications", tok
    ).json()["data"]
    keys = {r["targetKey"] for r in listed["routings"]}
    assert "FIELD:unit" in keys
    assert "SUPPLIER_LINK:000123/01:partNumber" in keys


@pytest.mark.usefixtures("prc_service_repo")
def test_route_divergence_forbidden_without_access(
    client, jwks_env, core_rbac, prc_service_repo,
):
    rid, _tok, vid, version = _open_in_progress(
        client, jwks_env, core_rbac, prc_service_repo
    )
    core_rbac["behavior"] = ("data", rbac_payload([], id="outsider"))
    resp = _post(
        client,
        f"{_base(rid)}/actions/route-divergence",
        _token(jwks_env, "outsider"),
        json={
            "expectedVersion": version,
            "verificationId": vid,
            "targetType": "FIELD",
            "targetPath": "unit",
            "decision": "ERP_MANUAL_CORRECTION",
            "reason": "Sem permissão.",
        },
    )
    assert resp.status_code in (403, 401)


@pytest.mark.usefixtures("prc_service_repo")
def test_allowed_actions_include_route_divergence(
    client, jwks_env, core_rbac, prc_service_repo,
):
    rid, tok, _vid, _version = _open_in_progress(
        client, jwks_env, core_rbac, prc_service_repo
    )
    detail = _get(client, f"{_base(rid)}", tok).json()["data"]
    assert "route_divergence" in detail["allowedActions"]
    assert detail["status"] == "in_progress"
