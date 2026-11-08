"""PRC-C1/C2/C3 — testes do vertical Product Registration.

Cobertura dos AC-PRC-MVP-* executáveis neste ciclo: intake, identidade,
idempotência, alteração seletiva, workflow, CAS, escopo, verificação
oficial (not_found/mismatch/unverifiable/unavailable/timeout),
conclusão única, rejeição sem side-effect, permissões granulares.
"""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload

from engineering_app.composition import prc_composer
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
    InMemoryProductRegistrationRepository,
)

# Modelo de duas permissões (PO 2026-11-06): CRUD operacional = access.
ENG_ACCESS = "engineering.access"
ANALYST = [ENG_ACCESS]
REQUESTER = [ENG_ACCESS]


@pytest.fixture
def prc_service_repo(monkeypatch):
    """Service singleton com repo in-memory + reader injetável."""
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


def _create_body(**over):
    body = {
        "source": "engineering-test",
        "externalRequestId": "ext-1",
        "requestType": "create",
        "productType": "raw_material",
        "schemaVersion": 1,
        "requestedData": {
            "description": "MATERIAL TESTE",
            "group": "1001",
            "productKind": "MP",
            "defaultWarehouse": "01",
            "unit": "UN",
            "thirdPartyProduct": "1",
            "accountingAccount": "11401002",
            "customerReference": "",
            "suppliers": [
                {
                    "supplierCode": "000001",
                    "store": "01",
                    "supplierName": "FORNECEDOR X",
                    "partNumber": "PN-1",
                    "catalogNumber": None,
                }
            ],
        },
    }
    body.update(over)
    return body


def _token(jwks_env, sub="user-1"):
    return jwks_env["make_token"](sub=sub)


def _post(client, url, token, json=None, headers=None):
    h = {"Authorization": f"Bearer {token}"}
    if headers:
        h.update(headers)
    return client.post(url, json=json or {}, headers=h)


def _get(client, url, token):
    return client.get(url, headers={"Authorization": f"Bearer {token}"})


def _submit_create(client, jwks_env, core_rbac, sub="user-1"):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    return _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env, sub),
        json=_create_body(),
        headers={"Idempotency-Key": "k-1"},
    )


def _advance_to_review(client, jwks_env, core_rbac, rid, sub="analyst-1"):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    tok = _token(jwks_env, sub)
    r = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/start",
        tok, json={"expectedVersion": 1},
    )
    assert r.status_code == 200, r.text
    r = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/submit-review",
        tok, json={"expectedVersion": 2},
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]["caseVersion"]


class FakeReader:
    def __init__(self, result):
        self._result = result

    async def read_product(self, *, access_token, request_id, official_code):
        return self._result


def _product(**over):
    product = {
        "code": "001234",
        "description": "MATERIAL TESTE",
        "group_code": "1001",
        "type": "MP",
        "default_warehouse": "01",
        "unit": "UN",
        "material_type": "1",
        "customer_reference": "",
        "accounting_account": "11401002",
    }
    product.update(over)
    return {
        "status": "available",
        "product": product,
        "suppliers": [
            {
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-1",
                "catalog_code": None,
            }
        ],
    }


class TestIntake:
    def test_create_happy_path(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        resp = _submit_create(client, jwks_env, core_rbac)
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["caseStatus"] == "submitted"
        assert data["requestType"] == "create"
        assert data["caseVersion"] == 1

    def test_idempotent_replay_same_key(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        first = _submit_create(client, jwks_env, core_rbac)
        assert first.status_code == 201
        second = _submit_create(client, jwks_env, core_rbac)
        assert second.status_code == 200
        assert second.json()["data"]["requestId"] == (
            first.json()["data"]["requestId"]
        )

    def test_same_key_different_payload_409(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _submit_create(client, jwks_env, core_rbac)
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=_create_body(
                requestedData={"description": "OUTRO"}
            ),
            headers={"Idempotency-Key": "k-1"},
        )
        assert resp.status_code == 409

    def test_forbidden_without_create(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Sem engineering.access → 403 (fail-closed); com access, CRUD abre.
        core_rbac["behavior"] = (
            "data", rbac_payload(["dashboard-engineering.view"])
        )
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=_create_body(),
        )
        assert resp.status_code == 403

    def test_source_not_allowlisted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=_create_body(source="evil-origin"),
        )
        assert resp.status_code == 403

    def test_missing_required_field_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        payload = _create_body()
        del payload["requestedData"]["unit"]
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=payload,
        )
        assert resp.status_code == 422
        assert "unit" in str(resp.json()["data"]["fields"])

    def test_requester_is_jwt_sub_not_body(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        resp = _submit_create(client, jwks_env, core_rbac, sub="real-user")
        rid = resp.json()["data"]["requestId"]
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "real-user"),
        )
        assert detail.json()["data"]["requester"]["subject"] == "real-user"


