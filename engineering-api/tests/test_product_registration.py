"""PRC-C1/C2/C3 — testes do vertical Product Registration.

Cobertura dos AC-PRC-MVP-* executáveis neste ciclo: intake, identidade,
idempotência, alteração seletiva, workflow, CAS, escopo, verificação
oficial (not_found/mismatch/unverifiable/unavailable/timeout),
conclusão única, rejeição sem side-effect, permissões granulares.
"""

from __future__ import annotations

import uuid

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
    from engineering_app.infrastructure.storage.prc_attachment_storage import (  # noqa: E501
        MemoryAttachmentStorage,
    )

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(
            repo,
            official_reader=_ReaderProxy(),
            attachment_storage=MemoryAttachmentStorage(),
        )
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


def _advance_to_attendance(
    client, jwks_env, core_rbac, rid, sub="analyst-1",
):
    """PRC-REF-020 — deixa a solicitação em ``in_progress`` (pronto
    para Concluir atendimento)."""
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    tok = _token(jwks_env, sub)
    r = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/start",
        tok, json={"expectedVersion": 1},
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]["caseVersion"]


def _advance_to_review(client, jwks_env, core_rbac, rid, sub="analyst-1"):
    """LEGADO — sobe até ``under_review`` (compat alias submit-review)."""
    version = _advance_to_attendance(
        client, jwks_env, core_rbac, rid, sub=sub,
    )
    tok = _token(jwks_env, sub)
    r = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/submit-review",
        tok, json={"expectedVersion": version},
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
    suppliers = over.pop("suppliers", None)
    suppliers_complete = over.pop("suppliers_complete", True)
    status = over.pop("status", "available")
    product.update(over)
    return {
        "status": status,
        "product": product,
        "suppliers": suppliers if suppliers is not None else [
            {
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-1",
                "catalog_code": None,
            }
        ],
        "suppliers_complete": suppliers_complete,
    }


