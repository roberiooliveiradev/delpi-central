"""EVA-PRC-COMPLETE-FLOW-SEMANTIC-PARITY-02 — paridade REST × MCP das
capacidades adicionadas no ciclo de fluxo completo PRC.

Todas as chamadas passam pelo gate real (``sem.tool_read`` /
``sem.tool_execute`` → registry ``proven`` → dispatch → mesmo
``ProductRegistrationService`` das rotas REST). ``route_divergence``
ficou EXCLUDED (rota REST deprecated — REF-021 não é etapa
compulsória do Portal).
"""

from __future__ import annotations

import asyncio
import pytest
from types import SimpleNamespace

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tests.conftest import rbac_payload
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    FakeReader,
    _advance_to_attendance,
    _get,
    _post,
    _product,
    _submit_create,
    _token,
)
from tests.test_prc_conversation import _post_comment_ok  # noqa: F401
from tests.test_prc_record_flags import (  # noqa: F401
    _create_flag,
    _v1,
    prc_service_repo,
)
from tests.test_prc_information_rounds import (  # noqa: F401
    _answers,
    _open_round,
)
from tests.test_d16_attendance_flags import (  # noqa: F401
    _create_flag as _create_request_flag,
)

from engineering_app.interface.mcp import semantic_bridge as sem
from engineering_app.interface.mcp.semantic_bridge import (
    _EXECUTE_DISPATCH,
    _READ_DISPATCH,
)

REQUESTER_SUB = "user-1"
ANALYST_SUB = "analyst-1"
_BASE = "/v1/product-registration"


def _eva_ctx(user_id=ANALYST_SUB, permissions=None):
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


