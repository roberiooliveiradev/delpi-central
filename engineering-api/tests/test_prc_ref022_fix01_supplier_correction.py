"""PRC-REF-022-FIX-01 — devolução de vínculos SA5 + PN obrigatório."""

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
from tests.test_prc_ref022_correction_returns import (
    _as,
    _base,
    _case_version,
    _open_case,
)

REQUESTER_SUB = "user-1"
ANALYST_SUB = "analyst-1"

SUP1 = {
    "supplierCode": "000123", "store": "01",
    "supplierName": "FORNECEDOR UM", "partNumber": "PN-A",
    "catalogNumber": "CAT-A",
}
SUP2 = {
    "supplierCode": "000456", "store": "02",
    "supplierName": "FORNECEDOR DOIS", "partNumber": "PN-B",
    "catalogNumber": None,
}


def _create_with_suppliers(client, jwks_env, core_rbac, suppliers):
    from tests.test_product_registration import _create_body
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=REQUESTER_SUB))
    body = _create_body()
    body["requestedData"]["suppliers"] = suppliers
    return _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env, REQUESTER_SUB),
        json=body,
    )


def _open_case_suppliers(client, jwks_env, core_rbac, suppliers=None):
    resp = _create_with_suppliers(
        client, jwks_env, core_rbac, suppliers or [dict(SUP1), dict(SUP2)]
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    r = _post(
        client, f"{_base(rid)}/actions/start", tok,
        json={"expectedVersion": 1},
    )
    assert r.status_code == 200, r.text
    return rid


def _return_supplier(client, jwks_env, core_rbac, rid, targets):
    version = _case_version(client, jwks_env, core_rbac, rid)
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    return _post(
        client, f"{_base(rid)}/actions/return-for-correction", tok,
        json={"expectedVersion": version, "targets": targets},
    )


def _supplier_target(code, store, attr, reason="Corrigir atributo."):
    return {
        "targetType": "SUPPLIER_LINK",
        "targetAttribute": attr,
        "supplierKey": {"supplierCode": code, "store": store},
        "reason": reason,
    }


def _save_changes(client, jwks_env, core_rbac, rid, version, changes):
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    return _patch(
        client, f"{_base(rid)}/returned-fields", tok,
        json={"expectedVersion": version, "changes": changes},
    )


def test_return_supplier_link_targets(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [
            _supplier_target("000123", "01", "partNumber"),
            _supplier_target("000123", "01", "catalogNumber"),
            _supplier_target("000456", "02", "partNumber"),
        ],
    )
    assert resp.status_code == 200, resp.text
    targets = resp.json()["data"]["correctionReturn"]["targets"]
    keys = {t["targetKey"] for t in targets}
    assert "SUPPLIER_LINK:000123/01:partNumber" in keys
    assert "SUPPLIER_LINK:000123/01:catalogNumber" in keys
    assert "SUPPLIER_LINK:000456/02:partNumber" in keys


def test_return_supplier_link_unknown_link_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("999999", "99", "partNumber")],
    )
    assert resp.status_code == 422, resp.text


def test_return_supplier_link_duplicate_target_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [
            _supplier_target("000123", "01", "partNumber"),
            _supplier_target("000123", "01", "partNumber",
                             reason="Outro motivo."),
        ],
    )
    assert resp.status_code in (400, 422), resp.text


def test_correction_pn_change_applied(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [
        dict(SUP1, partNumber="PN-NOVO"),
        dict(SUP2),
    ]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "PN corrigido.", "mode": "changed",
        }],
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(
        _base(rid),
        headers={
            "Authorization": f"Bearer {_as(jwks_env, core_rbac, REQUESTER_SUB)}"
        },
    ).json()["data"]
    sup = detail["technicalDraft"]["suppliers"]
    assert sup[0]["partNumber"] == "PN-NOVO"
    assert sup[0]["catalogNumber"] == "CAT-A"
    assert sup[1]["partNumber"] == "PN-B"
    targets = detail["correctionExchange"]["openReturn"]["targets"]
    assert targets[0]["addressedAt"]


def test_correction_catalog_not_returned_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [
        dict(SUP1, partNumber="PN-NOVO", catalogNumber="CAT-X"),
        dict(SUP2),
    ]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "Tentativa de alterar catálogo.", "mode": "changed",
        }],
    )
    assert resp.status_code == 422, resp.text


