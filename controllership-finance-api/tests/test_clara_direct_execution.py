"""CLARA-MCP-SEMANTIC-002 (doc 124) — execução direta por risco.

Cobre:
- `execute_direct`: selagem → claim → execução canônica → pós-condição
  por read-back → auditoria, SEM desafio de consentimento.
- Allowlist tipada: só capabilities marcadas `direct` no registry —
  demais recusam com `consent_required` (caminho governado intacto).
- Idempotência física (V019): retry idêntico devolve `replayed`;
  outcome UNKNOWN/FAILED é bloqueio honesto; conflito de key
  concorrente reconcilia pelo resultado já gravado.
- Gates: manage/dre revalidados na execução; snapshot indisponível
  bloqueia; falha de pós-condição ⇒ `outcome_verification_failed`.
- Dispatcher: `phase` omitida executa direto para DIRECT_ALLOWED e
  mantém prepare para governadas; `phase=direct` em governada/delete
  ⇒ `consent_required` tipado.
- Orquestração: diretas executam já; governadas voltam
  `pending_confirmation`; dependentes bloqueiam até o dep executar;
  outcomes parciais honestos.
"""

from __future__ import annotations

import json

import pytest
from unittest.mock import MagicMock

from mcp.types import CallToolResult

from controllership_finance_app.application.clara import governed_writes as gw_mod
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
)
from controllership_finance_app.application.clara.step_up_consent import (
    ConsentRequired,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    IdempotencyConflict,
)
from controllership_finance_app.interface.mcp import semantic_bridge as sb
from controllership_finance_app.interface.mcp import tool_bridge


def _payload(result: CallToolResult) -> dict:
    return result.structured_content or json.loads(
        result.content[0].text
    )


@pytest.fixture()
def actor(monkeypatch):
    user = MagicMock()
    user.id = "3f8f3e9b-8d8c-4b3a-9a77-0f6a2a4b9c11"
    user.name = "Usuária Teste"
    monkeypatch.setattr(
        sb, "_user_and_access", lambda: (MagicMock(), user)
    )
    monkeypatch.setattr(
        tool_bridge, "_user_and_access", lambda: (MagicMock(), user)
    )
    monkeypatch.setattr(sb, "actor_subject", lambda _u: "sub-1")
    return user


# ------------------------------------------------------------------
# execute_direct — núcleo governado sem consentimento
# ------------------------------------------------------------------


def _direct_spec(**over):
    spec = {
        "gate": "access",
        "direct": True,
        "resource_type": "pendency",
        "resource_key": lambda p: "rk-1",
        "required_params": ("period", "kind", "title"),
        "describe": lambda p: "criar pendência",
        "execute": lambda p, actor, groups: {"pendency_id": "p1"},
        "verify": lambda p, result: bool(result.get("pendency_id")),
        "postcondition": lambda p, result, actor: True,
    }
    spec.update(over)
    return spec


def _writes(table: dict) -> ClaraGovernedWrites:
    gw = ClaraGovernedWrites(
        proposals=MagicMock(),
        identity_provider=lambda: {
            "is_manage": False,
            "is_dre": False,
        },
    )
    gw._capability_table = lambda: table  # type: ignore[method-assign]
    gw._snapshot = (  # type: ignore[method-assign]
        lambda capability, params: {"state": "OPEN"}
    )
    return gw


def _fresh_proposal() -> dict:
    return {
        "proposal_id": "prop-1",
        "capability": "pendency.create",
        "resource_type": "pendency",
        "resource_key": "rk-1",
        "payload": {},
        "expected_state": {"state": "OPEN"},
        "expires_at": None,
        "created_at": None,
    }


PARAMS = {"period": "2026-10", "kind": "K", "title": "T"}


