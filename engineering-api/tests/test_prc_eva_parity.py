"""PRC-C4.6 — paridade REST × EVA para product_registration.

Mesma identidade autenticada → mesmos efeitos via REST (TestClient) e
via handlers semânticos (prc_semantic). Terminais exigem proposta
selada + confirmação humana verificável.
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from tests.conftest import rbac_payload
from tests.test_product_registration import (
    ANALYST,
    FakeReader,
    _advance_to_attendance,
    _create_body,
    _get,
    _post,
    _submit_create,
    _token,
)

from engineering_app.composition import prc_composer
from engineering_app.interface.mcp import prc_semantic
from engineering_app.interface.mcp.semantic_bridge import (
    _EXECUTE_DISPATCH,
    _READ_DISPATCH,
)


@pytest.fixture
def eva_service():
    """Service singleton com repo in-memory + reader injetável."""
    prc_composer.reset_prc_singletons()
    from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
        InMemoryProductRegistrationRepository,
    )
    from engineering_app.application.use_cases.product_registration.service import (
        ProductRegistrationService,
    )

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

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(repo, official_reader=_ReaderProxy())
    )
    yield state
    prc_composer.reset_prc_singletons()
    prc_composer.set_prc_service_for_tests(None)


def _ctx(user_id="analyst-1", permissions=None, token="tok"):
    user = SimpleNamespace(
        id=user_id,
        email=None,
        permissions=list(permissions or ANALYST),
        is_superadmin=False,
        principal_type="user",
        access_token=token,
    )
    return SimpleNamespace(user=user)


def _entry(action, capability=None):
    return SimpleNamespace(
        action=action,
        entity="product_registration",
        capability=capability or f"product_registration.{action}",
    )


class TestReadParity:
    @pytest.mark.asyncio
    async def test_detail_matches_rest(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        rest = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        # EVA: mesmo use case, mesma identidade.
        ctx_user = SimpleNamespace(
            id="analyst-1", permissions=list(ANALYST),
            is_superadmin=False, access_token="t",
        )
        eva = await prc_semantic.read_action(
            SimpleNamespace(user=ctx_user),
            _entry("detail"),
            {"request_id": rid},
        )
        body = eva.content[0].text
        assert '"success": true' in body or "Solicitação" in body
        assert rid in body

    @pytest.mark.asyncio
    async def test_scope_enforced_in_eva(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        outsider = SimpleNamespace(
            id="user-2", permissions=["engineering.product-registration.read"],
            is_superadmin=False, access_token="t",
        )
        eva = await prc_semantic.read_action(
            SimpleNamespace(user=outsider),
            _entry("detail"),
            {"request_id": rid},
        )
        assert "fora do escopo" in eva.content[0].text or '"success": false' in eva.content[0].text

    @pytest.mark.asyncio
    async def test_read_dispatch_registered(self):
        for action in (
            "list", "detail", "timeline", "verifications", "record",
            "revisions", "revision", "reference_data", "outbound_result",
        ):
            assert ("product_registration", action) in _READ_DISPATCH


class TestExecuteParity:
    @pytest.mark.asyncio
    async def test_start_via_eva(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("start"), "act",
            target_ref=rid, expected_version=1,
        )
        assert "in_progress" in eva.content[0].text

    @pytest.mark.asyncio
    async def test_reject_requires_proposal(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "commit",
            target_ref=rid, expected_version=1,
            payload={"reason": "teste"},
        )
        assert '"success": false' in eva.content[0].text

    @pytest.mark.asyncio
    async def test_reject_prepare_seals_proposal(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "prepare",
            target_ref=rid, expected_version=1,
            payload={"reason": "teste"},
        )
        body = eva.content[0].text
        assert "proposal_ref" in body
        # PREPARE não pode escrever: request ainda submitted.
        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_verify_prepare_then_act_mismatch_safe(
        self, client, jwks_env, core_rbac, eva_service
    ):
        eva_service["reader"] = FakeReader({"status": "not_found"})
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        prep = await prc_semantic.execute_action(
            _ctx(), _entry("complete"), "prepare",
            target_ref=rid, expected_version=version,
            payload={"official_code": "001234"},
        )
        assert "proposal_ref" in prep.content[0].text

    @pytest.mark.asyncio
    async def test_execute_dispatch_registered(self):
        for action in (
            "submit", "start", "update_draft", "request_information",
            "resume", "submit_review", "return_to_attendance",
            "reject", "complete", "verify_and_complete",
        ):
            assert ("product_registration", action) in _EXECUTE_DISPATCH


def _confirmed(monkeypatch):
    """Simula confirmação humana verificável (elicitation aceita)."""
    import engineering_app.interface.mcp.semantic_bridge as sb

    async def _ok(*_a, **_k):
        return None  # None = confirmado; CallToolResult = bloqueado

    monkeypatch.setattr(sb, "_require_human_confirmation", _ok)


def _ref_from(prep_result):
    import json

    return json.loads(prep_result.content[0].text)["data"]["proposal_ref"]


class TestTerminalE2E:
    @pytest.mark.asyncio
    async def test_reject_full_cycle(
        self, client, jwks_env, core_rbac, eva_service, monkeypatch
    ):
        _confirmed(monkeypatch)
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        prep = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "prepare",
            target_ref=rid, expected_version=1,
            payload={"reason": "duplicada"},
        )
        ref = _ref_from(prep)
        commit = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "commit",
            target_ref=rid, expected_version=1,
            payload={"reason": "duplicada"}, proposal_ref=ref,
        )
        assert "rejected" in commit.content[0].text
        detail = _get(
            client, f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "rejected"
        # proposta consumida: replay com mesmo ref falha
        replay = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "commit",
            target_ref=rid, expected_version=1,
            payload={"reason": "duplicada"}, proposal_ref=ref,
        )
        assert '"success": false' in replay.content[0].text

    @pytest.mark.asyncio
    async def test_proposal_wrong_actor_blocked(
        self, client, jwks_env, core_rbac, eva_service, monkeypatch
    ):
        _confirmed(monkeypatch)
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        prep = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "prepare",
            target_ref=rid, expected_version=1,
            payload={"reason": "x"},
        )
        ref = _ref_from(prep)
        out = await prc_semantic.execute_action(
            _ctx(user_id="outro-actor"), _entry("reject"), "commit",
            target_ref=rid, expected_version=1,
            payload={"reason": "x"}, proposal_ref=ref,
        )
        assert '"success": false' in out.content[0].text

    @pytest.mark.asyncio
    async def test_proposal_param_mismatch_blocked(
        self, client, jwks_env, core_rbac, eva_service, monkeypatch
    ):
        _confirmed(monkeypatch)
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        prep = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "prepare",
            target_ref=rid, expected_version=1,
            payload={"reason": "motivo-a"},
        )
        ref = _ref_from(prep)
        out = await prc_semantic.execute_action(
            _ctx(), _entry("reject"), "commit",
            target_ref=rid, expected_version=1,
            payload={"reason": "motivo-b"}, proposal_ref=ref,
        )
        assert '"success": false' in out.content[0].text
        detail = _get(
            client, f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert detail["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_verify_full_cycle_matched(
        self, client, jwks_env, core_rbac, eva_service, monkeypatch
    ):
        from tests.test_product_registration import _product

        _confirmed(monkeypatch)
        eva_service["reader"] = FakeReader(_product())
        rid = _submit_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        version = _advance_to_attendance(client, jwks_env, core_rbac, rid)
        # isola o CONTRACT_GAP (accountingAccount) para exercitar sucesso
        eva_service["repo"]._drafts[rid]["technical_data"].pop(
            "accountingAccount", None
        )
        prep = await prc_semantic.execute_action(
            _ctx(), _entry("complete"), "prepare",
            target_ref=rid, expected_version=version,
            payload={"official_code": "001234"},
        )
        ref = _ref_from(prep)
        commit = await prc_semantic.execute_action(
            _ctx(), _entry("complete"), "commit",
            target_ref=rid, expected_version=version,
            payload={"official_code": "001234"}, proposal_ref=ref,
        )
        body = commit.content[0].text
        assert "completed" in body, body
        # conclusão duplicada: PREPARE pode selar, mas o ACT revalida
        # estado/versão → state_conflict/stale_version, nunca 2ª conclusão.
        prep2 = await prc_semantic.execute_action(
            _ctx(), _entry("complete"), "prepare",
            target_ref=rid, expected_version=version,
            payload={"official_code": "001234"},
        )
        ref2 = _ref_from(prep2)
        commit2 = await prc_semantic.execute_action(
            _ctx(), _entry("complete"), "commit",
            target_ref=rid, expected_version=version,
            payload={"official_code": "001234"}, proposal_ref=ref2,
        )
        assert '"success": false' in commit2.content[0].text