class TestDispatchAndGates:
    def test_new_dispatch_entries_registered(self):
        for a in (
            "correction_return_list", "correction_return_get",
            "edit_context", "catalog_items", "supplier_search",
            "outbound_list", "comment_attachment_list",
            "record_flag_events", "flag_list_cross", "flag_summary",
        ):
            assert ("product_registration", a) in _READ_DISPATCH, a
        for a in (
            "record_flag_create", "record_flag_update",
            "record_flag_resolve", "record_flag_remove",
            "information_draft_answers", "information_submit_answers",
        ):
            assert ("product_registration", a) in _EXECUTE_DISPATCH, a
        # route_divergence EXCLUDED — rota REST deprecated
        assert ("product_registration", "route_divergence") \
            not in _EXECUTE_DISPATCH

    def test_route_divergence_rejected_as_unknown(self):
        _eva_ctx()
        res = _read("route_divergence", ref="x")
        assert res.is_error

    def test_read_forbidden_without_permission(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        _eva_ctx(permissions=[])
        for a in ("correction_return_list", "outbound_list"):
            res = _read(a, ref=rid) if a != "outbound_list" else _read(a)
            assert res.is_error, a


class TestNewReadsEndToEnd:
    def test_correction_returns_empty_then_not_found(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        _eva_ctx()
        res = _read("correction_return_list", ref=rid)
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data.get("returns") == [] or data.get("items") == []
        # get sem return_id → validation; return_id inexistente → 404
        missing = _read("correction_return_get", ref=rid)
        assert missing.is_error
        notfound = _read(
            "correction_return_get", ref=rid,
            filters={"return_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert notfound.is_error

    def test_outbound_list_matches_rest(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        rest = _get(
            client, f"{_BASE}/outbound/requests",
            _token(jwks_env, ANALYST_SUB),
        ).json()["data"]
        _eva_ctx()
        res = _read("outbound_list")
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["total"] == rest["total"]
        items = data.get("items") or []
        assert rid in {
            i.get("requestId") or i.get("request_id") for i in items
        }

    def test_comment_attachment_list(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        c = _post_comment_ok(
            client, jwks_env, core_rbac, rid, body="msg com anexo"
        )
        cid = c["commentId"]
        _eva_ctx()
        res = _read(
            "comment_attachment_list", ref=rid,
            filters={"comment_id": cid},
        )
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert data["requestId"] == rid
        missing = _read("comment_attachment_list", ref=rid)
        assert missing.is_error

    def test_record_flag_events(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        fid = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]["id"]
        _eva_ctx()
        res = _read(
            "record_flag_events", ref=rec["id"],
            filters={"flag_id": fid},
        )
        assert not res.is_error, res.structured_content
        events = res.structured_content["data"]
        items = events.get("items") or events.get("events") or []
        assert any(
            "created" in str(
                e.get("eventType") or e.get("event")
                or e.get("type") or ""
            ).lower()
            for e in items
        ), events

    def test_edit_context_delegated_reader(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        prc_service_repo["reader"] = FakeReader(_product())
        _eva_ctx()
        res = _read(
            "edit_context", filters={"official_code": "001234"}
        )
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        assert isinstance(data, dict) and data
        missing = _read("edit_context")
        assert missing.is_error

    def test_catalog_items_delegated(
        self, client, jwks_env, core_rbac, prc_service_repo,
        monkeypatch,
    ):
        from engineering_app.infrastructure.gateways import (
            downstream_client as dc,
        )

        async def _fake_get(self, path, *, params=None, access_token,
                            request_id=None, service_token=None):
            assert access_token == "eva-token"
            return {"items": [{"code": "KG"}]}
        monkeypatch.setattr(dc.DownstreamClient, "get", _fake_get)
        _eva_ctx()
        res = _read(
            "catalog_items",
            filters={"catalog": "units", "query": "KG"},
        )
        assert not res.is_error, res.structured_content
        assert res.structured_content["data"]["items"][0]["code"] == "KG"
        missing = _read("catalog_items", filters={"query": "x"})
        assert missing.is_error

    def test_flag_cross_list_and_summary(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac
        ).json()["data"]["requestId"]
        created = _create_request_flag(
            client, jwks_env, core_rbac, rid, key="x-flag-1"
        )
        assert created.status_code == 201, created.text
        _eva_ctx()
        res = _read("flag_list_cross")
        assert not res.is_error, res.structured_content
        data = res.structured_content["data"]
        items = data.get("items") or []
        assert rid in {
            i.get("requestId") or i.get("request_id") for i in items
        }
        scoped = _read(
            "flag_list_cross", filters={"request_id": rid}
        )
        assert not scoped.is_error, scoped.structured_content
        assert scoped.structured_content["data"]["total"] >= 1
        summ = _read("flag_summary", filters={"group_by": "request"})
        assert not summ.is_error, summ.structured_content

    def test_supplier_search_delegated(
        self, client, jwks_env, core_rbac, prc_service_repo,
        monkeypatch,
    ):
        from engineering_app.infrastructure.gateways import (
            downstream_client as dc,
        )

        async def _fake_get(self, path, *, params=None, access_token,
                            request_id=None, service_token=None):
            assert "/suppliers" in path
            return {"items": [{"supplierCode": "000001"}]}
        monkeypatch.setattr(dc.DownstreamClient, "get", _fake_get)
        _eva_ctx()
        res = _read(
            "supplier_search",
            filters={"query": "FORN", "page": 1, "page_size": 20},
        )
        assert not res.is_error, res.structured_content
        assert (
            res.structured_content["data"]["items"][0]["supplierCode"]
            == "000001"
        )


class TestRecordFlagWriteEndToEnd:
    """Bandeiras de produto acompanhado — ciclo completo via EVA com
    read-back REST na mesma identidade."""

    @pytest.fixture(autouse=True)
    def _act_on(self, monkeypatch):
        monkeypatch.setenv("ENG_EVA_ACT_ENABLED", "true")

    def test_create_update_resolve_via_eva(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        _eva_ctx()
        created = _execute(
            "record_flag_create", phase="act", target_ref=rec["id"],
            payload={
                "title": "Descrição divergente",
                "description": "Conferir com o oficial.",
                "subject": "FIELD", "target_path": "description",
            },
            idempotency_key="eva-rf-1",
        )
        assert not created.is_error, created.structured_content
        fid = created.structured_content["data"]["id"]
        # read-back REST — mesmo registro, mesma identidade
        rest = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}/flags",
            _token(jwks_env, ANALYST_SUB),
        ).json()["data"]
        assert fid in {f["id"] for f in rest["items"]}

        upd = _execute(
            "record_flag_update", phase="act", target_ref=rec["id"],
            payload={"flag_id": fid, "title": "Título revisado"},
            expected_version="1",
        )
        assert not upd.is_error, upd.structured_content
        # CAS — versão velha falha com stale_version
        stale = _execute(
            "record_flag_update", phase="act", target_ref=rec["id"],
            payload={"flag_id": fid, "title": "X"},
            expected_version="1",
        )
        assert stale.is_error

        res = _execute(
            "record_flag_resolve", phase="act", target_ref=rec["id"],
            payload={"flag_id": fid, "note": "ok"},
            expected_version="2",
        )
        assert not res.is_error, res.structured_content
        rest2 = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}/flags",
            _token(jwks_env, ANALYST_SUB),
        ).json()["data"]
        flag = next(f for f in rest2["items"] if f["id"] == fid)
        assert flag["status"] == "RESOLVED"
        assert flag["title"] == "Título revisado"

    def test_remove_requires_sealed_proposal(
        self, client, jwks_env, core_rbac, prc_service_repo,
        monkeypatch,
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        fid = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]["id"]
        _eva_ctx()
        prep = _execute(
            "record_flag_remove", phase="prepare",
            target_ref=rec["id"],
            payload={"flag_id": fid},
            expected_version="1",
        )
        assert not prep.is_error, prep.structured_content
        proposal_ref = prep.structured_content["data"]["proposal_ref"]
        # commit sem proposta → bloqueado
        blocked = _execute(
            "record_flag_remove", phase="commit",
            target_ref=rec["id"],
            payload={"flag_id": fid},
            expected_version="1",
        )
        assert blocked.is_error
        # commit com proposta + confirmação humana satisfeita
        async def _ok_conf(*_a, **_k):
            return None
        monkeypatch.setattr(
            sem, "_require_human_confirmation", _ok_conf
        )
        done = _execute(
            "record_flag_remove", phase="commit",
            target_ref=rec["id"],
            payload={"flag_id": fid},
            expected_version="1",
            proposal_ref=proposal_ref,
        )
        assert not done.is_error, done.structured_content
        # REMOVED é terminal — flag sai da listagem padrão;
        # eventos preservam a remoção (read-back via própria EVA)
        ev = _read(
            "record_flag_events", ref=rec["id"],
            filters={"flag_id": fid},
        )
        assert not ev.is_error, ev.structured_content
        types = [
            str(e.get("eventType") or "")
            for e in ev.structured_content["data"]["items"]
        ]
        assert any("removed" in t for t in types), types

    def test_create_denied_for_requester(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        _eva_ctx(user_id=REQUESTER_SUB)
        res = _execute(
            "record_flag_create", phase="act", target_ref=rec["id"],
            payload={"title": "t", "description": "d"},
        )
        assert res.is_error


class TestInformationAnswersEndToEnd:
    """Draft/submit de respostas pelo solicitante via gate MCP."""

    @pytest.fixture(autouse=True)
    def _act_on(self, monkeypatch):
        monkeypatch.setenv("ENG_EVA_ACT_ENABLED", "true")

    def test_draft_then_submit_matches_rest(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        _eva_ctx(user_id=REQUESTER_SUB)
        draft = _execute(
            "information_draft_answers", phase="act", target_ref=rid,
            payload={
                "round_id": rnd["id"],
                "answers": _answers(rnd),
            },
            expected_version=str(rnd["version"]),
            idempotency_key="eva-ans-1",
        )
        assert not draft.is_error, draft.structured_content
        version = draft.structured_content["data"]["version"]
        submit = _execute(
            "information_submit_answers", phase="act", target_ref=rid,
            payload={
                "round_id": rnd["id"],
                "answers": _answers(rnd),
            },
            expected_version=str(version),
            idempotency_key="eva-ans-2",
        )
        assert not submit.is_error, submit.structured_content
        # read-back REST — rodada respondida
        rest = _get(
            client,
            f"{_BASE}/requests/{rid}/information-rounds",
            _token(jwks_env, ANALYST_SUB),
        ).json()["data"]
        rnd_rest = next(
            r for r in rest["items"] if r["id"] == rnd["id"]
        )
        assert rnd_rest["status"] in ("answered", "submitted",
                                      "closed", "ANSWERED",
                                      "awaiting_review")

    def test_draft_denied_for_analyst(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        _eva_ctx()  # analista — não é o solicitante do caso
        res = _execute(
            "information_draft_answers", phase="act", target_ref=rid,
            payload={
                "round_id": rnd["id"],
                "answers": _answers(rnd),
            },
            expected_version=str(rnd["version"]),
        )
        assert res.is_error

    def test_submit_stale_round_version(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        _eva_ctx(user_id=REQUESTER_SUB)
        res = _execute(
            "information_submit_answers", phase="act", target_ref=rid,
            payload={
                "round_id": rnd["id"],
                "answers": _answers(rnd),
            },
            expected_version=str(rnd["version"] + 9),
        )
        assert res.is_error