class TestUpdate:
    def _update_body(self, changes, code="001234", base=1):
        return {
            "source": "engineering-test",
            "requestType": "update",
            "productType": "raw_material",
            "schemaVersion": 1,
            "officialProductCode": code,
            "baseRevision": base,
            "changes": changes,
        }

    def test_update_requires_changes(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=self._update_body(changes=[], base=None),
        )
        assert resp.status_code == 422

    def test_update_single_field_no_record(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=self._update_body(
                changes=[
                    {
                        "path": "description",
                        "proposedValue": "NOVA DESC",
                        "reason": "correção",
                    }
                ],
                base=None,
            ),
        )
        assert resp.status_code == 201, resp.text
        rid = resp.json()["data"]["requestId"]
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env),
        ).json()["data"]
        assert detail["technicalDraft"]["description"] == "NOVA DESC"
        assert detail["technicalDraft"]["officialProductCode"] == "001234"

    def test_unknown_path_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=self._update_body(
                changes=[
                    {
                        "path": "internalSecret",
                        "proposedValue": "x",
                        "reason": "r",
                    }
                ],
                base=None,
            ),
        )
        assert resp.status_code == 422


class TestWorkflow:
    def test_full_workflow_and_cas(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        version = _advance_to_review(client, jwks_env, core_rbac, rid)
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "under_review"
        assert version == 3
        # stale version → 409
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/reject",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1, "reason": "stale"},
        )
        assert resp.status_code == 409

    def test_draft_patch_only_in_progress(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        tok = _token(jwks_env, "analyst-1")
        _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/start",
            tok, json={"expectedVersion": 1},
        )
        resp = client.patch(
            f"/v1/product-registration/requests/{rid}/draft",
            json={
                "expectedVersion": 2,
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "DESC CORRIGIDA",
                        "reason": "padronização",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert resp.status_code == 200, resp.text
        assert (
            resp.json()["data"]["technicalDraft"]["description"]
            == "DESC CORRIGIDA"
        )

    def test_needs_information_resume(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        tok = _token(jwks_env, "analyst-1")
        _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/start",
            tok, json={"expectedVersion": 1},
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/request-information",
            tok,
            json={
                "expectedVersion": 2,
                "reason": "falta ficha técnica",
                "pendingFields": ["unit"],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "needs_information"
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/resume",
            tok, json={"expectedVersion": 3},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "in_progress"

    def test_reject_does_not_touch_record(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/reject",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1, "reason": "duplicada"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "rejected"
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["allowedActions"] == []
        assert detail["completedRecordId"] is None

    def test_scope_access_sees_foreign_request(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="user-1"
        ).json()["data"]["requestId"]
        core_rbac["behavior"] = (
            "data", rbac_payload(REQUESTER, id="user-2")
        )
        resp = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "user-2"),
        )
        assert resp.status_code == 200

    def test_requester_without_access_denied(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _submit_create(client, jwks_env, core_rbac, sub="user-1")
        core_rbac["behavior"] = (
            "data", rbac_payload([], id="user-2")
        )
        resp = _get(
            client, "/v1/product-registration/requests",
            _token(jwks_env, "user-2"),
        )
        assert resp.status_code == 403


class TestVerifyAndComplete:
    def _ready_request(
        self, client, jwks_env, core_rbac, prc_service_repo, reader
    ):
        prc_service_repo["reader"] = reader
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        version = _advance_to_review(client, jwks_env, core_rbac, rid)
        return rid, version

    def test_not_found_does_not_complete(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader({"status": "not_found"}),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 409
        assert resp.json()["data"]["code"] == "erp_mismatch"
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "under_review"
        verifs = _get(
            client,
            f"/v1/product-registration/requests/{rid}/verifications",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]["items"]
        assert verifs[-1]["result"] == "not_found"

    def test_mismatched_description_blocks(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader(_product(description="OUTRA DESCRICAO")),
        )
        # Remove o campo CONTRACT_GAP para isolar a divergência real.
        prc_service_repo["repo"]._drafts[rid][
            "technical_data"
        ].pop("accountingAccount", None)
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 409
        fields = resp.json()["data"]["fieldResults"]
        assert fields["description"]["result"] == "mismatched"

    def test_unverifiable_field_blocks(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Campo ausente no payload oficial → unverifiable (fail-closed).
        product = _product()
        product["product"].pop("accounting_account", None)
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader(product),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 422
        assert resp.json()["data"]["code"] == "unverifiable_field"

    def test_supplier_part_number_mismatch_blocks(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader(
                {
                    "status": "available",
                    "product": {
                        "code": "001234",
                        "description": "MATERIAL TESTE",
                        "group_code": "1001",
                        "type": "MP",
                        "default_warehouse": "01",
                        "unit": "UN",
                        "material_type": "1",
                        "customer_reference": "",
                    },
                    "suppliers": [
                        {
                            "supplier_code": "000001",
                            "supplier_store": "01",
                            "supplier_name": "FORNECEDOR X",
                            "supplier_part_number": "OUTRO-PN",
                            "catalog_code": None,
                        }
                    ],
                }
            ),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 422

    def test_unavailable_blocks(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader({"status": "unavailable"}),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 503

    def test_timeout_blocks(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader({"status": "timeout"}),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 504

    def test_full_match_completes_once(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Remove accountingAccount do draft para fechar com contrato atual.
        repo = prc_service_repo["reader"] = FakeReader(_product())
        resp = _submit_create(client, jwks_env, core_rbac)
        rid = resp.json()["data"]["requestId"]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        tok = _token(jwks_env, "analyst-1")
        _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/start",
            tok, json={"expectedVersion": 1},
        )
        _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/submit-review",
            tok, json={"expectedVersion": 2},
        )
        # accountingAccount agora é verificável via view=engineering.
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            tok,
            json={"expectedVersion": 3, "officialCode": "001234"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["status"] == "completed"
        assert data["revisionNumber"] == 1
        record_id = data["recordId"]
        # terminal: segunda conclusão → 409
        resp2 = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            tok,
            json={"expectedVersion": 4, "officialCode": "001234"},
        )
        assert resp2.status_code == 409
        # revisão imutável consultável
        rev = _get(
            client,
            f"/v1/product-registration/technical-records/{record_id}",
            tok,
        )
        assert rev.status_code == 200
        assert rev.json()["data"]["official_product_code"] == "001234"


class TestReferenceData:
    def test_reference_data_fields(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(REQUESTER))
        resp = _get(
            client,
            "/v1/product-registration/reference-data",
            _token(jwks_env),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        paths = {f["path"] for f in data["fields"]}
        assert "partNumber" not in paths
        assert "accountingAccount" in paths
        spec = next(
            f for f in data["fields"] if f["path"] == "accountingAccount"
        )
        assert spec["verifiable"] is True
        kind_spec = next(
            f for f in data["fields"] if f["path"] == "productKind"
        )
        # Enum oficial do domínio (B1_TIPO canônico) anunciado ao MFE;
        # kind permanece "code" — backend não rejeita outros tipos legados.
        assert kind_spec["kind"] == "code"
        assert kind_spec["enumValues"] == ["MP", "PA", "PI"]
        third_party = next(
            f for f in data["fields"] if f["path"] == "thirdPartyProduct"
        )
        assert third_party["enumValues"] == ["1", "2"]
        assert "suppliers" in data["editableDraftPaths"]
        assert data["permissions"]["access"] == "engineering.access"


class TestOutbound:
    def test_outbound_request(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        resp = _get(
            client,
            f"/v1/product-registration/outbound/requests/{rid}",
            _token(jwks_env),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "submitted"
        assert "technicalDraft" not in data


def _create_body_with_suppliers(suppliers):
    body = _create_body()
    body["requestedData"]["suppliers"] = suppliers
    return body


class TestSupplierPartNumber:
    """PO-D5.4: partNumber (A5_CODPRF) opcional — identidade por (code,store)."""

    def _submit(self, client, jwks_env, core_rbac, suppliers, sub="user-1"):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
        return _post(
            client, "/v1/product-registration/intake/requests",
            _token(jwks_env, sub),
            json=_create_body_with_suppliers(suppliers),
            headers={"Idempotency-Key": "k-pn-" + sub + str(len(suppliers))},
        )

    def _sup(self, **kw):
        s = {"supplierCode": "000001", "store": "01",
             "supplierName": "FORNECEDOR X", "partNumber": "PN-1",
             "catalogNumber": None}
        s.update(kw)
        return s

    def _verify(self, client, jwks_env, core_rbac, prc_service_repo,
                suppliers, observed):
        prc_service_repo["reader"] = FakeReader(
            {"status": "available",
             "product": _product()["product"], "suppliers": observed})
        rid = self._submit(
            client, jwks_env, core_rbac, suppliers).json()["data"]["requestId"]
        v = _advance_to_review(client, jwks_env, core_rbac, rid)
        return _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": v, "officialCode": "001234"}), rid

    # --- intake validation -------------------------------------------------
    def test_intake_pn_empty_accepted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = self._submit(client, jwks_env, core_rbac,
                         [self._sup(partNumber="")])
        assert r.status_code == 201, r.text
        draft = r.json()["data"].get("draft", {})
        # normalized canonical representation is ""
        assert draft.get("suppliers", [{}])[0].get("partNumber", "") == ""

    def test_intake_pn_omitted_accepted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        s = self._sup(); s.pop("partNumber")
        r = self._submit(client, jwks_env, core_rbac, [s])
        assert r.status_code == 201, r.text

    def test_intake_pn_null_accepted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = self._submit(client, jwks_env, core_rbac,
                         [self._sup(partNumber=None)])
        assert r.status_code == 201, r.text

    # --- official comparison ------------------------------------------------
    def test_match_empty_pn_vs_empty_official(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Cenário A — exp "" + obs "" → completed (caso real 90264270/WEG)
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "", "catalog_code": None}]
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup(partNumber="")], obs)
        assert r.status_code == 200, r.text
        assert r.json()["data"]["status"] == "completed"

    def test_match_filled_pn(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-1", "catalog_code": None}]
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup()], obs)
        assert r.status_code == 200, r.text

    def test_mismatch_filled_pn_differs(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-OUTRO", "catalog_code": None}]
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup()], obs)
        assert r.status_code == 409

    def test_mismatch_empty_pn_vs_filled_official(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Cenário D — ficha aprovada diz vazio; oficial tem PN → mismatch.
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-1", "catalog_code": None}]
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup(partNumber="")], obs)
        assert r.status_code == 409

    def test_unverifiable_when_official_attr_absent(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Cenário E — campo omitido no payload oficial → unverifiable.
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X", "catalog_code": None}]
        r, rid = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup()], obs)
        assert r.status_code == 409
        verif = r.json()["data"]["verification"]
        assert verif["field_results"]["suppliers"]["result"] == "unverifiable"

    def test_ambiguous_official_link(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        row = {"supplier_code": "000001", "supplier_store": "01",
               "supplier_name": "FORNECEDOR X",
               "supplier_part_number": "PN-1", "catalog_code": None}
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup()], [row, dict(row)])
        assert r.status_code == 409

    def test_ambiguous_expected_link(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-1", "catalog_code": None}]
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup(), self._sup()], obs)
        assert r.status_code == 409