def test_execute_direct_happy_path_executes_and_audits(monkeypatch):
    audits: list[str] = []
    monkeypatch.setattr(
        gw_mod, "_audit_mcp",
        lambda *, event_type, **kw: audits.append(event_type),
    )
    gw = _writes({"pendency.create": _direct_spec()})
    gw._proposals.find_by_idempotency.return_value = None
    gw._proposals.create.return_value = _fresh_proposal()

    res = gw.execute_direct(
        capability="pendency.create",
        params=dict(PARAMS),
        actor_sub="sub-1",
    )
    assert res["executed"] is True
    assert res["consent"] == "not_required"
    assert res["result"] == {"pendency_id": "p1"}
    gw._proposals.claim.assert_called_once()
    gw._proposals.record_result.assert_called_once()
    stored = gw._proposals.record_result.call_args.kwargs["result"]
    assert stored["outcome"] == "executed"
    assert "CLARA_DIRECT_ATTEMPT" in audits
    assert "CLARA_DIRECT_ACT" in audits


def test_execute_direct_derives_deterministic_idempotency_key():
    gw = _writes({"pendency.create": _direct_spec()})
    gw._proposals.find_by_idempotency.return_value = None
    gw._proposals.create.return_value = _fresh_proposal()
    gw.execute_direct(
        capability="pendency.create",
        params=dict(PARAMS),
        actor_sub="sub-1",
    )
    key = gw._proposals.create.call_args.kwargs["idempotency_key"]
    assert key.startswith("clara-direct-")
    # Mesmos params ⇒ mesma key (retry replaya); params diferentes
    # ⇒ key diferente.
    gw._proposals.create.return_value = _fresh_proposal()
    gw.execute_direct(
        capability="pendency.create",
        params=dict(PARAMS),
        actor_sub="sub-1",
    )
    assert (
        gw._proposals.create.call_args.kwargs["idempotency_key"] == key
    )


def test_execute_direct_replay_returns_verified_result(monkeypatch):
    monkeypatch.setattr(
        gw_mod, "_audit_mcp", lambda **kw: None
    )
    executed = []

    spec = _direct_spec(
        execute=lambda p, a, g: executed.append(1) or {"id": 1}
    )
    gw = _writes({"pendency.create": spec})
    gw._proposals.find_by_idempotency.return_value = {
        "resource_key": "rk-1",
        "execution_state": "VERIFIED",
        "result": {"outcome": "executed", "result": {"id": 1}},
    }
    res = gw.execute_direct(
        capability="pendency.create",
        params=dict(PARAMS),
        actor_sub="sub-1",
    )
    assert res["executed"] is True
    assert res["replayed"] is True
    assert res["result"] == {"id": 1}
    assert executed == []
    gw._proposals.create.assert_not_called()


def test_execute_direct_unknown_outcome_blocks_honestly():
    gw = _writes({"pendency.create": _direct_spec()})
    gw._proposals.find_by_idempotency.return_value = {
        "resource_key": "rk-1",
        "execution_state": "CLAIMED",
        "result": None,
    }
    with pytest.raises(IdempotencyConflict):
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )
    gw._proposals.create.assert_not_called()


def test_execute_direct_failed_prior_propagates_typed_error():
    gw = _writes({"pendency.create": _direct_spec()})
    gw._proposals.find_by_idempotency.return_value = {
        "resource_key": "rk-1",
        "execution_state": "FAILED",
        "result": {"outcome": "failed", "error_code": "business_rule"},
    }
    with pytest.raises(ChecklistDomainError):
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )


def test_execute_direct_insert_conflict_reconciles_replay():
    gw = _writes({"pendency.create": _direct_spec()})
    findings = [
        None,  # primeira consulta — ninguém
        {      # após UniqueViolation — concorrente já verificou
            "resource_key": "rk-1",
            "execution_state": "VERIFIED",
            "result": {"outcome": "executed", "result": {"id": 9}},
        },
    ]
    gw._proposals.find_by_idempotency.side_effect = findings
    gw._proposals.create.side_effect = IdempotencyConflict("dup")
    res = gw.execute_direct(
        capability="pendency.create",
        params=dict(PARAMS),
        actor_sub="sub-1",
    )
    assert res["replayed"] is True
    assert res["result"] == {"id": 9}


