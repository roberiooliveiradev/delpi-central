"""D15 — baseline SA5, pré/pós-condições e gate REMOVE PENDING_OWNER."""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from engineering_app.composition import prc_composer
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
    InMemoryProductRegistrationRepository,
)
from tests.test_product_registration import (
    ANALYST,
    FakeReader,
    _advance_to_review,
    _attach_reader,
    _get,
    _post,
    _product,
    _token,
)


@pytest.fixture
def prc_service_repo(monkeypatch):
    """Mesmo harness de ``test_product_registration`` (fixture local)."""
    prc_composer.reset_prc_singletons()
    repo = InMemoryProductRegistrationRepository()
    state = {"reader": None, "repo": repo}

    class _ReaderProxy:
        async def read_product(self, *, access_token, request_id,
                               official_code):
            return await state["reader"].read_product(
                access_token=access_token,
                request_id=request_id,
                official_code=official_code,
            )

    from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
        ProductRegistrationService,
    )

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(repo, official_reader=_ReaderProxy())
    )
    yield state
    prc_composer.reset_prc_singletons()
    prc_composer.set_prc_service_for_tests(None)


def _update_sa5(ops, code="001234", fingerprint=None):
    body = {
        "source": "engineering-test",
        "requestType": "update",
        "productType": "raw_material",
        "schemaVersion": 1,
        "officialProductCode": code,
        "changes": [],
        "supplierLinkChanges": ops,
    }
    if fingerprint:
        body["baselineFingerprint"] = fingerprint
    return body


def test_d15_baseline_module_fingerprint_stable():
    from engineering_app.domain.product_registration import baseline as b

    observed = _product()
    a = b.build_official_baseline(
        observed,
        official_code="001234",
        captured_by="u1",
        correlation_id="c1",
        captured_at="2026-01-01T00:00:00+00:00",
    )
    b2 = b.build_official_baseline(
        observed,
        official_code="001234",
        captured_by="u2",
        correlation_id="c2",
        captured_at="2026-01-02T00:00:00+00:00",
    )
    assert a["fingerprint"] == b2["fingerprint"]
    assert a["linksComplete"] is True
    assert len(a["links"]) == 1


def test_d15_precondition_add_existing_rejected():
    from engineering_app.domain.product_registration import baseline as b

    baseline = b.build_official_baseline(
        _product(),
        official_code="001234",
        captured_by="u",
        correlation_id="c",
        captured_at="t",
    )
    err = b.validate_link_ops_against_baseline(
        [{"operation": "add",
          "key": {"supplierCode": "000001", "store": "01"},
          "fields": {"partNumber": "X"}}],
        baseline,
    )
    assert err and "já existe" in err


def test_d15_precondition_add_absent_ok():
    from engineering_app.domain.product_registration import baseline as b

    baseline = b.build_official_baseline(
        _product(),
        official_code="001234",
        captured_by="u",
        correlation_id="c",
        captured_at="t",
    )
    err = b.validate_link_ops_against_baseline(
        [{"operation": "add",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"partNumber": "PN-N"}}],
        baseline,
    )
    assert err is None


def test_d15_precondition_update_missing_rejected():
    from engineering_app.domain.product_registration import baseline as b

    baseline = b.build_official_baseline(
        _product(),
        official_code="001234",
        captured_by="u",
        correlation_id="c",
        captured_at="t",
    )
    err = b.validate_link_ops_against_baseline(
        [{"operation": "update",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"partNumber": "PN-2"}}],
        baseline,
    )
    assert err and "ausente" in err


def test_d15_precondition_incomplete_baseline():
    from engineering_app.domain.product_registration import baseline as b

    baseline = b.build_official_baseline(
        _product(suppliers_complete=False),
        official_code="001234",
        captured_by="u",
        correlation_id="c",
        captured_at="t",
    )
    err = b.validate_link_ops_against_baseline(
        [{"operation": "add",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"partNumber": "X"}}],
        baseline,
    )
    assert err and "incompleto" in err


def test_d15_precondition_ambiguous_key():
    from engineering_app.domain.product_registration import baseline as b

    observed = _product(
        suppliers=[
            {"supplier_code": "000001", "supplier_store": "01",
             "supplier_name": "A", "supplier_part_number": "1",
             "catalog_code": ""},
            {"supplier_code": "000001", "supplier_store": "01",
             "supplier_name": "B", "supplier_part_number": "2",
             "catalog_code": ""},
        ]
    )
    baseline = b.build_official_baseline(
        observed,
        official_code="001234",
        captured_by="u",
        correlation_id="c",
        captured_at="t",
    )
    err = b.validate_link_ops_against_baseline(
        [{"operation": "update",
          "key": {"supplierCode": "000001", "store": "01"},
          "fields": {"partNumber": "9"}}],
        baseline,
    )
    assert err and "ambígua" in err