def _attach_reader(prc_service_repo, result=None):
    prc_service_repo["reader"] = FakeReader(result or _product())


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
        _attach_reader(prc_service_repo)
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
        assert detail["officialBaseline"]["officialProductCode"] == "001234"
        assert detail["officialBaseline"]["linksComplete"] is True
        assert detail["officialBaseline"]["fingerprint"]

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
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "in_progress"
        assert "complete" in detail["allowedActions"]
        assert "submit_review" not in detail["allowedActions"]
        assert version == 2
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

    def test_draft_patch_state_and_owner_policy(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """FIX-08 — o criador edita em submitted; iniciado o
        atendimento, a ficha vira somente leitura para todos."""
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="user-1")
        )
        tok = _token(jwks_env, "user-1")
        # Criador edita em submitted (mesmo requestId, CAS v1).
        resp = client.patch(
            f"/v1/product-registration/requests/{rid}/draft",
            json={
                "expectedVersion": 1,
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
        # Analista de terceiro não edita a ficha alheia nem em submitted.
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        tok_a = _token(jwks_env, "analyst-1")
        resp = client.patch(
            f"/v1/product-registration/requests/{rid}/draft",
            json={
                "expectedVersion": 2,
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "HIJACK",
                        "reason": "x",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {tok_a}"},
        )
        assert resp.status_code == 403, resp.text
        # Início do atendimento → escrita bloqueada para ambos os papéis.
        _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/start",
            tok_a, json={"expectedVersion": 2},
        )
        for t, expected in ((tok, 403), (tok_a, 403)):
            resp = client.patch(
                f"/v1/product-registration/requests/{rid}/draft",
                json={
                    "expectedVersion": 3,
                    "changes": [
                        {
                            "path": "description",
                            "proposedValue": "LATE",
                            "reason": "x",
                        }
                    ],
                },
                headers={"Authorization": f"Bearer {t}"},
            )
            assert resp.status_code in (403, 409), resp.text

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
            tok,
            json={
                "expectedVersion": 3,
                # PRC-REF-019: rodada aberta bloqueia resume sem waiver.
                "reason": "waiver: retorno interno legado",
            },
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
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
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
            f"/v1/product-registration/requests/{rid}/actions/complete",
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
        assert detail["status"] == "in_progress"
        verifs = _get(
            client,
            f"/v1/product-registration/requests/{rid}/verifications",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]["items"]
        assert verifs[-1]["result"] == "not_found"

    def test_complete_rejects_submitted_status(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        prc_service_repo["reader"] = FakeReader(_product())
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1, "officialCode": "001234"},
        )
        assert resp.status_code == 409
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "submitted"
        assert detail.get("completedRecordId") is None

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
            f"/v1/product-registration/requests/{rid}/actions/complete",
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
            f"/v1/product-registration/requests/{rid}/actions/complete",
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
            f"/v1/product-registration/requests/{rid}/actions/complete",
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
            f"/v1/product-registration/requests/{rid}/actions/complete",
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
            f"/v1/product-registration/requests/{rid}/actions/complete",
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
        started = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/start",
            tok, json={"expectedVersion": 1},
        )
        assert started.status_code == 200, started.text
        version = started.json()["data"]["caseVersion"]
        # PRC-REF-020 — conclusão direta a partir de in_progress.
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            tok,
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["status"] == "completed"
        assert data["revisionNumber"] == 1
        record_id = data["recordId"]
        # alias legado aponta para o mesmo use case (já terminal → 409)
        resp2 = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/verify-and-complete",
            tok,
            json={"expectedVersion": version + 1, "officialCode": "001234"},
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

    def test_create_completion_requires_official_code(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """PRC-REF-017 — CREATE sem código na conclusão → 422."""
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader(_product()),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version},
        )
        assert resp.status_code == 422
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "in_progress"
        assert not detail.get("officialCode")

    def test_create_intake_without_official_code(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """PRC-REF-017 — CREATE intake não exige código oficial."""
        resp = _submit_create(client, jwks_env, core_rbac)
        assert resp.status_code == 201
        rid = resp.json()["data"]["requestId"]
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env),
        ).json()["data"]
        assert detail["requestType"] == "create"
        assert not detail.get("officialCode")

    def test_create_invalid_official_code(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader(_product()),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "   "},
        )
        assert resp.status_code == 422

    def test_create_leading_zeros_preserved(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        product = _product()
        product["product"]["code"] = "001234"
        rid, version = self._ready_request(
            client, jwks_env, core_rbac, prc_service_repo,
            FakeReader(product),
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["officialCode"] == "001234"

    def test_update_rejects_arbitrary_code_swap(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """PRC-REF-017 — UPDATE não troca officialCode na conclusão."""
        _attach_reader(prc_service_repo)
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        create = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json={
                "source": "engineering-test",
                "requestType": "update",
                "productType": "raw_material",
                "schemaVersion": 1,
                "officialProductCode": "001234",
                "baseRevision": None,
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "NOVA DESC",
                        "reason": "correção",
                    }
                ],
            },
            headers={"Idempotency-Key": "k-upd-lock"},
        )
        assert create.status_code == 201, create.text
        rid = create.json()["data"]["requestId"]
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        prc_service_repo["reader"] = FakeReader(
            _product(description="NOVA DESC")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={
                "expectedVersion": version,
                "officialCode": "999999",
            },
        )
        assert resp.status_code == 422
        body = resp.json()["data"]
        assert "officialCode" in str(body.get("fields") or body)

    def test_update_field_results_include_previous(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """PRC-REF-017 — field_results UPDATE traz previous/expected/observed."""
        _attach_reader(prc_service_repo)
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        create = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json={
                "source": "engineering-test",
                "requestType": "update",
                "productType": "raw_material",
                "schemaVersion": 1,
                "officialProductCode": "001234",
                "baseRevision": None,
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "NOVA DESC",
                        "reason": "correção",
                    }
                ],
            },
            headers={"Idempotency-Key": "k-upd-prev"},
        )
        assert create.status_code == 201, create.text
        rid = create.json()["data"]["requestId"]
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        prc_service_repo["reader"] = FakeReader(
            _product(description="OUTRA")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 409
        fields = resp.json()["data"]["fieldResults"]
        assert fields["description"]["result"] == "mismatched"
        assert fields["description"]["expected"] == "NOVA DESC"
        assert fields["description"]["observed"] == "OUTRA"
        assert "previous" in fields["description"]
        assert set(fields.keys()) == {"description"}

    def test_update_selective_match_completes(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _attach_reader(prc_service_repo)
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        create = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json={
                "source": "engineering-test",
                "requestType": "update",
                "productType": "raw_material",
                "schemaVersion": 1,
                "officialProductCode": "001234",
                "baseRevision": None,
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "NOVA DESC",
                        "reason": "correção",
                    }
                ],
            },
            headers={"Idempotency-Key": "k-upd-ok"},
        )
        assert create.status_code == 201, create.text
        rid = create.json()["data"]["requestId"]
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        prc_service_repo["reader"] = FakeReader(
            _product(description="NOVA DESC")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["officialCode"] == "001234"
        assert resp.json()["data"]["status"] == "completed"


class TestTechnicalRecordsList:
    """PRC-TRACK PROD-01 — listagem de produtos acompanhados."""

    URL = "/v1/product-registration/technical-records"

    @staticmethod
    def _seed(repo, *, code, updated_at, rev=1, record_id=None,
              source="totvs-prd", ptype="raw_material"):
        rid = record_id or str(uuid.uuid4())
        repo._records[rid] = {
            "id": rid,
            "product_type": ptype,
            "official_product_code": code,
            "current_revision_number": rev,
            "last_official_verified_at": updated_at,
            "official_source": source,
            "created_at": updated_at,
            "updated_at": updated_at,
        }
        repo._record_by_key[(source, code)] = rid
        return rid

    def test_empty_list(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _get(client, self.URL, _token(jwks_env, "analyst-1"))
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["items"] == [] and data["total"] == 0

    def test_lists_only_published_records(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        repo = prc_service_repo["repo"]
        self._seed(repo, code="001", updated_at="2026-01-01T10:00:00+00:00")
        self._seed(repo, code="002", updated_at="2026-01-02T10:00:00+00:00")
        # registro preparatório sem revisão publicada não aparece
        self._seed(
            repo, code="003", rev=0,
            updated_at="2026-01-03T10:00:00+00:00",
        )
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        data = _get(
            client, self.URL, _token(jwks_env, "analyst-1")
        ).json()["data"]
        assert data["total"] == 2
        codes = [i["officialCode"] for i in data["items"]]
        assert codes == ["002", "001"]  # updatedAt DESC
        item = data["items"][0]
        assert set(item) == {
            "recordId", "officialSource", "officialCode", "productType",
            "currentRevisionNumber", "lastOfficialVerifiedAt", "updatedAt",
        }

    def test_pagination_and_deterministic_tiebreak(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        repo = prc_service_repo["repo"]
        ids = [
            self._seed(
                repo, code=f"10{i}",
                updated_at="2026-01-01T10:00:00+00:00",
            )
            for i in range(3)
        ]
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        p1 = _get(
            client, f"{self.URL}?page=1&pageSize=2",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        p2 = _get(
            client, f"{self.URL}?page=2&pageSize=2",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert p1["total"] == 3 and p1["page"] == 1 and p1["pageSize"] == 2
        got = [i["recordId"] for i in p1["items"] + p2["items"]]
        # updated_at empatado → desempate por id DESC
        assert got == sorted(ids, reverse=True)
        assert p2["page"] == 2 and len(p2["items"]) == 1

    def test_search_case_insensitive(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        repo = prc_service_repo["repo"]
        self._seed(repo, code="ABC123", updated_at="2026-01-01T00:00:00Z")
        self._seed(repo, code="XYZ999", updated_at="2026-01-01T00:00:00Z")
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        data = _get(
            client, f"{self.URL}?search=abc",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert [i["officialCode"] for i in data["items"]] == ["ABC123"]
        data = _get(
            client, f"{self.URL}?search=  ",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert data["total"] == 2

    def test_invalid_params(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        tok = _token(jwks_env, "analyst-1")
        assert _get(client, f"{self.URL}?page=0", tok).status_code == 422
        assert (
            _get(client, f"{self.URL}?pageSize=101", tok).status_code == 422
        )
        assert (
            _get(client, f"{self.URL}?pageSize=0", tok).status_code == 422
        )

    def test_requester_without_engineering_access_denied(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        self._seed(
            prc_service_repo["repo"], code="001",
            updated_at="2026-01-01T00:00:00Z",
        )
        # requester de Minhas Solicitações sem engineering.access → 403
        core_rbac["behavior"] = (
            "data", rbac_payload(["my-requests.access"], id="req-1")
        )
        resp = _get(client, self.URL, _token(jwks_env, "req-1"))
        assert resp.status_code == 403
        assert "001" not in resp.text

    def test_unauthenticated_denied(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        assert client.get(self.URL).status_code in (401, 403)

    def test_repository_unavailable_fails_honest(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        import engineering_app.composition.prc_composer as comp
        from engineering_app.infrastructure.persistence.product_registration.unavailable_repository import (  # noqa: E501
            UnavailableProductRegistrationRepository,
        )
        from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
            ProductRegistrationService,
        )
        comp.set_prc_service_for_tests(
            ProductRegistrationService(
                UnavailableProductRegistrationRepository(),
                official_reader=None,
                attachment_storage=None,
            )
        )
        core_rbac["behavior"] = ("data", rbac_payload(ANALYST))
        resp = _get(client, self.URL, _token(jwks_env, "analyst-1"))
        assert resp.status_code in (503, 500)
        assert resp.status_code != 200

    def test_completed_request_appears_in_list(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, version = TestVerifyAndComplete._ready_request(
            TestVerifyAndComplete(), client, jwks_env, core_rbac,
            prc_service_repo, FakeReader(_product()),
        )
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        resp = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": version, "officialCode": "001234"},
        )
        assert resp.status_code == 200, resp.text
        record_id = resp.json()["data"]["recordId"]
        data = _get(
            client, self.URL, _token(jwks_env, "analyst-1")
        ).json()["data"]
        assert data["total"] == 1
        item = data["items"][0]
        assert item["recordId"] == record_id
        assert item["officialCode"] == "001234"
        assert item["currentRevisionNumber"] == 1


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
    """PRC-REF-022-FIX-01: partNumber (A5_CODPRF) obrigatório —
    substitui a regra histórica PO-D5.4 que o tratava como opcional.
    Identidade do vínculo continua (code, store)."""

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
        v = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        return _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": v, "officialCode": "001234"}), rid

    # --- intake validation -------------------------------------------------
    def test_intake_pn_empty_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = self._submit(client, jwks_env, core_rbac,
                         [self._sup(partNumber="")])
        assert r.status_code == 422, r.text
        fields = r.json()["data"]["fields"]
        assert "partNumber" in str(fields)

    def test_intake_pn_omitted_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        s = self._sup(); s.pop("partNumber")
        r = self._submit(client, jwks_env, core_rbac, [s])
        assert r.status_code == 422, r.text

    def test_intake_pn_null_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = self._submit(client, jwks_env, core_rbac,
                         [self._sup(partNumber=None)])
        assert r.status_code == 422, r.text

    def test_intake_pn_whitespace_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = self._submit(client, jwks_env, core_rbac,
                         [self._sup(partNumber="   ")])
        assert r.status_code == 422, r.text

    def test_intake_pn_too_long_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = self._submit(client, jwks_env, core_rbac,
                         [self._sup(partNumber="P" * 81)])
        assert r.status_code == 422, r.text

    def test_intake_catalog_absent_accepted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        s = self._sup(); s.pop("catalogNumber")
        r = self._submit(client, jwks_env, core_rbac, [s])
        assert r.status_code == 201, r.text

    # --- official comparison ------------------------------------------------
    def test_completion_blocked_empty_pn(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Fail-closed: vínculo registrado/alterado sem PN não conclui,
        mesmo quando o oficial também está vazio (legado preservado só
        em vínculo intocado)."""
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "", "catalog_code": None}]
        # Intake já bloqueia PN vazio — a porta de conclusão é a
        # segunda linha de defesa para dados legados.
        r = self._submit(
            client, jwks_env, core_rbac, [self._sup(partNumber="")])
        assert r.status_code == 422, r.text
        # Estado legado simulado: draft histórico com PN vazio.
        rid = self._submit(
            client, jwks_env, core_rbac, [self._sup()]
        ).json()["data"]["requestId"]
        repo = prc_service_repo["repo"]
        draft = repo._drafts[rid]
        draft["technical_data"]["suppliers"][0]["partNumber"] = ""
        prc_service_repo["reader"] = FakeReader(
            {"status": "available",
             "product": _product()["product"], "suppliers": obs})
        v = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        r = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": v, "officialCode": "001234"})
        assert r.status_code == 422, r.text

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

    def test_mismatch_pn_differs_blocks(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # PN divergente do oficial → mismatch bloqueia conclusão.
        obs = [{"supplier_code": "000001", "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-DIFERENTE",
                "catalog_code": None}]
        r, _ = self._verify(
            client, jwks_env, core_rbac, prc_service_repo,
            [self._sup()], obs)
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
        # CORRECTION-10 — intake agora rejeita (code,store) duplicado;
        # o estado ambíguo legado é injetado direto no draft para
        # continuar provando o gate de conclusão.
        prc_service_repo["reader"] = FakeReader(
            {"status": "available",
             "product": _product()["product"], "suppliers": obs})
        rid = self._submit(
            client, jwks_env, core_rbac, [self._sup()]
        ).json()["data"]["requestId"]
        draft = prc_service_repo["repo"]._drafts[rid]
        draft["technical_data"]["suppliers"].append(
            dict(draft["technical_data"]["suppliers"][0])
        )
        v = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        r = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": v, "officialCode": "001234"})
        assert r.status_code == 409


# --- D12 — supplierLinkChanges + verificação seletiva + edit-context -----------


def test_d12_link_ops_validation():
    from engineering_app.domain.product_registration import catalog
    ops, err = catalog.validate_supplier_link_changes([
        {"operation": "update",
         "key": {"supplierCode": "000089", "store": "01"},
         "fields": {"partNumber": "PN-2"}, "reason": "correção"},
        {"operation": "add",
         "key": {"supplierCode": "001572", "store": "01"},
         "fields": {"partNumber": "PN-1572", "catalogNumber": "CAT-1"},
         "reason": "nova fonte"},
    ])
    assert err is None and len(ops) == 2
    _, err = catalog.validate_supplier_link_changes(
        [{"operation": "remove",
          "key": {"supplierCode": "1", "store": "01"},
          "fields": {"partNumber": "x"}, "reason": "r"}])
    assert err is not None
    _, err = catalog.validate_supplier_link_changes(
        [{"operation": "update",
          "key": {"supplierCode": "1", "store": "01"},
          "fields": {"partNumber": "x"}, "reason": "r"},
         {"operation": "update",
          "key": {"supplierCode": "1", "store": "01"},
          "fields": {"catalogNumber": "y"}, "reason": "r"}])
    assert "duplica" in err
    _, err = catalog.validate_supplier_link_changes(
        [{"operation": "update",
          "key": {"supplierCode": "1", "store": "01"},
          "fields": {"supplierName": "x"}, "reason": "r"}])
    assert err is not None


def test_d12_compare_link_ops():
    from engineering_app.application.use_cases.product_registration.service import (
        compare_link_ops,
    )
    observed = [
        {"supplier_code": "000089", "supplier_store": "01",
         "supplier_part_number": "PN-2", "catalog_code": ""},
        {"supplier_code": "000010", "supplier_store": "01",
         "supplier_part_number": "PN-A", "catalog_code": "C1"},
    ]
    ok = compare_link_ops(
        [{"operation": "update",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"partNumber": "PN-2"}, "reason": "r"}],
        observed)
    assert ok["result"] == "matched"
    bad = compare_link_ops(
        [{"operation": "update",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"partNumber": "PN-9"}, "reason": "r"}],
        observed)
    assert bad["result"] == "mismatched"
    missing = compare_link_ops(
        [{"operation": "add",
          "key": {"supplierCode": "999999", "store": "01"},
          "fields": {"partNumber": "P"}, "reason": "r"}],
        observed)
    assert missing["result"] == "mismatched"
    incomplete = compare_link_ops(
        [{"operation": "update",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"partNumber": "PN-2"}, "reason": "r"}],
        observed, complete=False)
    assert incomplete["result"] == "unverifiable"
    # vínculos fora do change set não reprovam
    assert compare_link_ops(
        [{"operation": "update",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {"catalogNumber": ""}, "reason": "r"}],
        observed)["result"] == "matched"


def test_d13_expected_paths_sa5_only():
    """P0: UPDATE só-SA5 deve entrar no conjunto de verificação."""
    from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
        ProductRegistrationService,
    )
    svc = ProductRegistrationService(
        InMemoryProductRegistrationRepository(), official_reader=None
    )
    request = {
        "request_type": "update",
        "draft": {"changed_paths": []},
    }
    paths = svc._expected_verify_paths(
        request, {"supplierLinkChanges": [{"operation": "update"}]}
    )
    assert "suppliers" in paths
    paths = svc._expected_verify_paths(request, {})
    assert "suppliers" not in paths


def test_d13_compare_link_ops_remove():
    from engineering_app.application.use_cases.product_registration.service import (
        compare_link_ops,
    )
    observed = [
        {"supplier_code": "000089", "supplier_store": "01",
         "supplier_part_number": "PN", "catalog_code": ""},
    ]
    gone = compare_link_ops(
        [{"operation": "remove",
          "key": {"supplierCode": "000972", "store": "01"},
          "fields": {}, "reason": "desvincular"}],
        observed)
    assert gone["result"] == "matched"
    still = compare_link_ops(
        [{"operation": "remove",
          "key": {"supplierCode": "000089", "store": "01"},
          "fields": {}, "reason": "desvincular"}],
        observed)
    assert still["result"] == "mismatched"
    incomplete = compare_link_ops(
        [{"operation": "remove",
          "key": {"supplierCode": "000972", "store": "01"},
          "fields": {}, "reason": "r"}],
        observed, complete=False)
    assert incomplete["result"] == "unverifiable"


def test_d13_remove_op_validation():
    from engineering_app.domain.product_registration import catalog
    ops, err = catalog.validate_supplier_link_changes(
        [{"operation": "remove",
          "key": {"supplierCode": "000972", "store": "01"},
          "fields": {}, "reason": "desvincular fornecedor"}])
    assert err is None and ops[0]["operation"] == "remove"
    _, err = catalog.validate_supplier_link_changes(
        [{"operation": "remove",
          "key": {"supplierCode": "000972", "store": "01"},
          "fields": {"partNumber": "x"}, "reason": "r"}])
    assert err is not None


def test_d14_optional_reasons_and_field_reasons():
    from engineering_app.domain.product_registration import catalog
    # ausente e vazia são válidas
    ops, err = catalog.validate_supplier_link_changes(
        [{"operation": "update",
          "key": {"supplierCode": "000002", "store": "01"},
          "fields": {"partNumber": "P", "catalogNumber": "C"},
          "fieldReasons": {"partNumber": "Ref nova",
                           "catalogNumber": "Cat atualizado"}}])
    assert err is None
    assert ops[0]["fieldReasons"] == {
        "partNumber": "Ref nova", "catalogNumber": "Cat atualizado"}
    # 250 exato ok; 251 falha
    ops, err = catalog.validate_supplier_link_changes(
        [{"operation": "update",
          "key": {"supplierCode": "1", "store": "1"},
          "fields": {"partNumber": "x"}, "reason": "a" * 250}])
    assert err is None
    _, err = catalog.validate_supplier_link_changes(
        [{"operation": "update",
          "key": {"supplierCode": "1", "store": "1"},
          "fields": {"partNumber": "x"}, "reason": "a" * 251}])
    assert err is not None
    _, err = catalog.validate_supplier_link_changes(
        [{"operation": "update",
          "key": {"supplierCode": "1", "store": "1"},
          "fields": {"partNumber": "x"},
          "fieldReasons": {"partNumber": "b" * 251}}])
    assert err is not None


def test_d14_scalar_reason_optional():
    from engineering_app.domain.product_registration import catalog
    # sem reason → aceito
    out = catalog.validate_update_changes(
        [{"path": "accountingAccount", "proposedValue": "11401007"}])
    assert out[0]["reason"] == ""
    # 250 ok, 251 falha
    out = catalog.validate_update_changes(
        [{"path": "accountingAccount", "proposedValue": "x",
          "reason": "a" * 250}])
    assert out[0]["reason"] == "a" * 250
    import pytest as _pt
    with _pt.raises(Exception):
        catalog.validate_update_changes(
            [{"path": "accountingAccount", "proposedValue": "x",
              "reason": "a" * 251}])


def test_d14fix02_supplier_link_duplicate_and_conflict():
    """D14-FIX-02 — mesma chave SA5 não pode repetir ops nem misturar
    add/update/remove no mesmo intake."""
    from engineering_app.domain.product_registration import catalog
    key = {"supplierCode": "000002", "store": "01"}
    # dois ADD → duplicata
    _, err = catalog.validate_supplier_link_changes([
        {"operation": "add", "key": key, "fields": {"partNumber": "A"}},
        {"operation": "add", "key": key, "fields": {"partNumber": "B"}},
    ])
    assert err is not None and "duplica" in err
    # ADD + REMOVE → conflito tipado
    _, err = catalog.validate_supplier_link_changes([
        {"operation": "add", "key": key, "fields": {"partNumber": "A"}},
        {"operation": "remove", "key": key, "fields": {}, "reason": "x"},
    ])
    assert err is not None and "conflita" in err
    # UPDATE + REMOVE → conflito
    _, err = catalog.validate_supplier_link_changes([
        {"operation": "update", "key": key, "fields": {"partNumber": "A"}},
        {"operation": "remove", "key": key, "fields": {}},
    ])
    assert err is not None and "conflita" in err
    # dois REMOVE → duplicata
    _, err = catalog.validate_supplier_link_changes([
        {"operation": "remove", "key": key, "fields": {}},
        {"operation": "remove", "key": key, "fields": {}},
    ])
    assert err is not None
    # chaves distintas → ok
    ops, err = catalog.validate_supplier_link_changes([
        {"operation": "update", "key": key, "fields": {"partNumber": "A"}},
        {"operation": "add",
         "key": {"supplierCode": "000089", "store": "01"},
         "fields": {"partNumber": "PN-89", "catalogNumber": "C"}},
    ])
    assert err is None and len(ops) == 2


def test_d14fix_create_reasons_validation():
    from engineering_app.domain.product_registration import catalog
    keys = {("000001", "01"), ("000002", "02")}
    # ausente/vazio → sem razão, sem erro
    out, err = catalog.validate_create_reasons(None, keys)
    assert err is None and out == {}
    out, err = catalog.validate_create_reasons(
        {"fields": {}, "supplierLinks": []}, keys)
    assert err is None and out == {}
    # campos + vínculos independentes
    out, err = catalog.validate_create_reasons(
        {"fields": {"description": "Contexto da descrição"},
         "supplierLinks": [
             {"key": {"supplierCode": "000001", "store": "01"},
              "reason": "Inclusão homologada",
              "fieldReasons": {"partNumber": "PN novo",
                               "catalogNumber": "Cat X"}},
             {"key": {"supplierCode": "000002", "store": "02"},
              "reason": "Novo fornecedor"}]},
        keys)
    assert err is None
    assert out["fields"] == {"description": "Contexto da descrição"}
    assert out["supplierLinks"][0]["reason"] == "Inclusão homologada"
    assert out["supplierLinks"][0]["fieldReasons"] == {
        "partNumber": "PN novo", "catalogNumber": "Cat X"}
    assert "fieldReasons" not in out["supplierLinks"][1]
    # razão de PN nunca vaza para Catálogo nem outro vínculo
    assert out["supplierLinks"][1]["reason"] == "Novo fornecedor"
    # 250 exato ok; 251 rejeitado
    out, err = catalog.validate_create_reasons(
        {"fields": {"description": "a" * 250}}, keys)
    assert err is None
    _, err = catalog.validate_create_reasons(
        {"fields": {"description": "a" * 251}}, keys)
    assert err is not None
    _, err = catalog.validate_create_reasons(
        {"supplierLinks": [
            {"key": {"supplierCode": "000001", "store": "01"},
             "fieldReasons": {"partNumber": "b" * 251}}]},
        keys)
    assert err is not None
    # path desconhecido / suppliers / officialProductCode → 422
    _, err = catalog.validate_create_reasons(
        {"fields": {"campo_inventado": "x"}}, keys)
    assert err is not None
    _, err = catalog.validate_create_reasons(
        {"fields": {"suppliers": "x"}}, keys)
    assert err is not None
    # vínculo fora do payload → 422 (sem razão fantasma)
    _, err = catalog.validate_create_reasons(
        {"supplierLinks": [
            {"key": {"supplierCode": "999999", "store": "99"},
             "reason": "r"}]},
        keys)
    assert err is not None
    # atributo não editável → 422
    _, err = catalog.validate_create_reasons(
        {"supplierLinks": [
            {"key": {"supplierCode": "000001", "store": "01"},
             "fieldReasons": {"supplierName": "r"}}]},
        keys)
    assert err is not None


def test_d14fix_create_intake_persists_reasons(
    client, jwks_env, core_rbac, prc_service_repo
):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id="user-1"))
    body = _create_body(
        reasons={
            "fields": {"description": "Porque o material mudou"},
            "supplierLinks": [
                {"key": {"supplierCode": "000001", "store": "01"},
                 "reason": "Vínculo principal",
                 "fieldReasons": {"partNumber": "PN informado"}}],
        })
    resp = _post(
        client, "/v1/product-registration/intake/requests",
        _token(jwks_env), json=body, headers={"Idempotency-Key": "k-r1"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    detail = _get(
        client, f"/v1/product-registration/requests/{rid}",
        _token(jwks_env))
    assert detail.status_code == 200
    stored = detail.json()["data"]["requestedChanges"]
    assert stored["reasons"]["fields"]["description"] == \
        "Porque o material mudou"
    link = stored["reasons"]["supplierLinks"][0]
    assert link["reason"] == "Vínculo principal"
    assert link["fieldReasons"] == {"partNumber": "PN informado"}
    # razões não poluem o snapshot técnico do draft
    draft = detail.json()["data"]["technicalDraft"] or {}
    assert "reasons" not in draft


def test_d14fix_create_intake_reason_251_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id="user-1"))
    body = _create_body(reasons={"fields": {"description": "a" * 251}})
    resp = _post(
        client, "/v1/product-registration/intake/requests",
        _token(jwks_env), json=body, headers={"Idempotency-Key": "k-r2"},
    )
    assert resp.status_code == 422, resp.text
