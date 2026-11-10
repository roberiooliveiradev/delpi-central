"""PRC-REF-022 — devolução / correção / reenvio da ficha técnica."""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    _post,
    _submit_create,
    _token,
    prc_service_repo,
)
from tests.test_d16_attendance_flags import _patch

from engineering_app.domain.product_registration import correction_returns
from engineering_app.domain.product_registration.errors import PrcValidationError
from engineering_app.interface.mcp import prc_semantic
from engineering_app.interface.mcp.semantic_bridge import _EXECUTE_DISPATCH
from tests.test_prc_eva_parity import _ctx, _entry

REQUESTER_SUB = "user-1"
ANALYST_SUB = "analyst-1"
OTHER_SUB = "other-user"


def _base(rid: str) -> str:
    return f"/v1/product-registration/requests/{rid}"


def _as(jwks_env, core_rbac, sub: str) -> str:
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    return _token(jwks_env, sub)


def _open_case(client, jwks_env, core_rbac) -> str:
    _as(jwks_env, core_rbac, REQUESTER_SUB)
    rid = _submit_create(
        client, jwks_env, core_rbac, sub=REQUESTER_SUB
    ).json()["data"]["requestId"]
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client,
        f"{_base(rid)}/actions/start",
        tok,
        json={"expectedVersion": 1},
    )
    assert resp.status_code == 200, resp.text
    return rid


def _case_version(client, jwks_env, core_rbac, rid, sub=ANALYST_SUB) -> int:
    tok = _as(jwks_env, core_rbac, sub)
    resp = client.get(
        _base(rid), headers={"Authorization": f"Bearer {tok}"}
    )
    assert resp.status_code == 200, resp.text
    return int(resp.json()["data"]["caseVersion"])


def _return_targets(*paths: str):
    return [
        {
            "targetType": "FIELD",
            "targetPath": path,
            "reason": f"Corrigir {path} por favor.",
        }
        for path in paths
    ]


def test_domain_validate_targets_reject_arbitrary_path():
    with pytest.raises(PrcValidationError):
        correction_returns.validate_return_targets(
            [
                {
                    "targetType": "FIELD",
                    "targetPath": "notARealPath",
                    "reason": "motivo longo",
                }
            ]
        )


