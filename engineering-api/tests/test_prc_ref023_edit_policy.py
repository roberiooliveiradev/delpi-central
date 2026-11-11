"""PRC-REF-023-EDIT-POLICY-FIX-08 — governança de edição por estado.

Matriz definitiva (backend-first — a UI nunca decide):

- ``submitted``: o criador edita a ficha e anexa documentos
  (mesmo requestId, CAS + idempotência).
- ``in_progress``: ficha e documentos somente leitura — para o
  solicitante E para a Engenharia (edição genérica bloqueada).
- ``needs_correction``: somente os alvos devolvidos; upload exige
  alvo documental que o contrato ainda não modela → bloqueado.
- terminais: nenhuma escrita.

Identidades: A=criador, B=terceiro, C=analista Engenharia."""

from __future__ import annotations

import io

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (
    ANALYST,
    _create_body,
    _post,
    _token,
    prc_service_repo,
)

ENG_ACCESS = "engineering.access"
MR_CREATE = "my-requests.raw-material-creation.create"
MR_ACCESS = "my-requests.access"

A_SUB = "requester-a"
B_SUB = "third-party-b"
C_SUB = "analyst-c"

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def _base(rid: str) -> str:
    return f"/v1/product-registration/requests/{rid}"


def _as(jwks_env, core_rbac, sub, perms):
    core_rbac["behavior"] = ("data", rbac_payload(perms, id=sub))
    return _token(jwks_env, sub)


def _create_as_a(client, jwks_env, core_rbac):
    """A cria via intake de Minhas Solicitações (sem engineering.access)."""
    tok = _as(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE])
    body = _create_body(
        source="my-requests", externalRequestId="fix08-a"
    )
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        tok,
        json=body,
        headers={"Idempotency-Key": "fix08-create"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["requestId"]


def _patch_draft(client, tok, rid, version, value="EDIT"):
    return client.patch(
        f"{_base(rid)}/draft",
        json={
            "expectedVersion": version,
            "changes": [
                {"path": "description",
                 "proposedValue": value, "reason": "ajuste"},
            ],
        },
        headers={"Authorization": f"Bearer {tok}"},
    )


def _upload(client, tok, rid):
    return client.post(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok}"},
        files={"file": ("doc.pdf", io.BytesIO(PDF), "application/pdf")},
    )


# O stub `core_rbac` resolve a identidade pelo payload corrente — por
# isso toda troca de ator exige re-armar antes da requisição.
def _rearm(jwks_env, core_rbac, sub, perms):
    return _as(jwks_env, core_rbac, sub, perms)


def _a(jwks_env, core_rbac):
    return _rearm(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE])


def _b(jwks_env, core_rbac):
    return _rearm(jwks_env, core_rbac, B_SUB, [MR_ACCESS, MR_CREATE])


def _c(jwks_env, core_rbac):
    return _rearm(jwks_env, core_rbac, C_SUB, ANALYST)


def _start_as_c(client, jwks_env, core_rbac, rid, version=1):
    tok = _as(jwks_env, core_rbac, C_SUB, ANALYST)
    r = _post(
        client, f"{_base(rid)}/actions/start", tok,
        json={"expectedVersion": version},
    )
    assert r.status_code == 200, r.text


