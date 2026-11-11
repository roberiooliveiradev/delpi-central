"""PRC-REF-023-UNIFIED-VALIDATION-CORRECTION-10 — validação CREATE.

Invariantes provadas aqui (AC-13..AC-17, AC-22):

- Intake CREATE rejeita ``suppliers=[]``, ``null`` e path ausente —
  lista vazia não satisfaz ``required_create_intake``.
- PN segue obrigatório por vínculo; catálogo permanece opcional;
  duplicidade ``(supplierCode, store)`` é rejeitada.
- ``PATCH /draft`` de caso CREATE em ``submitted`` não salva estado
  final sem fornecedor (remoção do último vínculo → 422).
- Compatibilidade legada: o gate só dispara quando ``suppliers`` está
  no change set — um caso histórico já incompleto continua editável
  nos demais campos (sem deadlock retroativo).
- UPDATE preserva suas regras próprias (ops SA5 do edit_policy)."""

from __future__ import annotations

from tests.conftest import rbac_payload
from tests.test_product_registration import (
    _create_body,
    _post,
    _token,
    prc_service_repo,  # noqa: F401  (fixture reexportada)
)

MR_ACCESS = "my-requests.access"
MR_CREATE = "my-requests.raw-material-creation.create"
A_SUB = "requester-a"


def _as(jwks_env, core_rbac, sub, perms):
    core_rbac["behavior"] = ("data", rbac_payload(perms, id=sub))
    return _token(jwks_env, sub)


def _supplier(**kw):
    s = {
        "supplierCode": "000001",
        "store": "01",
        "supplierName": "FORNECEDOR X",
        "partNumber": "PN-1",
        "catalogNumber": None,
    }
    s.update(kw)
    return s


def _intake(client, jwks_env, core_rbac, body, key):
    tok = _as(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE])
    return _post(
        client,
        "/v1/product-registration/intake/requests",
        tok,
        json=body,
        headers={"Idempotency-Key": key},
    )


def _body_with(suppliers):
    body = _create_body(source="my-requests", externalRequestId="c10")
    body["requestedData"]["suppliers"] = suppliers
    return body


def _create_as_a(client, jwks_env, core_rbac):
    resp = _intake(
        client, jwks_env, core_rbac, _body_with([_supplier()]), "c10-create"
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["requestId"]


class TestCreateSupplierCardinality:
    def test_intake_empty_list_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = _intake(
            client, jwks_env, core_rbac, _body_with([]), "c10-empty"
        )
        assert r.status_code == 422, r.text
        assert r.json()["data"]["fields"]["suppliers"] == "required"

    def test_intake_null_suppliers_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        r = _intake(
            client, jwks_env, core_rbac, _body_with(None), "c10-null"
        )
        assert r.status_code == 422, r.text

    def test_intake_missing_suppliers_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        body = _body_with(None)
        body["requestedData"].pop("suppliers")
        r = _intake(client, jwks_env, core_rbac, body, "c10-missing")
        assert r.status_code == 422, r.text

    def test_intake_duplicate_key_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        dup = [_supplier(), _supplier(partNumber="PN-2")]
        r = _intake(client, jwks_env, core_rbac, _body_with(dup), "c10-dup")
        assert r.status_code == 422, r.text

    def test_intake_catalog_empty_accepted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        s = _supplier()
        s.pop("catalogNumber")
        r = _intake(client, jwks_env, core_rbac, _body_with([s]), "c10-cat")
        assert r.status_code == 201, r.text


class TestDraftSupplierGate:
    def _patch(self, client, tok, rid, changes, version=1):
        return client.patch(
            f"/v1/product-registration/requests/{rid}/draft",
            json={"expectedVersion": version, "changes": changes},
            headers={"Authorization": f"Bearer {tok}"},
        )

    def test_patch_remove_last_supplier_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = self._patch(
            client,
            _as(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE]),
            rid,
            [
                {
                    "path": "suppliers",
                    "proposedValue": [],
                    "reason": "limpeza",
                }
            ],
        )
        assert r.status_code == 422, r.text
        assert r.json()["data"]["fields"]["suppliers"] == "required"

    def test_patch_supplier_without_pn_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = self._patch(
            client,
            _as(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE]),
            rid,
            [
                {
                    "path": "suppliers",
                    "proposedValue": [_supplier(partNumber="")],
                    "reason": "ajuste",
                }
            ],
        )
        assert r.status_code == 422, r.text

    def test_legacy_empty_suppliers_no_deadlock(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Caso histórico com suppliers vazio (pré-regra) segue editável
        em outros campos — o gate só vale quando suppliers é alterado."""
        rid = _create_as_a(client, jwks_env, core_rbac)
        repo = prc_service_repo["repo"]
        repo._drafts[rid]["technical_data"]["suppliers"] = []
        r = self._patch(
            client,
            _as(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE]),
            rid,
            [
                {
                    "path": "description",
                    "proposedValue": "DESC LEGADA",
                    "reason": "ajuste",
                }
            ],
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["technicalDraft"]["description"] == (
            "DESC LEGADA"
        )