def test_execute_direct_rejects_non_direct_capability():
    spec = _direct_spec()
    spec["direct"] = False
    gw = _writes({"pendency.create": spec})
    with pytest.raises(ConsentRequired):
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )


def test_execute_direct_rejects_unknown_capability():
    gw = _writes({})
    with pytest.raises(ChecklistDomainError):
        gw.execute_direct(
            capability="admin.purge",
            params={},
            actor_sub="sub-1",
        )


def test_execute_direct_requires_params():
    gw = _writes({"pendency.create": _direct_spec()})
    with pytest.raises(ChecklistDomainError):
        gw.execute_direct(
            capability="pendency.create",
            params={"period": "2026-10"},
            actor_sub="sub-1",
        )


def test_execute_direct_gate_denied_no_mutation():
    spec = _direct_spec(gate="manage")
    gw = _writes({"pendency.create": spec})
    # identity_provider já devolve is_manage=False
    with pytest.raises(ChecklistDomainError) as exc:
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )
    assert getattr(exc.value, "code", "") == "forbidden"
    gw._proposals.create.assert_not_called()


def test_execute_direct_snapshot_unavailable_blocks():
    gw = _writes({"pendency.create": _direct_spec()})
    gw._proposals.find_by_idempotency.return_value = None
    gw._snapshot = lambda capability, params: {}  # type: ignore
    with pytest.raises(ChecklistDomainError) as exc:
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )
    assert getattr(exc.value, "code", "") == "snapshot_unavailable"
    gw._proposals.create.assert_not_called()


def test_execute_direct_postcondition_failure_is_unknown(monkeypatch):
    monkeypatch.setattr(gw_mod, "_audit_mcp", lambda **kw: None)
    spec = _direct_spec(postcondition=lambda p, r, a: False)
    gw = _writes({"pendency.create": spec})
    gw._proposals.find_by_idempotency.return_value = None
    gw._proposals.create.return_value = _fresh_proposal()
    with pytest.raises(ChecklistDomainError) as exc:
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )
    assert getattr(exc.value, "code", "") == (
        "outcome_verification_failed"
    )
    stored = gw._proposals.record_result.call_args.kwargs["result"]
    assert stored["outcome"] == "unverified"


def test_execute_direct_domain_error_recorded_failed(monkeypatch):
    monkeypatch.setattr(gw_mod, "_audit_mcp", lambda **kw: None)

    class Boom(ChecklistDomainError):
        code = "business_rule"

    spec = _direct_spec(
        execute=lambda p, a, g: (_ for _ in ()).throw(
            Boom("regra violada")
        )
    )
    gw = _writes({"pendency.create": spec})
    gw._proposals.find_by_idempotency.return_value = None
    gw._proposals.create.return_value = _fresh_proposal()
    with pytest.raises(Boom):
        gw.execute_direct(
            capability="pendency.create",
            params=dict(PARAMS),
            actor_sub="sub-1",
        )
    stored = gw._proposals.record_result.call_args.kwargs["result"]
    assert stored["outcome"] == "failed"
    assert stored["error_code"] == "business_rule"


# ------------------------------------------------------------------
# Dispatcher — fase default proporcional ao risco
# ------------------------------------------------------------------


@pytest.fixture()
def governed(monkeypatch, actor):
    gw = MagicMock()
    gw._capability_table.return_value = {
        "pendency.create": {
            "resource_type": "pendency",
            "required_params": ("period", "kind", "title"),
            "gate": "access",
            "destructive": False,
            "direct": True,
        },
        "package.finalize": {
            "resource_type": "package",
            "required_params": ("period", "package_id"),
            "gate": "manage",
            "destructive": False,
            "direct": False,
        },
        "document.cancel": {
            "resource_type": "document",
            "required_params": ("period", "document_id", "reason"),
            "gate": "access",
            "destructive": True,
            "direct": False,
        },
    }
    gw.capabilities.return_value = []
    gw.prepare.return_value = {
        "proposal_handle": "h1",
        "proposal_id": "prop-1",
        "confirmation_url": "https://portal/consent/1",
        "operation": {},
        "expires_at": "2026-10-29T12:00:00Z",
    }
    gw.execute_direct.return_value = {
        "executed": True,
        "capability": "pendency.create",
        "result": {"pendency_id": "p1"},
        "consent": "not_required",
    }
    monkeypatch.setattr(sb, "_governed_writes", lambda: gw)
    return gw


