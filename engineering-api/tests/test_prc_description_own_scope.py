"""PRC-DESCRIPTION-REQUIRED + MY-REQUESTS-OWNERSHIP-ISOLATION.

RQ-01 — ``description`` é obrigatória no CREATE e não pode ser zerada
em nenhum caminho de escrita (draft, update changes, correções).
``customerReference`` segue admitindo string vazia (gate de owner —
``allow_blank`` no spec), sem endurecimento acidental dos demais
campos ``text``.

RQ-02 — ``scope=mine`` aplica predicado estrito de criador antes de
COUNT/LIMIT, sem exceção para analistas; o detalhe no contexto
pessoal responde not_found para caso alheio (anti-enumeração), e a
fila autorizada permanece intacta para o atendimento.
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from engineering_app.domain.product_registration import catalog
from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)
from tests.conftest import rbac_payload
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    _create_body,
    _get,
    _post,
    _submit_create,
    _token,
    prc_service_repo,
)

MR_REQUESTER = [
    "my-requests.access",
    "my-requests.raw-material-creation.create",
]

_BASE = "/v1/product-registration/requests"


def _fields(resp) -> dict:
    return resp.json()["data"].get("fields") or {}


def _as(jwks_env, core_rbac, perms, sub):
    core_rbac["behavior"] = ("data", rbac_payload(perms, id=sub))
    return _token(jwks_env, sub)


def _mr_create(client, jwks_env, core_rbac, sub, key):
    tok = _as(jwks_env, core_rbac, MR_REQUESTER, sub)
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        tok,
        json=_create_body(source="my-requests"),
        headers={"Idempotency-Key": key},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]["requestId"], tok


# ---------------------------------------------------------------------------
# RQ-01 — domínio: descrição obrigatória
# ---------------------------------------------------------------------------


def _valid_payload(**over):
    data = {
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
    }
    data.update(over)
    return data


class TestCreatePayloadDescription:
    def test_valid(self):
        out = catalog.validate_create_payload(_valid_payload())
        assert out["description"] == "MATERIAL TESTE"
        assert out["customerReference"] == ""

    @pytest.mark.parametrize(
        "value", [None, "", "   ", "\t\n ", " \u00a0 ".replace("\u00a0", " ")]
    )
    def test_blank_rejected(self, value):
        payload = _valid_payload(description=value)
        if value is None:
            del payload["description"]
        with pytest.raises(PrcValidationError) as exc:
            catalog.validate_create_payload(payload)
        assert exc.value.fields["description"] == "required"

    def test_whitespace_normalized(self):
        out = catalog.validate_create_payload(
            _valid_payload(description="  TERMO  ENCOLHIVEL ")
        )
        assert out["description"] == "TERMO ENCOLHIVEL"

    def test_max_length(self):
        with pytest.raises(PrcValidationError):
            catalog.validate_create_payload(
                _valid_payload(description="X" * 201)
            )

    def test_customer_reference_blank_preserved(self):
        out = catalog.validate_create_payload(
            _valid_payload(customerReference="   ")
        )
        assert out["customerReference"] == ""

    def test_customer_reference_absent_accepted(self):
        """Opcional: campo ausente no intake não falha — antes era
        ``required`` (obrigatório artificial; B1_REFEREN é opcional)."""
        payload = _valid_payload()
        del payload["customerReference"]
        out = catalog.validate_create_payload(payload)
        assert "customerReference" not in out

    def test_required_fields_still_enforced(self):
        """Sibling negativo: campos required continuam bloqueando."""
        payload = _valid_payload()
        del payload["description"]
        del payload["unit"]
        with pytest.raises(PrcValidationError) as exc:
            catalog.validate_create_payload(payload)
        assert exc.value.fields["description"] == "required"
        assert exc.value.fields["unit"] == "required"


class TestDraftChangeDescription:
    def test_blank_rejected(self):
        for value in ("", "   ", "\t\n"):
            with pytest.raises(PrcValidationError) as exc:
                catalog.validate_draft_change("description", value)
            assert exc.value.fields["description"] == "required"

    def test_none_rejected(self):
        with pytest.raises(PrcValidationError):
            catalog.validate_draft_change("description", None)

    def test_valid_value(self):
        path, value = catalog.validate_draft_change(
            "description", "NOVA DESC"
        )
        assert (path, value) == ("description", "NOVA DESC")

    def test_customer_reference_blank_allowed(self):
        path, value = catalog.validate_draft_change(
            "customerReference", ""
        )
        assert (path, value) == ("customerReference", "")

    def test_customer_reference_none_allowed(self):
        """Opcional: remoção explícita (None) limpa o campo — antes
        rejeitada como 'campo obrigatório não pode ser removido'."""
        path, value = catalog.validate_draft_change(
            "customerReference", None
        )
        assert (path, value) == ("customerReference", "")

    def test_update_changes_blank_description(self):
        with pytest.raises(PrcValidationError) as exc:
            catalog.validate_update_changes(
                [
                    {
                        "path": "description",
                        "proposedValue": "   ",
                        "reason": "z",
                    }
                ]
            )
        assert "description" in exc.value.fields

    def test_update_changes_other_field_only(self):
        changes = catalog.validate_update_changes(
            [{"path": "unit", "proposedValue": "PC", "reason": "ok"}]
        )
        assert changes[0]["path"] == "unit"


# ---------------------------------------------------------------------------
# RQ-01 — REST: intake, draft e update
# ---------------------------------------------------------------------------


class TestDescriptionRest:
    def test_create_blank_description_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        body = _create_body()
        body["requestedData"]["description"] = "   "
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=body,
        )
        assert resp.status_code == 422
        assert _fields(resp).get("description") == "required"
        assert not prc_service_repo["repo"].list_requests(page=1).get(
            "items"
        )

    def test_create_missing_description_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        body = _create_body()
        del body["requestedData"]["description"]
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=body,
        )
        assert resp.status_code == 422
        assert _fields(resp).get("description") == "required"

    def test_create_blank_customer_reference_ok(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        resp = _submit_create(client, jwks_env, core_rbac)
        assert resp.status_code in (200, 201), resp.text

    def test_update_intake_blank_description_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        body = _create_body(
            requestType="update",
            requestedData=None,
            officialProductCode="P0001",
            changes=[
                {"path": "description", "proposedValue": "", "reason": "r"}
            ],
        )
        body.pop("requestedData", None)
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env),
            json=body,
        )
        assert resp.status_code == 422

    def test_draft_blank_description_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        detail = _get(client, f"{_BASE}/{rid}", _token(jwks_env)).json()[
            "data"
        ]
        resp = client.patch(
            f"{_BASE}/{rid}/draft",
            headers={"Authorization": f"Bearer {_token(jwks_env)}"},
            json={
                "expectedVersion": detail["caseVersion"],
                "changes": [
                    {
                        "path": "description",
                        "proposedValue": "  ",
                        "reason": "x",
                    }
                ],
            },
        )
        assert resp.status_code == 422
        # Estado preservado — descrição anterior intacta.
        after = _get(client, f"{_BASE}/{rid}", _token(jwks_env)).json()[
            "data"
        ]
        assert after["technicalDraft"]["description"] == "MATERIAL TESTE"


# ---------------------------------------------------------------------------
# RQ-02 — escopo pessoal: listagem e detalhe
# ---------------------------------------------------------------------------


class TestMineScope:
    def test_analyst_mine_returns_only_own(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # Usuário D: solicitante + analista (engineering.access).
        d_tok = _as(jwks_env, core_rbac, ANALYST, "user-d")
        rid_d = _submit_create(
            client, jwks_env, core_rbac, sub="user-d"
        ).json()["data"]["requestId"]
        # Usuário B: solicitante comum.
        rid_b, _ = _mr_create(
            client, jwks_env, core_rbac, "user-b", "k-b-1"
        )
        # O mock de RBAC é global — repõe o principal de D.
        d_tok = _as(jwks_env, core_rbac, ANALYST, "user-d")
        # mine → somente o próprio caso, sem exceção de analista.
        mine = _get(
            client, f"{_BASE}?scope=mine&pageSize=100", d_tok
        ).json()["data"]
        ids = {i["id"] for i in mine["items"]}
        assert ids == {rid_d}
        assert mine["total"] == 1
        # fila autorizada → comportamento vigente (analista vê os dois).
        queue = _get(client, f"{_BASE}?pageSize=100", d_tok).json()["data"]
        qids = {i["id"] for i in queue["items"]}
        assert {rid_d, rid_b} <= qids

    def test_requester_mine_isolated(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid_a, tok_a = _mr_create(
            client, jwks_env, core_rbac, "user-a", "k-a-1"
        )
        rid_b, _ = _mr_create(
            client, jwks_env, core_rbac, "user-b", "k-b-1"
        )
        tok_a = _as(jwks_env, core_rbac, MR_REQUESTER, "user-a")
        mine = _get(
            client, f"{_BASE}?scope=mine&pageSize=100", tok_a
        ).json()["data"]
        ids = {i["id"] for i in mine["items"]}
        assert ids == {rid_a}
        assert rid_b not in ids

    def test_mine_filters_do_not_widen(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _mr_create(client, jwks_env, core_rbac, "user-a", "k-a-1")
        rid_b, _ = _mr_create(
            client, jwks_env, core_rbac, "user-b", "k-b-1"
        )
        d_tok = _as(jwks_env, core_rbac, ANALYST, "user-d")
        # Filtro por status não amplia o escopo pessoal.
        mine = _get(
            client,
            f"{_BASE}?scope=mine&status=submitted&pageSize=100",
            d_tok,
        ).json()["data"]
        assert mine["items"] == []
        assert rid_b

    def test_detail_mine_forbidden_for_foreign_case(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid_b, _ = _mr_create(
            client, jwks_env, core_rbac, "user-b", "k-b-1"
        )
        d_tok = _as(jwks_env, core_rbac, ANALYST, "user-d")
        # Contexto pessoal: caso alheio → not_found (anti-enumeração).
        resp = _get(client, f"{_BASE}/{rid_b}?scope=mine", d_tok)
        assert resp.status_code == 404
        # Contexto operacional autorizado permanece: analista abre.
        resp = _get(client, f"{_BASE}/{rid_b}", d_tok)
        assert resp.status_code == 200

    def test_detail_mine_owner_ok(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid_a, tok_a = _mr_create(
            client, jwks_env, core_rbac, "user-a", "k-a-1"
        )
        resp = _get(client, f"{_BASE}/{rid_a}?scope=mine", tok_a)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# RQ-07 — EVA: mesmo use case, scope=mine
# ---------------------------------------------------------------------------


class TestEvaMineScope:
    @pytest.mark.asyncio
    async def test_list_scope_mine(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        from engineering_app.interface.mcp import prc_semantic

        rid_d = _submit_create(
            client, jwks_env, core_rbac, sub="user-d"
        ).json()["data"]["requestId"]
        _mr_create(client, jwks_env, core_rbac, "user-b", "k-b-1")
        _as(jwks_env, core_rbac, ANALYST, "user-d")
        ctx = SimpleNamespace(
            user=SimpleNamespace(
                id="user-d",
                email=None,
                permissions=list(ANALYST),
                is_superadmin=False,
                principal_type="user",
                access_token="t",
            )
        )
        entry = SimpleNamespace(
            action="list",
            entity="product_registration",
            capability="product_registration.list",
        )
        eva = await prc_semantic.read_action(
            ctx, entry, {"scope": "mine", "page_size": 100}
        )
        body = eva.content[0].text
        assert rid_d in body
        assert '"total": 1' in body

    @pytest.mark.asyncio
    async def test_submit_blank_description_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        from engineering_app.interface.mcp import prc_semantic

        ctx = SimpleNamespace(
            user=SimpleNamespace(
                id="user-d",
                email=None,
                permissions=list(ANALYST),
                is_superadmin=False,
                principal_type="user",
                access_token="t",
            )
        )
        entry = SimpleNamespace(
            action="submit",
            entity="product_registration",
            capability="product_registration.submit",
        )
        payload = _create_body()
        payload["requestedData"]["description"] = ""
        eva = await prc_semantic.execute_action(
            ctx, entry, "act", payload=payload
        )
        body = eva.content[0].text
        assert '"success": false' in body or "required" in body