def test_return_correct_resubmit_happy_path(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case(client, jwks_env, core_rbac)
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok_a = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok_a,
        json={
            "expectedVersion": version,
            "targets": _return_targets("unit", "description"),
        },
        headers={"Idempotency-Key": f"ret-{rid}-1"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["status"] == "needs_correction"
    assert "return_for_correction" not in body["allowedActions"]
    assert body["correctionExchange"]["hasOpenReturn"] is True
    assert len(body["correctionReturn"]["targets"]) == 2

    # Analista não recebe save/resubmit (não é o solicitante).
    assert "save_returned_fields" not in body["allowedActions"]
    assert "resubmit_correction" not in body["allowedActions"]

    version = int(body["caseVersion"])
    tok_r = _as(jwks_env, core_rbac, REQUESTER_SUB)
    detail = client.get(
        _base(rid), headers={"Authorization": f"Bearer {tok_r}"}
    ).json()["data"]
    assert "save_returned_fields" in detail["allowedActions"]
    assert detail["correctionExchange"]["canCorrect"] is True

    resp = _patch(
        client,
        f"{_base(rid)}/returned-fields",
        tok_r,
        json={
            "expectedVersion": version,
            "changes": [
                {
                    "path": "unit",
                    "proposedValue": "KG",
                    "reason": "Unidade correta é KG.",
                    "mode": "changed",
                },
                {
                    "path": "description",
                    "proposedValue": detail["technicalDraft"]["description"],
                    "reason": "Confirmo a descrição atual.",
                    "mode": "confirmed",
                },
            ],
        },
        headers={"Idempotency-Key": f"save-{rid}-1"},
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])

    resp = _post(
        client,
        f"{_base(rid)}/actions/resubmit-correction",
        tok_r,
        json={"expectedVersion": version},
        headers={"Idempotency-Key": f"resub-{rid}-1"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["status"] == "in_progress"
    assert body["correctionExchange"]["hasOpenReturn"] is False
    assert body["correctionExchange"]["lastResubmitted"] is not None
    assert "return_for_correction" in body["allowedActions"]


def test_return_rejects_empty_targets(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case(client, jwks_env, core_rbac)
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok,
        json={"expectedVersion": version, "targets": []},
    )
    assert resp.status_code in (400, 422)


def test_requester_cannot_edit_non_returned_field(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case(client, jwks_env, core_rbac)
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok_a = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok_a,
        json={
            "expectedVersion": version,
            "targets": _return_targets("unit"),
        },
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    tok_r = _as(jwks_env, core_rbac, REQUESTER_SUB)
    resp = _patch(
        client,
        f"{_base(rid)}/returned-fields",
        tok_r,
        json={
            "expectedVersion": version,
            "changes": [
                {
                    "path": "description",
                    "proposedValue": "hack",
                    "reason": "tentativa indevida",
                }
            ],
        },
    )
    assert resp.status_code == 422, resp.text


def test_third_party_cannot_correct(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case(client, jwks_env, core_rbac)
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok_a = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok_a,
        json={
            "expectedVersion": version,
            "targets": _return_targets("unit"),
        },
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    tok_o = _as(jwks_env, core_rbac, OTHER_SUB)
    resp = _patch(
        client,
        f"{_base(rid)}/returned-fields",
        tok_o,
        json={
            "expectedVersion": version,
            "changes": [
                {
                    "path": "unit",
                    "proposedValue": "PC",
                    "reason": "não sou o dono",
                }
            ],
        },
    )
    assert resp.status_code == 403, resp.text


def test_resubmit_blocked_until_all_addressed(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case(client, jwks_env, core_rbac)
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok_a = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok_a,
        json={
            "expectedVersion": version,
            "targets": _return_targets("unit", "description"),
        },
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    tok_r = _as(jwks_env, core_rbac, REQUESTER_SUB)
    resp = _patch(
        client,
        f"{_base(rid)}/returned-fields",
        tok_r,
        json={
            "expectedVersion": version,
            "changes": [
                {
                    "path": "unit",
                    "proposedValue": "PC",
                    "reason": "só um campo",
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    resp = _post(
        client,
        f"{_base(rid)}/actions/resubmit-correction",
        tok_r,
        json={"expectedVersion": version},
    )
    assert resp.status_code == 422, resp.text


def test_idempotent_return_replay(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case(client, jwks_env, core_rbac)
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    body = {
        "expectedVersion": version,
        "targets": _return_targets("unit"),
    }
    key = f"idem-ret-{rid}"
    r1 = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok,
        json=body,
        headers={"Idempotency-Key": key},
    )
    r2 = _post(
        client,
        f"{_base(rid)}/actions/return-for-correction",
        tok,
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    assert r1.json()["data"]["caseVersion"] == r2.json()["data"]["caseVersion"]


def test_multiple_cycles(client, jwks_env, core_rbac, prc_service_repo):
    rid = _open_case(client, jwks_env, core_rbac)

    def cycle(path: str):
        version = _case_version(client, jwks_env, core_rbac, rid)
        tok_a = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _post(
            client,
            f"{_base(rid)}/actions/return-for-correction",
            tok_a,
            json={
                "expectedVersion": version,
                "targets": _return_targets(path),
            },
        )
        assert resp.status_code == 200, resp.text
        version = int(resp.json()["data"]["caseVersion"])
        tok_r = _as(jwks_env, core_rbac, REQUESTER_SUB)
        resp = _patch(
            client,
            f"{_base(rid)}/returned-fields",
            tok_r,
            json={
                "expectedVersion": version,
                "changes": [
                    {
                        "path": path,
                        "proposedValue": "PC",
                        "reason": f"ajuste {path}",
                    }
                ],
            },
        )
        assert resp.status_code == 200, resp.text
        version = int(resp.json()["data"]["caseVersion"])
        resp = _post(
            client,
            f"{_base(rid)}/actions/resubmit-correction",
            tok_r,
            json={"expectedVersion": version},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "in_progress"

    cycle("unit")
    cycle("description")
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    listed = client.get(
        f"{_base(rid)}/correction-returns",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["data"]["total"] == 2


@pytest.mark.asyncio
async def test_eva_return_for_correction_dispatch(prc_service_repo):
    assert (
        "product_registration",
        "return_for_correction",
    ) in _EXECUTE_DISPATCH
    assert (
        "product_registration",
        "save_returned_fields",
    ) in _EXECUTE_DISPATCH
    assert (
        "product_registration",
        "resubmit_correction",
    ) in _EXECUTE_DISPATCH
    entry = _entry("return_for_correction")
    out = await prc_semantic.execute_action(
        _ctx(ANALYST_SUB),
        entry,
        "prepare",
        target_ref="00000000-0000-0000-0000-000000000001",
        expected_version=1,
        payload={"targets": _return_targets("unit")},
    )
    # prepare devolve CallToolResult / envelope — sem 501.
    payload = getattr(out, "structuredContent", None) or getattr(
        out, "data", None
    ) or out
    text = str(payload)
    assert "501" not in text
    assert "not_implemented" not in text