def test_default_phase_executes_direct_capability(governed):
    res = sb.tool_execute(
        entity="pendency", action="create",
        params=dict(PARAMS),
    )
    assert res.is_error is False
    governed.execute_direct.assert_called_once_with(
        capability="pendency.create",
        params=dict(PARAMS),
        actor_sub="sub-1",
    )
    governed.prepare.assert_not_called()


def test_explicit_direct_phase_executes(governed):
    res = sb.tool_execute(
        entity="pendency", action="create",
        params=dict(PARAMS), phase="direct",
    )
    assert res.is_error is False
    governed.execute_direct.assert_called_once()


def test_prepare_phase_still_available_for_direct_capability(
    governed,
):
    res = sb.tool_execute(
        entity="pendency", action="create",
        params=dict(PARAMS), phase="prepare",
    )
    assert res.is_error is False
    governed.prepare.assert_called_once()
    governed.execute_direct.assert_not_called()


def test_governed_capability_defaults_to_prepare(governed):
    res = sb.tool_execute(
        entity="package", action="finalize",
        params={"period": "2026-10", "package_id": "pk1"},
    )
    assert res.is_error is False
    governed.prepare.assert_called_once()
    governed.execute_direct.assert_not_called()


def test_direct_phase_on_governed_capability_is_consent_required(
    governed,
):
    res = sb.tool_execute(
        entity="package", action="finalize",
        params={"period": "2026-10", "package_id": "pk1"},
        phase="direct",
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "consent_required"
    governed.execute_direct.assert_not_called()


def test_delete_never_executes_directly(governed):
    res = sb.tool_delete(
        entity="document", action="cancel",
        params={
            "period": "2026-10",
            "document_id": "d1",
            "reason": "r",
        },
        phase="direct",
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "consent_required"


def test_missing_params_blocked_before_direct_execution(governed):
    res = sb.tool_execute(
        entity="pendency", action="create",
        params={"period": "2026-10"},
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"
    governed.execute_direct.assert_not_called()


def test_execute_direct_domain_error_maps_typed(governed):
    class Boom(ChecklistDomainError):
        code = "forbidden"
        status = 403

    governed.execute_direct.side_effect = Boom("sem permissão")
    res = sb.tool_execute(
        entity="pendency", action="create",
        params=dict(PARAMS),
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "forbidden"


# ------------------------------------------------------------------
# Orquestração — diretas executam, governadas preparam, deps bloqueiam
# ------------------------------------------------------------------


@pytest.fixture()
def orch(monkeypatch, governed):
    o = MagicMock()
    monkeypatch.setattr(sb, "_batch_orchestrator", lambda: o)
    return o


def _plan(ops: list[dict]) -> dict:
    return {
        "operations": ops,
        "viable_count": len(
            [o for o in ops if o["status"] == "viable"]
        ),
        "blocked_count": len(
            [o for o in ops if o["status"] != "viable"]
        ),
        "plan_hash": "ph1",
    }


def test_orchestrated_batch_executes_direct_and_prepares_governed(
    orch, governed,
):
    orch.plan_batch.return_value = _plan([
        {
            "index": 0,
            "capability": "pendency.create",
            "params": dict(PARAMS),
            "depends_on": [],
            "status": "viable",
            "resource_type": "pendency",
        },
        {
            "index": 1,
            "capability": "package.finalize",
            "params": {"period": "2026-10", "package_id": "pk1"},
            "depends_on": [],
            "status": "viable",
            "resource_type": "package",
        },
        {
            "index": 2,
            "capability": "pendency.transition",
            "params": {"period": "2026-10", "pendency_id": "p"},
            "depends_on": [1],
            "status": "viable",
            "resource_type": "pendency",
        },
    ])
    governed._capability_table.return_value["pendency.transition"] = {
        "resource_type": "pendency",
        "required_params": ("period", "pendency_id"),
        "gate": "access",
        "destructive": False,
        "direct": True,
    }
    res = sb.tool_execute(
        batch={
            "operations": [
                {"entity": "pendency", "action": "create",
                 "params": dict(PARAMS)},
                {"entity": "package", "action": "finalize",
                 "params": {
                     "period": "2026-10", "package_id": "pk1",
                 }},
                {"entity": "pendency", "action": "transition",
                 "params": {"period": "2026-10", "pendency_id": "p"},
                 "depends_on": [1]},
            ],
        }
    )
    assert res.is_error is False
    data = _payload(res)["data"]
    statuses = {
        o["index"]: o["status"] for o in data["operations"]
    }
    assert statuses[0] == "executed"
    assert statuses[1] == "pending_confirmation"
    # dependente de operação governada pendente ⇒ bloqueado
    assert statuses[2] == "blocked"
    assert data["summary"]["executed"] == 1
    assert data["summary"]["pending_confirmation"] == 1
    assert data["summary"]["blocked"] == 1


def test_orchestrated_batch_dependency_failure_blocks_dependent(
    orch, governed,
):
    class Boom(ChecklistDomainError):
        code = "business_rule"

    governed.execute_direct.side_effect = Boom("violou regra")
    orch.plan_batch.return_value = _plan([
        {
            "index": 0, "capability": "pendency.create",
            "params": dict(PARAMS), "depends_on": [],
            "status": "viable", "resource_type": "pendency",
        },
        {
            "index": 1, "capability": "pendency.claim",
            "params": {"period": "2026-10", "pendency_id": "p"},
            "depends_on": [0],
            "status": "viable", "resource_type": "pendency",
        },
    ])
    governed._capability_table.return_value["pendency.claim"] = {
        "resource_type": "pendency",
        "required_params": ("period", "pendency_id"),
        "gate": "access", "destructive": False, "direct": True,
    }
    res = sb.tool_execute(
        batch={
            "operations": [
                {"entity": "pendency", "action": "create",
                 "params": dict(PARAMS)},
                {"entity": "pendency", "action": "claim",
                 "params": {"period": "2026-10", "pendency_id": "p"},
                 "depends_on": [0]},
            ],
        }
    )
    data = _payload(res)["data"]
    statuses = {o["index"]: o["status"] for o in data["operations"]}
    assert statuses[0] == "failed"
    assert statuses[1] == "blocked"
    assert data["summary"]["failed"] == 1


def test_orchestrated_batch_all_direct_executes_in_order(
    orch, governed,
):
    calls: list[str] = []
    governed.execute_direct.side_effect = (
        lambda **kw: calls.append(kw["capability"]) or {
            "executed": True,
        }
    )
    governed._capability_table.return_value["pendency.claim"] = {
        "resource_type": "pendency",
        "required_params": ("period", "pendency_id"),
        "gate": "access", "destructive": False, "direct": True,
    }
    orch.plan_batch.return_value = _plan([
        {
            "index": 0, "capability": "pendency.create",
            "params": dict(PARAMS), "depends_on": [],
            "status": "viable", "resource_type": "pendency",
        },
        {
            "index": 1, "capability": "pendency.claim",
            "params": {"period": "2026-10", "pendency_id": "p"},
            "depends_on": [0],
            "status": "viable", "resource_type": "pendency",
        },
    ])
    res = sb.tool_execute(
        batch={
            "phase": "run",
            "operations": [
                {"entity": "pendency", "action": "create",
                 "params": dict(PARAMS)},
                {"entity": "pendency", "action": "claim",
                 "params": {"period": "2026-10", "pendency_id": "p"},
                 "depends_on": [0]},
            ],
        }
    )
    data = _payload(res)["data"]
    assert data["summary"]["executed"] == 2
    assert calls == ["pendency.create", "pendency.claim"]


def test_orchestrated_batch_blocked_plan_op_reported(orch, governed):
    orch.plan_batch.return_value = _plan([
        {
            "index": 0, "capability": "admin.purge",
            "params": {}, "depends_on": [],
            "status": "blocked", "block_reason": "unknown_capability",
            "resource_type": None,
        },
    ])
    res = sb.tool_execute(
        batch={"operations": [{"entity": "admin", "action": "purge"}]}
    )
    data = _payload(res)["data"]
    assert data["operations"][0]["status"] == "blocked"
    assert data["operations"][0]["reason"] == "unknown_capability"
    governed.execute_direct.assert_not_called()


# ------------------------------------------------------------------
# Catálogo — flags de risco expostas
# ------------------------------------------------------------------


def test_catalog_exposes_direct_flag_and_phase_policy(
    monkeypatch, actor,
):
    gw = MagicMock()
    gw.capabilities.return_value = [
        {
            "capability": "pendency.create",
            "resource_type": "pendency",
            "required_params": ["period", "kind", "title"],
            "gate": "access",
            "destructive": False,
            "direct": True,
        },
        {
            "capability": "document.cancel",
            "resource_type": "document",
            "required_params": ["period", "document_id"],
            "gate": "access",
            "destructive": True,
            "direct": False,
        },
    ]
    monkeypatch.setattr(sb, "_governed_writes", lambda: gw)
    monkeypatch.setattr(
        sb, "_is_manage", lambda _u: False
    ) if hasattr(sb, "_is_manage") else None
    catalog = sb._semantic_catalog({"is_manage": False, "is_dre": False})
    by_cap = {
        e["capability"]: e for e in catalog["actions"]["governed"]
    }
    assert by_cap["pendency.create"]["direct"] is True
    assert by_cap["pendency.create"]["phase_policy"] == (
        "direct_or_prepare_consent_act"
    )
    assert by_cap["document.cancel"]["direct"] is False
    assert by_cap["document.cancel"]["phase_policy"] == (
        "prepare_consent_act"
    )


def test_schema_for_reflects_risk_policy(monkeypatch, actor):
    gw = MagicMock()
    gw._capability_table.return_value = {
        "pendency.create": {
            "resource_type": "pendency",
            "required_params": ("period", "kind", "title"),
            "gate": "access",
            "destructive": False,
            "direct": True,
        },
    }
    monkeypatch.setattr(sb, "_governed_writes", lambda: gw)
    schema = sb._schema_for("pendency", "create")
    assert schema["direct"] is True
    assert "direct" in schema["phase_policy"]


# ------------------------------------------------------------------
# TRANSVERSAL-001 — classificação real do registry (sem mocks)
# ------------------------------------------------------------------


def test_registry_marks_draft_caps_direct():
    """Doc 124 rev. A: as duas operações de rascunho são DIRECT_ALLOWED
    no registry real — guarda contra remoção acidental da flag."""
    table = ClaraGovernedWrites()._capability_table()
    assert table["checklist.draft_create"]["direct"] is True
    assert table["checklist.draft_update"]["direct"] is True
    # Vizinhas de governança continuam governadas.
    for cap in (
        "checklist.version_submit",
        "checklist.version_publish",
        "checklist.version_discard",
        "checklist.doc_requirement",
        "catalog.entry_create",
        "catalog.entry_update",
        "competence.open",
        "package.finalize",
        "p3.upsert_reconciliation",
        "item.create_exceptional",
    ):
        assert not table[cap].get("direct"), cap


def test_registry_direct_count_is_thirteen():
    table = ClaraGovernedWrites()._capability_table()
    direct = [c for c, s in table.items() if s.get("direct")]
    assert len(direct) == 13