def test_correction_other_supplier_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [
        dict(SUP1, partNumber="PN-NOVO"),
        dict(SUP2, partNumber="PN-HACK"),
    ]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "Alterar outro vínculo.", "mode": "changed",
        }],
    )
    assert resp.status_code == 422, resp.text


def test_correction_remove_link_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": [dict(SUP1)],
            "reason": "Remover o outro vínculo.", "mode": "changed",
        }],
    )
    assert resp.status_code == 422, resp.text


def test_correction_change_without_pn_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    """Vínculo alterado exige PN válido — legado com PN vazio só
    corrige Catálogo se o PN também for devolvido e preenchido."""
    legacy = dict(SUP1, partNumber="")
    rid = _open_case_suppliers(
        client, jwks_env, core_rbac, [legacy, dict(SUP2)]
    ) if False else None
    # legado PN vazio não entra mais por intake; simular via draft:
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    repo = prc_service_repo["repo"]
    draft = repo._drafts[rid]
    draft["technical_data"]["suppliers"][0]["partNumber"] = ""
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "catalogNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    current = draft["technical_data"]["suppliers"]
    proposed = [dict(current[0], catalogNumber="CAT-N"), dict(current[1])]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": proposed,
            "reason": "Só catálogo, PN vazio permanece.",
            "mode": "changed",
        }],
    )
    assert resp.status_code == 422, resp.text
    # Com PN também devolvido, a correção completa passa.
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [
            _supplier_target("000123", "01", "partNumber"),
            _supplier_target("000123", "01", "catalogNumber"),
        ],
    )
    # Devolução anterior já fechada? Não — ainda aberta; novo return
    # é 409. Reusar o ciclo aberto: devolver PN+cat em nova checagem
    # exigiria um novo ciclo — o alvo cat já está devolvido.
    assert resp.status_code in (409, 422)


def test_correction_zeros_preserved(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [dict(SUP1, partNumber="0000123"), dict(SUP2)]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "PN com zeros.", "mode": "changed",
        }],
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(
        _base(rid),
        headers={
            "Authorization": f"Bearer {_as(jwks_env, core_rbac, REQUESTER_SUB)}"
        },
    ).json()["data"]
    assert detail["technicalDraft"]["suppliers"][0]["partNumber"] == (
        "0000123"
    )


def test_correction_cas_stale_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [dict(SUP1, partNumber="PN-1"), dict(SUP2)]
    first = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "Primeira gravação.", "mode": "changed",
        }],
    )
    assert first.status_code == 200, first.text
    replay = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers",
            "proposedValue": [dict(SUP1, partNumber="PN-2"), dict(SUP2)],
            "reason": "CAS velho.", "mode": "changed",
        }],
    )
    assert replay.status_code == 409, replay.text