class TestSubmittedFreeEdit:
    """Cenários 1–3 — criador edita e anexa enquanto submitted."""

    def test_creator_edits_sheet_in_submitted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = _patch_draft(client, _a(jwks_env, core_rbac), rid, 1, "DESC REVISADA")
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["technicalDraft"]["description"] == "DESC REVISADA"
        assert d["status"] == "submitted"
        assert d["id"] == rid  # mesmo requestId, sem novo chamado

    def test_creator_edits_suppliers_in_submitted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = client.patch(
            f"{_base(rid)}/draft",
            json={
                "expectedVersion": 1,
                "changes": [
                    {
                        "path": "suppliers",
                        "proposedValue": [
                            {
                                "supplierCode": "000777",
                                "store": "02",
                                "supplierName": "FORNECEDOR NOVO",
                                "partNumber": "PN-NEW",
                                "catalogNumber": "CAT-1",
                            }
                        ],
                        "reason": "troca de fornecedor",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"},
        )
        assert r.status_code == 200, r.text
        sup = r.json()["data"]["technicalDraft"]["suppliers"]
        assert sup[0]["supplierCode"] == "000777"
        assert sup[0]["partNumber"] == "PN-NEW"

    def test_creator_uploads_in_submitted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        assert _upload(client, _a(jwks_env, core_rbac), rid).status_code == 201

    def test_allowed_actions_offer_edit_draft_in_submitted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = client.get(
            _base(rid), headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"}
        )
        assert "edit_draft" in r.json()["data"]["allowedActions"]


class TestThirdPartyDenied:
    """Cenários 4–5 — terceiro não edita nem anexa no caso de A."""

    def test_third_party_cannot_edit(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        tok_b = _as(jwks_env, core_rbac, B_SUB, [MR_ACCESS, MR_CREATE])
        r = _patch_draft(client, tok_b, rid, 1, "HIJACK")
        assert r.status_code == 403, r.text

    def test_third_party_cannot_upload(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        tok_b = _as(jwks_env, core_rbac, B_SUB, [MR_ACCESS, MR_CREATE])
        assert _upload(client, tok_b, rid).status_code == 403

    def test_analyst_cannot_edit_foreign_case_in_submitted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """engineering.access não é passe de edição — só o criador."""
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = _patch_draft(client, _c(jwks_env, core_rbac), rid, 1, "HIJACK")
        assert r.status_code == 403, r.text


class TestInProgressLocked:
    """Cenários 6–9 — iniciado o atendimento, tudo vira leitura."""

    def test_start_blocks_creator_edit(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        _start_as_c(client, jwks_env, core_rbac, rid)
        r = _patch_draft(client, _a(jwks_env, core_rbac), rid, 2, "LATE")
        assert r.status_code == 409, r.text

    def test_start_blocks_creator_upload(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        _start_as_c(client, jwks_env, core_rbac, rid)
        assert _upload(client, _a(jwks_env, core_rbac), rid).status_code == 409

    def test_start_blocks_analyst_generic_edit(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """C não reescreve a ficha submetida por endpoint genérico."""
        rid = _create_as_a(client, jwks_env, core_rbac)
        _start_as_c(client, jwks_env, core_rbac, rid)
        r = _patch_draft(client, _c(jwks_env, core_rbac), rid, 2, "ANALYST REWRITE")
        assert r.status_code == 403, r.text

    def test_edit_draft_disappears_from_allowed_actions(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        _start_as_c(client, jwks_env, core_rbac, rid)
        r = client.get(
            _base(rid), headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"}
        )
        assert "edit_draft" not in r.json()["data"]["allowedActions"]

    def test_inflight_edit_after_start_fails(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Concorrência: edição lida antes do start não escreve depois —
        CAS rejeita versão/estado defasados atomicamente."""
        rid = _create_as_a(client, jwks_env, core_rbac)
        version_seen = 1  # A leu o caso ainda submitted
        _start_as_c(client, jwks_env, core_rbac, rid)
        r = _patch_draft(client, _a(jwks_env, core_rbac), rid, version_seen, "LATE")
        assert r.status_code in (403, 409), r.text


class TestCorrectionScope:
    """Cenários 10–14 — devolução só autoriza os alvos devolvidos."""

    def _returned_case(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        _start_as_c(client, jwks_env, core_rbac, rid)
        r = _post(
            client,
            f"{_base(rid)}/actions/return-for-correction",
            _c(jwks_env, core_rbac),
            json={
                "expectedVersion": 2,
                "reason": "corrigir descrição",
                "targets": [
                    {
                        "targetType": "FIELD",
                        "targetPath": "description",
                        "reason": "descrição ambígua",
                    }
                ],
            },
        )
        assert r.status_code == 200, r.text
        return rid

    def test_requester_edits_only_returned_targets(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = self._returned_case(
            client, jwks_env, core_rbac, prc_service_repo
        )
        # Endpoint de correção: somente alvos devolvidos.
        detail = client.get(
            _base(rid), headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"}
        ).json()["data"]
        r = client.patch(
            f"{_base(rid)}/returned-fields",
            json={
                "expectedVersion": detail["caseVersion"],
                "changes": [
                    {
                        "path": "unit",
                        "proposedValue": "KG",
                        "reason": "não devolvido",
                        "mode": "changed",
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {_a(jwks_env, core_rbac)}"
            },
        )
        assert r.status_code in (400, 403, 409, 422), r.text

    def test_generic_draft_patch_blocked_in_needs_correction(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Correção não é edição livre — /draft genérico segue 409."""
        rid = self._returned_case(
            client, jwks_env, core_rbac, prc_service_repo
        )
        r = _patch_draft(client, _a(jwks_env, core_rbac), rid, 3, "FREE EDIT")
        assert r.status_code == 409, r.text

    def test_upload_blocked_in_needs_correction(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """AC-08 — sem alvo documental no contrato de devolução,
        upload permanece bloqueado (dependência registrada)."""
        rid = self._returned_case(
            client, jwks_env, core_rbac, prc_service_repo
        )
        assert _upload(client, _a(jwks_env, core_rbac), rid).status_code == 409

    def test_resubmit_returns_to_locked_attendance(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = self._returned_case(
            client, jwks_env, core_rbac, prc_service_repo
        )
        detail = client.get(
            _base(rid), headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"}
        ).json()["data"]
        client.patch(
            f"{_base(rid)}/returned-fields",
            json={
                "expectedVersion": detail["caseVersion"],
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "DESC CORRIGIDA",
                        "reason": "conforme devolução",
                        "mode": "changed",
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {_a(jwks_env, core_rbac)}"
            },
        )
        detail = client.get(
            _base(rid), headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"}
        ).json()["data"]
        r = _post(
            client,
            f"{_base(rid)}/actions/resubmit-correction",
            _a(jwks_env, core_rbac),
            json={"expectedVersion": detail["caseVersion"]},
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["status"] == "in_progress"
        # Mesmo requestId — e a edição livre continua bloqueada.
        d2 = client.get(
            _base(rid), headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"}
        ).json()["data"]
        assert d2["id"] == rid
        assert "edit_draft" not in d2["allowedActions"]
        assert _upload(client, _a(jwks_env, core_rbac), rid).status_code == 409


class TestTerminalStates:
    """Cenário 17 — caso rejeitado não aceita escrita."""

    def test_rejected_case_is_read_only(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = _post(
            client, f"{_base(rid)}/actions/reject", _c(jwks_env, core_rbac),
            json={"expectedVersion": 1, "reason": "fora de escopo"},
        )
        assert r.status_code == 200, r.text
        assert _patch_draft(client, _a(jwks_env, core_rbac), rid, 2).status_code in (
            403,
            409,
        )
        assert _upload(client, _a(jwks_env, core_rbac), rid).status_code == 409


class TestIdempotencyAndVersion:
    """Versão, idempotência e histórico preservados na edição."""

    def test_stale_version_conflict(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        assert _patch_draft(client, _a(jwks_env, core_rbac), rid, 1).status_code == 200
        # Versão defasada → 409; nada é sobrescrito silenciosamente.
        assert _patch_draft(client, _a(jwks_env, core_rbac), rid, 1).status_code == 409

    def test_immutable_field_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        r = client.patch(
            f"{_base(rid)}/draft",
            json={
                "expectedVersion": 1,
                "changes": [
                    {
                        "path": "officialProductCode",
                        "proposedValue": "999999",
                        "reason": "x",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"},
        )
        assert r.status_code == 422, r.text

    def test_draft_changed_event_audited(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_as_a(client, jwks_env, core_rbac)
        _patch_draft(client, _a(jwks_env, core_rbac), rid, 1, "AUDIT TRAIL")
        events = prc_service_repo["repo"]._events[rid]
        kinds = [e["event_type"] for e in events]
        assert "draft_changed" in kinds
        ev = next(e for e in events if e["event_type"] == "draft_changed")
        assert ev["actor_subject"] == A_SUB
        assert ev["metadata"]["changes"][0]["path"] == "description"
        # Evento de criação não é reescrito.
        assert events[0]["event_type"] == "submitted"


class TestUpdateCaseSupplierDerivation:
    """FIX-08 — edição pré-atendimento em caso UPDATE: a lista alvo de
    fornecedores é convertida pelo backend em ``supplierLinkChanges``
    derivados do baseline oficial (verify compara ops, nunca lista)."""

    _counter = [0]

    def _update_as_a(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        from tests.test_product_registration import _attach_reader

        type(self)._counter[0] += 1
        _attach_reader(prc_service_repo)
        tok = _as(jwks_env, core_rbac, A_SUB, [MR_ACCESS, MR_CREATE])
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            tok,
            json={
                "source": "my-requests",
                "requestType": "update",
                "productType": "raw_material",
                "schemaVersion": 1,
                "officialProductCode": "001234",
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "DESC V2",
                        "reason": "ajuste",
                    }
                ],
            },
            headers={"Idempotency-Key": f"fix08-update-{type(self)._counter[0]}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["data"]["requestId"]

    def test_suppliers_edit_derives_link_ops(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        from tests.test_product_registration import _get

        rid = self._update_as_a(
            client, jwks_env, core_rbac, prc_service_repo
        )
        r = client.patch(
            f"{_base(rid)}/draft",
            json={
                "expectedVersion": 1,
                "changes": [
                    {
                        "path": "suppliers",
                        "proposedValue": [
                            {
                                "supplierCode": "000001",
                                "store": "01",
                                "supplierName": "FORNECEDOR X",
                                "partNumber": "PN-NEW",
                                "catalogNumber": "CAT-9",
                            },
                            {
                                "supplierCode": "000777",
                                "store": "01",
                                "supplierName": "FORNECEDOR NOVO",
                                "partNumber": "PN-777",
                                "catalogNumber": None,
                            },
                        ],
                        "reason": "ajuste de vínculos",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"},
        )
        assert r.status_code == 200, r.text
        detail = _get(
            client, _base(rid), _a(jwks_env, core_rbac)
        ).json()["data"]
        ops = detail["technicalDraft"]["supplierLinkChanges"]
        by_op = {(o["operation"], o["key"]["supplierCode"]): o for o in ops}
        assert ("update", "000001") in by_op
        assert by_op[("update", "000001")]["fields"]["partNumber"] == (
            "PN-NEW"
        )
        assert ("add", "000777") in by_op
        assert {c["path"] for c in detail["changedPaths"]} >= {
            "suppliers"
        }

    def test_suppliers_edit_remove_and_pn_gate(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Remover o vínculo oficial gera REMOVE; ADD sem PN falha 422."""
        rid = self._update_as_a(
            client, jwks_env, core_rbac, prc_service_repo
        )
        r = client.patch(
            f"{_base(rid)}/draft",
            json={
                "expectedVersion": 1,
                "changes": [
                    {"path": "suppliers", "proposedValue": [],
                     "reason": "sem fornecedor"}
                ],
            },
            headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"},
        )
        assert r.status_code == 200, r.text
        ops = r.json()["data"]["technicalDraft"]["supplierLinkChanges"]
        assert ops and ops[0]["operation"] == "remove"

        rid2 = self._update_as_a(
            client, jwks_env, core_rbac, prc_service_repo
        )
        bad = client.patch(
            f"{_base(rid2)}/draft",
            json={
                "expectedVersion": 1,
                "changes": [
                    {
                        "path": "suppliers",
                        "proposedValue": [
                            {
                                "supplierCode": "000001",
                                "store": "01",
                                "supplierName": "FORNECEDOR X",
                                "partNumber": "PN-1",
                            },
                            {
                                "supplierCode": "000888",
                                "store": "01",
                                "supplierName": "SEM PN",
                                "partNumber": "",
                            },
                        ],
                        "reason": "x",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {_a(jwks_env, core_rbac)}"},
        )
        assert bad.status_code == 422, bad.text