def test_d15_intake_persists_baseline(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json={
            "source": "engineering-test",
            "requestType": "update",
            "productType": "raw_material",
            "schemaVersion": 1,
            "officialProductCode": "001234",
            "changes": [
                {"path": "description", "proposedValue": "NOVA",
                 "reason": "r"},
            ],
        },
        headers={"Idempotency-Key": "d15-b1"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    detail = _get(
        client, f"/v1/product-registration/requests/{rid}", _token(jwks_env)
    ).json()["data"]
    bl = detail["officialBaseline"]
    assert bl["officialProductCode"] == "001234"
    assert bl["linksComplete"] is True
    assert bl["fingerprint"]
    assert bl["removeCompletionPolicy"] == "PENDING_OWNER"
    assert detail["removeCompletionPolicy"] == "PENDING_OWNER"


def test_d15_intake_add_duplicate_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5([
            {"operation": "add",
             "key": {"supplierCode": "000001", "store": "01"},
             "fields": {"partNumber": "X"}},
        ]),
        headers={"Idempotency-Key": "d15-add-dup"},
    )
    assert resp.status_code == 422, resp.text
    assert "baseline_precondition" in str(resp.json())


def test_d15_intake_add_new_accepted(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5([
            {"operation": "add",
             "key": {"supplierCode": "000089", "store": "01"},
             "fields": {"partNumber": "PN-N", "catalogNumber": ""}},
        ]),
        headers={"Idempotency-Key": "d15-add-ok"},
    )
    assert resp.status_code == 201, resp.text


def test_d15_intake_stale_fingerprint(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5(
            [{"operation": "add",
              "key": {"supplierCode": "000089", "store": "01"},
              "fields": {"partNumber": "PN-N"}}],
            fingerprint="deadbeef" * 8,
        ),
        headers={"Idempotency-Key": "d15-stale"},
    )
    assert resp.status_code == 409, resp.text
    assert resp.json()["data"]["code"] == "official_context_stale"


def test_d15_intake_incomplete_sa5_blocks_link_ops(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo, _product(suppliers_complete=False))
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5([
            {"operation": "add",
             "key": {"supplierCode": "000089", "store": "01"},
             "fields": {"partNumber": "X"}},
        ]),
        headers={"Idempotency-Key": "d15-inc"},
    )
    assert resp.status_code == 422, resp.text


def test_d15_remove_completion_pending_owner(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5([
            {"operation": "remove",
             "key": {"supplierCode": "000001", "store": "01"},
             "fields": {}, "reason": "desvincular"},
        ]),
        headers={"Idempotency-Key": "d15-rm"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    # Simula atendimento TOTVS: vínculo já ausente no read-back
    prc_service_repo["reader"] = FakeReader(
        _product(suppliers=[])
    )
    v = _advance_to_review(client, jwks_env, core_rbac, rid)
    done = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
        _token(jwks_env, "analyst-1"),
        json={"expectedVersion": v, "officialCode": "001234"},
    )
    assert done.status_code == 409, done.text
    assert done.json()["data"]["code"] == "remove_completion_pending_owner"
    # nenhuma revisão publicada
    detail = _get(
        client, f"/v1/product-registration/requests/{rid}",
        _token(jwks_env, "analyst-1"),
    ).json()["data"]
    assert detail["status"] == "under_review"
    assert detail["completedRecordId"] is None


def test_d15_update_pn_selective_verify(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(
        prc_service_repo,
        _product(
            suppliers=[{
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-1",
                "catalog_code": "CAT-1",
            }]
        ),
    )
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5([
            {"operation": "update",
             "key": {"supplierCode": "000001", "store": "01"},
             "fields": {"partNumber": "PN-2"}},
        ]),
        headers={"Idempotency-Key": "d15-upd-pn"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    # Catálogo permanece CAT-1; só PN muda — verify seletivo
    prc_service_repo["reader"] = FakeReader(
        _product(
            suppliers=[{
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-2",
                "catalog_code": "CAT-1",
            }]
        )
    )
    v = _advance_to_review(client, jwks_env, core_rbac, rid)
    done = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
        _token(jwks_env, "analyst-1"),
        json={"expectedVersion": v, "officialCode": "001234"},
    )
    assert done.status_code == 200, done.text
    assert done.json()["data"]["status"] == "completed"


def test_d15_add_verify_presence_after(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env),
        json=_update_sa5([
            {"operation": "add",
             "key": {"supplierCode": "000089", "store": "01"},
             "fields": {"partNumber": "PN-N", "catalogNumber": "C"}},
        ]),
        headers={"Idempotency-Key": "d15-add-v"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    # pós: ADD ainda ausente → mismatch, sem revisão
    prc_service_repo["reader"] = FakeReader(_product())
    v = _advance_to_review(client, jwks_env, core_rbac, rid)
    done = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
        _token(jwks_env, "analyst-1"),
        json={"expectedVersion": v, "officialCode": "001234"},
    )
    assert done.status_code == 409, done.text
    # pós: presente com atributos → complete
    prc_service_repo["reader"] = FakeReader(
        _product(
            suppliers=[
                {
                    "supplier_code": "000001",
                    "supplier_store": "01",
                    "supplier_name": "FORNECEDOR X",
                    "supplier_part_number": "PN-1",
                    "catalog_code": None,
                },
                {
                    "supplier_code": "000089",
                    "supplier_store": "01",
                    "supplier_name": "NOVO",
                    "supplier_part_number": "PN-N",
                    "catalog_code": "C",
                },
            ]
        )
    )
    done2 = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
        _token(jwks_env, "analyst-1"),
        json={"expectedVersion": v, "officialCode": "001234"},
    )
    assert done2.status_code == 200, done2.text


def test_d15_edit_context_exposes_fingerprint(
    client, jwks_env, core_rbac, prc_service_repo
):
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
    resp = _get(
        client,
        "/v1/product-registration/reference-data/products/001234/edit-context",
        _token(jwks_env),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["fingerprint"]
    assert data["sourceContractVersion"] == "prc-sa5-baseline.v1"
    assert data["removeCompletionPolicy"] == "PENDING_OWNER"