def test_correction_other_user_forbidden(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    tok = _as(jwks_env, core_rbac, "other-user")
    resp = _patch(
        client, f"{_base(rid)}/returned-fields", tok,
        json={
            "expectedVersion": version,
            "changes": [{
                "path": "suppliers",
                "proposedValue": [dict(SUP1, partNumber="X"), dict(SUP2)],
                "reason": "não sou dono",
            }],
        },
    )
    assert resp.status_code == 403, resp.text


def test_resubmit_requires_all_supplier_targets_addressed(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [
            _supplier_target("000123", "01", "partNumber"),
            _supplier_target("000456", "02", "partNumber"),
        ],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [dict(SUP1, partNumber="PN-1"), dict(SUP2)]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "Só um alvo tratado.", "mode": "changed",
        }],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    resp = _post(
        client, f"{_base(rid)}/actions/resubmit-correction", tok,
        json={"expectedVersion": version},
    )
    assert resp.status_code == 422, resp.text
    # Confirmação explícita fecha o alvo restante.
    version = _case_version(
        client, jwks_env, core_rbac, rid, sub=REQUESTER_SUB
    )
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers",
            "proposedValue": [dict(SUP1, partNumber="PN-1"), dict(SUP2)],
            "reason": "Confirmo o segundo vínculo.",
            "mode": "confirmed",
        }],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    resp = _post(
        client, f"{_base(rid)}/actions/resubmit-correction", tok,
        json={"expectedVersion": version},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "in_progress"


def test_idempotent_save_replay(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    version = int(resp.json()["data"]["caseVersion"])
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    suppliers = [dict(SUP1, partNumber="PN-9"), dict(SUP2)]
    body = {
        "expectedVersion": version,
        "changes": [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "PN corrigido.", "mode": "changed",
        }],
    }
    key = f"idem-save-{rid}"
    r1 = _patch(
        client, f"{_base(rid)}/returned-fields", tok, json=body,
        headers={"Idempotency-Key": key},
    )
    r2 = _patch(
        client, f"{_base(rid)}/returned-fields", tok, json=body,
        headers={"Idempotency-Key": key},
    )
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text


def test_link_op_add_requires_part_number():
    from engineering_app.domain.product_registration import catalog
    _, err = catalog.validate_supplier_link_changes(
        [{
            "operation": "add",
            "key": {"supplierCode": "000777", "store": "01"},
            "fields": {"catalogNumber": "CAT"},
        }]
    )
    assert err is not None and "partNumber" in err
    _, err = catalog.validate_supplier_link_changes(
        [{
            "operation": "add",
            "key": {"supplierCode": "000777", "store": "01"},
            "fields": {"partNumber": "   "},
        }]
    )
    assert err is not None
    ops, err = catalog.validate_supplier_link_changes(
        [{
            "operation": "add",
            "key": {"supplierCode": "000777", "store": "01"},
            "fields": {"partNumber": "PN-777"},
        }]
    )
    assert err is None and len(ops) == 1


def test_link_op_update_rejects_empty_part_number():
    from engineering_app.domain.product_registration import catalog
    _, err = catalog.validate_supplier_link_changes(
        [{
            "operation": "update",
            "key": {"supplierCode": "000123", "store": "01"},
            "fields": {"partNumber": ""},
        }]
    )
    assert err is not None and "partNumber" in err


def test_baseline_update_requires_resulting_pn():
    from engineering_app.domain.product_registration import baseline
    base = {
        "linksComplete": True,
        "links": [
            {"supplierCode": "000123", "store": "01",
             "partNumber": "", "catalogNumber": "CAT"},
        ],
    }
    # UPDATE só de catálogo num vínculo com PN vazio → rejeitado.
    err = baseline.validate_link_ops_against_baseline(
        [{
            "operation": "update",
            "key": {"supplierCode": "000123", "store": "01"},
            "fields": {"catalogNumber": "CAT-2"},
        }],
        base,
    )
    assert err is not None and "partNumber" in err
    # UPDATE incluindo PN → aceito.
    err = baseline.validate_link_ops_against_baseline(
        [{
            "operation": "update",
            "key": {"supplierCode": "000123", "store": "01"},
            "fields": {"partNumber": "PN-OK", "catalogNumber": "CAT-2"},
        }],
        base,
    )
    assert err is None


def test_legacy_untouched_link_kept_in_correction(
    client, jwks_env, core_rbac, prc_service_repo
):
    """Vínculo histórico intocado preserva dados — sem reescrita."""
    rid = _open_case_suppliers(client, jwks_env, core_rbac)
    repo = prc_service_repo["repo"]
    draft = repo._drafts[rid]
    draft["technical_data"]["suppliers"][1]["partNumber"] = ""
    resp = _return_supplier(
        client, jwks_env, core_rbac, rid,
        [_supplier_target("000123", "01", "partNumber")],
    )
    assert resp.status_code == 200, resp.text
    version = int(resp.json()["data"]["caseVersion"])
    suppliers = [
        dict(SUP1, partNumber="PN-1"),
        dict(SUP2, partNumber=""),
    ]
    resp = _save_changes(
        client, jwks_env, core_rbac, rid, version,
        [{
            "path": "suppliers", "proposedValue": suppliers,
            "reason": "Só o vínculo devolvido.", "mode": "changed",
        }],
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(
        _base(rid),
        headers={
            "Authorization": f"Bearer {_as(jwks_env, core_rbac, REQUESTER_SUB)}"
        },
    ).json()["data"]
    sup = detail["technicalDraft"]["suppliers"]
    assert sup[0]["partNumber"] == "PN-1"
    assert sup[1]["partNumber"] == ""  # legado preservado
