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


# === P2 — paridade da conversa (Issue #207) ===========================
# comment_list/comment_create/comment_update via MESMOS use cases REST:
# mesma identidade → mesmos efeitos; negações espelhadas.

from tests.test_prc_conversation import (  # noqa: E402
    ANALYST_SUB,
    OTHER_SUB,
    REQUESTER_PERMS,
    REQUESTER_SUB,
    _as,
    _base,
    _comment,
    _create,
    _post_comment_ok,
    _start,
)


def _list_rest(client, jwks_env, core_rbac, rid, sub=ANALYST_SUB):
    tok = _as(jwks_env, core_rbac, sub)
    r = client.get(f"{_base(rid)}/comments",
                   headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _ctx_req(user_id=REQUESTER_SUB):
    return _ctx(user_id=user_id, permissions=list(REQUESTER_PERMS))


class TestConversationParity:
    @pytest.mark.asyncio
    async def test_dispatch_and_tool_count(self):
        from engineering_app.application.eva.semantic_registry import (
            SEMANTIC_TOOL_NAMES,
            semantic_action,
        )
        assert len(SEMANTIC_TOOL_NAMES) == 6
        assert ("product_registration", "comment_list") in _READ_DISPATCH
        for a in ("comment_create", "comment_update"):
            assert ("product_registration", a) in _EXECUTE_DISPATCH
            assert semantic_action("product_registration", a) is not None

    @pytest.mark.asyncio
    async def test_eva_list_matches_rest(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evl")
        _post_comment_ok(client, jwks_env, core_rbac, rid, body="m1")
        _post_comment_ok(client, jwks_env, core_rbac, rid, body="m2")
        rest = _list_rest(client, jwks_env, core_rbac, rid)
        eva = await prc_semantic.read_action(
            _ctx(), _entry("comment_list"), {"request_id": rid},
        )
        body = eva.content[0].text
        assert "m1" in body and "m2" in body
        for c in rest["items"]:
            assert c["commentId"] in body
        # escopo negado espelha REST: não-analista de outro caso (403)
        outsider = SimpleNamespace(
            id=OTHER_SUB, permissions=list(REQUESTER_PERMS),
            is_superadmin=False, access_token="t",
        )
        eva_out = await prc_semantic.read_action(
            SimpleNamespace(user=outsider), _entry("comment_list"),
            {"request_id": rid},
        )
        assert '"success": false' in eva_out.content[0].text

    @pytest.mark.asyncio
    async def test_eva_create_persists_and_rest_reads_back(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evc")
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("comment_create"), "act",
            target_ref=rid,
            payload={"body": "via EVA", "authorUserId": "spoof-x"},
            idempotency_key="k-ev1",
        )
        body = eva.content[0].text
        assert '"success": true' in body
        rest = _list_rest(client, jwks_env, core_rbac, rid)
        assert rest["total"] == 1
        c = rest["items"][0]
        assert c["body"] == "via EVA"
        # autor = principal delegado, nunca payload
        assert c["authorSubject"] == "analyst-1"

    @pytest.mark.asyncio
    async def test_prepare_never_persists(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evp")
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("comment_create"), "prepare",
            target_ref=rid, payload={"body": "nao persiste"},
        )
        assert "prepare" in eva.content[0].text
        rest = _list_rest(client, jwks_env, core_rbac, rid)
        assert rest["total"] == 0

    @pytest.mark.asyncio
    async def test_idempotent_replay_single_message(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evi")
        for _ in range(2):
            await prc_semantic.execute_action(
                _ctx(), _entry("comment_create"), "act",
                target_ref=rid, payload={"body": "dup"},
                idempotency_key="k-dup",
            )
        rest = _list_rest(client, jwks_env, core_rbac, rid)
        assert rest["total"] == 1

    @pytest.mark.asyncio
    async def test_update_own_comment_and_cas_conflict(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evu")
        c = _post_comment_ok(client, jwks_env, core_rbac, rid,
                             body="original")
        ok = await prc_semantic.execute_action(
            _ctx(), _entry("comment_update"), "act",
            target_ref=rid,
            payload={"comment_id": c["commentId"], "body": "editado"},
            expected_version=c["version"],
        )
        assert '"success": true' in ok.content[0].text
        rest = _list_rest(client, jwks_env, core_rbac, rid)
        c2 = rest["items"][0]
        assert c2["body"] == "editado"
        assert c2["authorSubject"] == c["authorSubject"]  # autor preservado
        # CAS obsoleto → erro tipado, sem sobrescrita
        stale = await prc_semantic.execute_action(
            _ctx(), _entry("comment_update"), "act",
            target_ref=rid,
            payload={"comment_id": c["commentId"], "body": "x"},
            expected_version=c["version"],
        )
        assert '"success": false' in stale.content[0].text
        assert "stale_version" in stale.content[0].text

    @pytest.mark.asyncio
    async def test_update_non_author_denied(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evn")
        _start(client, jwks_env, core_rbac, rid)
        c = _post_comment_ok(client, jwks_env, core_rbac, rid,
                             body="do analista", sub=ANALYST_SUB)
        eva = await prc_semantic.execute_action(
            _ctx_req(), _entry("comment_update"), "act",
            target_ref=rid,
            payload={"comment_id": c["commentId"], "body": "hack"},
            expected_version=c["version"],
        )
        assert '"success": false' in eva.content[0].text
        assert "forbidden" in eva.content[0].text

    @pytest.mark.asyncio
    async def test_comment_idor_other_request(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid_a = _create(client, jwks_env, core_rbac, suffix="eva")
        rid_b = _create(client, jwks_env, core_rbac, suffix="evb")
        c = _post_comment_ok(client, jwks_env, core_rbac, rid_a)
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("comment_update"), "act",
            target_ref=rid_b,
            payload={"comment_id": c["commentId"], "body": "x"},
            expected_version=c["version"],
        )
        assert '"success": false' in eva.content[0].text
        assert "not_found" in eva.content[0].text

    @pytest.mark.asyncio
    async def test_frozen_terminal_blocks_create(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _create(client, jwks_env, core_rbac, suffix="evf")
        eva_service["repo"]._requests[rid]["status"] = "completed"
        eva = await prc_semantic.execute_action(
            _ctx(), _entry("comment_create"), "act",
            target_ref=rid, payload={"body": "tarde demais"},
        )
        assert '"success": false' in eva.content[0].text
        # leitura continua permitida
        ok = await prc_semantic.read_action(
            _ctx(), _entry("comment_list"), {"request_id": rid},
        )
        assert '"success": true' in ok.content[0].text


# =============================================================================
# EVA-ENGINEERING-API-PRC-FULL-SEMANTIC-PARITY-01 — paridade E2E via tools.
#
# Diferente dos testes acima (handler-level), estes passam pelo caminho
# completo: _resolve (gate status=proven) → _READ/_EXECUTE_DISPATCH →
# prc_semantic → service — exigindo contexto MCP humano autenticado.
# =============================================================================

import asyncio

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from engineering_app.interface.mcp import semantic_bridge as sem
from tests.test_prc_record_flags import _create_flag, _v1, _v2


def _eva_ctx(user_id="analyst-1", permissions=None):
    user = SimpleNamespace(
        id=user_id, email="analyst@delpi.test", name="Analyst",
        permissions=list(permissions if permissions is not None else ANALYST),
        is_superadmin=False, principal_type="user",
        access_token="eva-token",
    )
    set_current_user(user)
    set_request_authorization("Bearer eva-token")


@pytest.fixture(autouse=True)
def _clear_mcp_ctx():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


def _read(action, **kw):
    return asyncio.run(
        sem.tool_read(entity="product_registration", action=action, **kw)
    )


def _execute(action, **kw):
    return asyncio.run(
        sem.tool_execute(entity="product_registration", action=action, **kw)
    )


class TestReadParityEndToEnd:
    """RQ-02/RQ-03/RQ-04/RQ-05/RQ-06 — leituras no caminho MCP completo."""

    def test_list_matches_rest(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        rest = _get(
            client, "/v1/product-registration/requests",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        _eva_ctx()
        res = _read("list")
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["total"] == rest["total"]
        assert {i["id"] for i in data["items"]} == {
            i["id"] for i in rest["items"]
        }
        assert rid in {i["id"] for i in data["items"]}

    def test_list_view_pending_excludes_terminal(
        self, client, jwks_env, core_rbac, eva_service
    ):
        pending_rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        # Segundo caso completado até o fim → terminal, fora do pending.
        done, _ = _v2_done = __import__(
            "tests.test_prc_snapshot_versioning", fromlist=["_complete_update"]
        )._complete_update(
            client, jwks_env, core_rbac, eva_service,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
        )
        assert done.status_code == 200, done.text
        _eva_ctx()
        res = _read("list", filters={"view": "pending"})
        assert not res.is_error, res.structured_content
        items = res.structured_content["data"]["items"]
        ids = {i["id"] for i in items}
        assert pending_rid in ids
        assert len(ids) == 1
        # status explícito prevalece sobre o preset
        res2 = _read("list", filters={
            "view": "pending", "status": "completed"})
        assert not res2.is_error
        assert res2.structured_content["data"]["total"] == 1

    def test_list_pagination(
        self, client, jwks_env, core_rbac, eva_service
    ):
        _submit_create(client, jwks_env, core_rbac)
        _eva_ctx()
        res = _read("list", pagination={"page": 1, "page_size": 1})
        assert not res.is_error
        data = res.structured_content["data"]
        assert len(data["items"]) == 1
        assert data["total"] == 1

    def test_timeline_matches_rest(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        rest = _get(
            client,
            f"/v1/product-registration/requests/{rid}/timeline",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        _eva_ctx()
        res = _read("timeline", ref=rid)
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["total"] == rest["total"]
        assert {e["event_type"] for e in data["items"]} == {
            e["event_type"] for e in rest["items"]
        }

    def test_verifications_matches_rest(
        self, client, jwks_env, core_rbac, eva_service
    ):
        done, rid = __import__(
            "tests.test_prc_snapshot_versioning",
            fromlist=["_complete_update"],
        )._complete_update(
            client, jwks_env, core_rbac, eva_service,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
        )
        assert done.status_code == 200, done.text
        _eva_ctx()
        res = _read("verifications", ref=rid)
        assert not res.is_error, res.structured_content
        assert res.structured_content["success"] is True

    def test_reference_data(
        self, client, jwks_env, core_rbac, eva_service
    ):
        _eva_ctx()
        res = _read("reference_data")
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data.get("fields") or data.get("fieldCatalog")

    def test_outbound_result(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        _eva_ctx()
        res = _read("outbound_result", ref=rid)
        assert not res.is_error, res.structured_content

    def test_records_list_matches_rest(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rec = _v1(client, jwks_env, core_rbac, eva_service)
        rest = _get(
            client, "/v1/product-registration/technical-records",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        _eva_ctx()
        res = _read("records_list")
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["total"] == rest["total"]
        assert rec["id"] in {i["recordId"] for i in data["items"]}
        # filtro flagState
        res_f = _read("records_list", filters={"flagState": "open"})
        assert not res_f.is_error, res_f.structured_content

    def test_record_revisions_compare(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rec = _v1(client, jwks_env, core_rbac, eva_service)
        _v2(client, jwks_env, core_rbac, eva_service)
        _eva_ctx()
        record = _read("record", ref=rec["id"])
        assert not record.is_error, record.structured_content
        revisions = _read("revisions", ref=rec["id"])
        assert not revisions.is_error, revisions.structured_content
        assert revisions.structured_content["data"]["total"] == 2
        rev1 = _read(
            "revision", ref=rec["id"],
            filters={"revision_number": 1},
        )
        assert not rev1.is_error, rev1.structured_content
        cmp_res = _read(
            "revision_compare", ref=rec["id"],
            filters={"from_revision": 1, "to_revision": 2},
        )
        assert not cmp_res.is_error, cmp_res.structured_content
        # mesmo resultado do endpoint REST de comparação
        rest = _get(
            client,
            f"/v1/product-registration/technical-records/{rec['id']}"
            "/comparison?from=1&to=2",
            _token(jwks_env, "analyst-1"),
        )
        assert rest.status_code == 200, rest.text
        assert (
            cmp_res.structured_content["data"]
            == rest.json()["data"]
        )

    def test_record_flag_list(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rec = _v1(client, jwks_env, core_rbac, eva_service)
        created = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        )
        assert created.status_code == 201, created.text
        _eva_ctx()
        res = _read("record_flag_list", ref=rec["id"])
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["total"] == 1
        assert data["openCount"] == 1
        assert data["items"][0]["targetKey"] == "FIELD:description"

    def test_forbidden_without_permission(
        self, client, jwks_env, core_rbac, eva_service
    ):
        _submit_create(client, jwks_env, core_rbac)
        _eva_ctx(permissions=[])
        res = _read("list")
        assert res.is_error

    def test_not_implemented_for_unknown(
        self, client, jwks_env, core_rbac, eva_service
    ):
        _eva_ctx()
        res = _read("fly")
        assert res.is_error
        assert (
            res.structured_content["error_code"] == "not_implemented"
        )


class TestExecuteParityEndToEnd:
    """RQ-07 — executes flippados (submit/update_draft/submit_review)
    provados no caminho MCP completo com ACT habilitado."""

    @pytest.fixture(autouse=True)
    def _act_on(self, monkeypatch):
        monkeypatch.setenv("ENG_EVA_ACT_ENABLED", "true")

    def test_submit_creates_request(
        self, client, jwks_env, core_rbac, eva_service
    ):
        _eva_ctx()
        res = _execute(
            "submit", phase="act",
            payload=_create_body(externalRequestId="eva-ext-1"),
            idempotency_key="eva-submit-1",
        )
        assert not res.is_error, res.structured_content
        rid = res.structured_content["data"]["requestId"]
        rest = _get(
            client, f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        )
        assert rest.status_code == 200, rest.text
        assert rest.json()["data"]["source"] == "eva"

    def test_update_draft_via_eva(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        detail = _get(
            client, f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        version = detail["caseVersion"]
        _eva_ctx()
        res = _execute(
            "update_draft", phase="act", target_ref=rid,
            changes={"changes": [
                {"path": "unit", "proposedValue": "KG",
                 "reason": "EVA"}
            ]},
            expected_version=str(version),
            idempotency_key="eva-draft-1",
        )
        assert not res.is_error, res.structured_content
        rest = _get(
            client, f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        tech = rest.get("technicalDraft") or {}
        assert tech.get("unit") == "KG"

    def test_submit_review_via_eva(
        self, client, jwks_env, core_rbac, eva_service
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        version = _advance_to_attendance(
            client, jwks_env, core_rbac, rid
        )
        _eva_ctx()
        res = _execute(
            "submit_review", phase="act", target_ref=rid,
            expected_version=str(version),
            idempotency_key="eva-review-1",
        )
        assert not res.is_error, res.structured_content
        rest = _get(
            client, f"/v1/product-registration/requests/{rid}",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert rest["status"] == "under_review"

    def test_execute_blocked_when_act_disabled(
        self, client, jwks_env, core_rbac, eva_service, monkeypatch
    ):
        monkeypatch.delenv("ENG_EVA_ACT_ENABLED", raising=False)
        _eva_ctx()
        res = _execute(
            "submit", phase="act",
            payload=_create_body(externalRequestId="eva-ext-2"),
        )
        assert res.is_error

    def test_attachment_list_metadata(
        self, client, jwks_env, core_rbac, eva_service
    ):
        """RQ-08 — paridade de metadados de anexos (binário fora do
        contrato MCP, classificação explícita)."""
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        eva_service["repo"].create_attachment(attachment={
            "id": "att-1", "request_id": rid,
            "original_file_name": "spec.pdf",
            "media_type": "application/pdf", "size_bytes": 128,
            "sha256": "a" * 64, "state": "AVAILABLE",
            "storage_key": "k/1",
            "uploaded_by_subject": "analyst-1",
            "uploaded_by_display_name": "Analyst",
            "created_at": "2026-11-17T00:00:00Z",
        })
        rest = _get(
            client,
            f"/v1/product-registration/requests/{rid}/attachments",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        _eva_ctx()
        res = _read("attachment_list", ref=rid)
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["attachments"] == rest["attachments"]
        # metadados apenas — sem storage_key/path físico
        assert "storage_key" not in str(data["attachments"])
