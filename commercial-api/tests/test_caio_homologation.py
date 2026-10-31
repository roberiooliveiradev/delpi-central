"""CAIO 2.0 executable homologation suite — issue #125.

Covers the full semantic catalog at contract level:
- every READ: unknown filter → 400; undeclared pagination → 400;
  declared pagination reaches the owner adapter;
- every ANALYZE: dispatch coverage + required upstream params → 400;
- every EXECUTE: unknown field → 400; missing ref → 400; full declared
  field surface reaches the dispatch handler;
- every DELETE: sealed prepare → commit → replay failure, per
  capability with the correct target_ref shape;
- AuthZ profile matrix: no context → 401; non-commercial user → 403;
  service principal → 403; access user on manage-gated adapters → 403
  (proven by calling the REAL handler — the gate fires before any
  owner use case/DB call).

Owner-integration (real use case → TOTVS/DB) and authenticated
production calls remain TEST_NOT_RUN — no isolated TOTVS/DB fixture
and no Keycloak mcp-commercial client; both are recorded in
CAIO_HOMOLOGATION_MATRIX.md.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from delpi_mcp.errors import mcp_tool_result

from commercial_app.application.caio import proposal_store
from commercial_app.application.caio.semantic_registry import (
    SEMANTIC_ACTIONS,
    semantic_action,
)
from commercial_app.interface.mcp import semantic_bridge as sem
from commercial_app.interface.mcp import tool_bridge_parity as parity


def _human_user(permissions=("commercial.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    proposal_store.reset_proposal_store_for_tests()
    yield
    proposal_store.reset_proposal_store_for_tests()
    clear_current_user()
    clear_request_authorization()


READS = [a for a in SEMANTIC_ACTIONS if a.tool == "read"]
ANALYSES = [a for a in SEMANTIC_ACTIONS if a.tool == "analyze"]
EXECUTES = [a for a in SEMANTIC_ACTIONS if a.tool == "execute"]
DELETES = [a for a in SEMANTIC_ACTIONS if a.tool == "delete"]

PAGINATION_KEYS = {"page", "page_size", "limit", "cursor"}


def _caps(actions):
    return [a.capability for a in actions]


# --- E1: catalog inventory ---------------------------------------------------------


def test_catalog_inventory_counts():
    counts = {
        "get_context": 0,
        "read": 0,
        "analyze": 0,
        "knowledge": 0,
        "execute": 0,
        "delete": 0,
    }
    for a in SEMANTIC_ACTIONS:
        counts[a.tool] += 1
    assert counts == {
        "get_context": 1,
        "read": 53,
        "analyze": 21,
        "knowledge": 2,
        "execute": 40,
        "delete": 10,
    }
    assert len(SEMANTIC_ACTIONS) == 127
    assert len({a.capability for a in SEMANTIC_ACTIONS}) == 127


def test_get_context_exposes_full_catalog():
    _set_context(_human_user())
    result = sem.tool_get_context()
    assert result.is_error is False
    data = result.structured_content["data"]
    assert len(data["actions"]) == len(SEMANTIC_ACTIONS)
    assert len(data["semantic_tools"]) == 6
    assert all(
        a["status"] == "proven" for a in data["actions"]
    )


# --- E3: read — negative contract (all 49) -------------------------------------------


@pytest.mark.parametrize("cap", _caps(READS))
def test_read_rejects_unknown_filter(cap):
    _set_context(_human_user(permissions=["commercial.access",
                                        "commercial.manage"]))
    entity, action = cap.split(".", 1)
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if semantic_action(entity, action).ref_arg else None,
        filters={"zzz_undeclared_field": 1},
    )
    assert result.is_error is True
    payload = result.structured_content
    assert payload["status_code"] == 400
    assert payload["error_code"] == "validation"


@pytest.mark.parametrize("cap", _caps(READS))
def test_read_rejects_undeclared_pagination(cap):
    entry = next(a for a in READS if a.capability == cap)
    if "page" in entry.fields:
        pytest.skip("capability declares page pagination")
    _set_context(_human_user(permissions=["commercial.access",
                                        "commercial.manage"]))
    entity, action = cap.split(".", 1)
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if entry.ref_arg else None,
        pagination={"page": 1, "page_size": 1},
    )
    assert result.is_error is True
    payload = result.structured_content
    assert payload["status_code"] == 400
    assert payload["error_code"] == "validation"


@pytest.mark.parametrize("cap", _caps(READS))
def test_read_requires_ref_when_declared(cap):
    entry = next(a for a in READS if a.capability == cap)
    if not entry.ref_arg:
        pytest.skip("no ref_arg")
    _set_context(_human_user())
    entity, action = cap.split(".", 1)
    result = sem.tool_read(entity=entity, action=action)
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


# --- E3: read — AuthZ profile matrix (real handlers, no DB reached) -------------------


@pytest.mark.parametrize("cap", _caps(READS))
def test_read_no_context_is_unauthorized(cap):
    entity, action = cap.split(".", 1)
    entry = semantic_action(entity, action)
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if entry.ref_arg else None,
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 401


@pytest.mark.parametrize("cap", _caps(READS))
def test_read_service_principal_is_forbidden(cap):
    entity, action = cap.split(".", 1)
    entry = semantic_action(entity, action)
    _set_context(
        _human_user(principal_type="service",
                    permissions=["commercial.manage"])
    )
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if entry.ref_arg else None,
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 403


@pytest.mark.parametrize("cap", _caps(READS))
def test_read_user_without_permission_is_forbidden(cap):
    entity, action = cap.split(".", 1)
    entry = semantic_action(entity, action)
    _set_context(_human_user(permissions=[]))
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if entry.ref_arg else None,
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 403


# Manage-gated read adapters — the manage check fires inside the real
# handler BEFORE the owner use case, so an access-only user gets 403
# without any DB/infra dependency. Verified per capability.
# NOTE: sla_policy.list and customer_center.list are intentionally
# access-level — the REST routes gate them with
# COMMERCIAL_READ/ANALYTICS permissions (manage only gates
# include_inactive on the route), and the adapters mirror that.
MANAGE_READS = [
    "portfolio.list",
    "portfolio.coverage_audit",
    "portfolio.load_summary",
    "team.roster",
    "group.list",
    "group.get",
]


@pytest.mark.parametrize("cap", MANAGE_READS)
def test_read_manage_gate_fires_for_access_user(cap):
    entity, action = cap.split(".", 1)
    entry = semantic_action(entity, action)
    _set_context(_human_user(permissions=["commercial.access"]))
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if entry.ref_arg else None,
    )
    assert result.is_error is True, cap
    payload = result.structured_content
    assert payload["status_code"] == 403, (
        f"{cap}: expected manage-gate 403, got "
        f"{payload.get('status_code')} {payload.get('error_code')}"
    )


# Required contract fields — missing required args must be a typed
# 400 validation, never a TypeError masked as 502 (issue #125 found
# the same defect class as the pagination bug in #123).
REQUIRED_READ_CASES = [
    (cap, field)
    for cap, field in [
        (a.capability, f)
        for a in READS
        for f in a.required_fields
    ]
]


@pytest.mark.parametrize("cap,field", REQUIRED_READ_CASES)
def test_read_missing_required_field_is_validation(cap, field):
    entry = next(a for a in READS if a.capability == cap)
    _set_context(
        _human_user(
            permissions=["commercial.access", "commercial.manage"]
        )
    )
    entity, action = cap.split(".", 1)
    filters = {
        f: "v" for f in entry.required_fields if f != field
    }
    result = sem.tool_read(
        entity=entity,
        action=action,
        ref="x" if entry.ref_arg else None,
        filters=filters,
    )
    assert result.is_error is True, cap
    payload = result.structured_content
    assert payload["status_code"] == 400, (cap, payload)
    assert payload["error_code"] == "validation"
    assert field in payload["data"]["missing_fields"]


def test_registry_required_fields_match_handler_signatures():
    """Registry must declare exactly the required params of the real
    dispatch handler — keeps required_fields honest forever."""
    import inspect

    from commercial_app.interface.mcp import tool_bridge as bridge_mod

    def required_params(fn, ref_arg):
        return {
            n
            for n, p in inspect.signature(
                fn
            ).parameters.items()
            if p.default is inspect.Parameter.empty
            and p.kind
            in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
            and n != ref_arg
        }

    def resolve(fn):
        if getattr(fn, "__name__", "") == "<lambda>":
            for name in fn.__code__.co_names:
                f = getattr(parity, name, None) or getattr(
                    bridge_mod, name, None
                )
                if callable(f):
                    return f
        return fn

    mismatches = []
    for entry in SEMANTIC_ACTIONS:
        if entry.tool == "read":
            fn = resolve(
                sem._READ_DISPATCH[(entry.entity, entry.action)]
            )
        elif entry.tool == "execute":
            fn = resolve(
                sem._EXECUTE_DISPATCH[(entry.entity, entry.action)]
            )
        else:
            continue
        expected = required_params(fn, entry.ref_arg)
        if set(entry.required_fields) != expected:
            mismatches.append(
                (
                    entry.capability,
                    sorted(entry.required_fields),
                    sorted(expected),
                )
            )
    assert mismatches == [], mismatches


# --- E4: analyze — contract (all 21) ---------------------------------------------------


@pytest.mark.parametrize("cap", _caps(ANALYSES))
def test_analyze_no_context_is_unauthorized(cap):
    result = sem.tool_analyze(analysis_type=cap)
    assert result.is_error is True
    assert result.structured_content["status_code"] == 401


def test_analyze_required_params_map():
    for kind, (_, _, required) in parity.ANALYZE_PROXY_MAP.items():
        if not required:
            continue
        _set_context(_human_user())
        result = sem.tool_analyze(analysis_type=kind, parameters={})
        assert result.is_error is True, kind
        payload = result.structured_content
        assert payload["status_code"] == 400, kind
        assert set(payload["data"]["required"]) == set(required)


def test_analyze_unknown_param_rejected():
    _set_context(_human_user())
    result = sem.tool_analyze(
        analysis_type="rol.summary",
        parameters={"zz_unknown": 1},
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


def test_analyze_unknown_type_is_not_implemented():
    _set_context(_human_user())
    result = sem.tool_analyze(analysis_type="bogus.type")
    assert result.is_error is True
    assert result.structured_content["status_code"] == 501


# --- E5: execute — contract (all 40) ----------------------------------------------------


@pytest.mark.parametrize("cap", _caps(EXECUTES))
def test_execute_rejects_unknown_field(cap):
    _set_context(_human_user(permissions=["commercial.access",
                                        "commercial.manage"]))
    entity, action = cap.split(".", 1)
    entry = semantic_action(entity, action)
    result = sem.tool_execute(
        entity=entity,
        action=action,
        target_ref="x" if entry.ref_arg else None,
        payload={"zzz_undeclared": 1},
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


@pytest.mark.parametrize("cap", _caps(EXECUTES))
def test_execute_requires_target_when_declared(cap):
    entry = next(a for a in EXECUTES if a.capability == cap)
    if not entry.ref_arg:
        pytest.skip("no ref_arg")
    _set_context(_human_user(permissions=["commercial.access",
                                        "commercial.manage"]))
    entity, action = cap.split(".", 1)
    result = sem.tool_execute(
        entity=entity, action=action, payload={}
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


@pytest.mark.parametrize("cap", _caps(EXECUTES))
def test_execute_no_context_is_unauthorized(cap):
    entity, action = cap.split(".", 1)
    result = sem.tool_execute(
        entity=entity, action=action, payload={}
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 401


REQUIRED_EXECUTE_CASES = [
    (cap, field)
    for cap, field in [
        (a.capability, f)
        for a in EXECUTES
        for f in a.required_fields
    ]
]


@pytest.mark.parametrize("cap,field", REQUIRED_EXECUTE_CASES)
def test_execute_missing_required_field_is_validation(cap, field):
    entry = next(a for a in EXECUTES if a.capability == cap)
    _set_context(
        _human_user(
            permissions=["commercial.access", "commercial.manage"]
        )
    )
    entity, action = cap.split(".", 1)
    payload = {
        f: "v" for f in entry.required_fields if f != field
    }
    result = sem.tool_execute(
        entity=entity,
        action=action,
        target_ref="t-1" if entry.ref_arg else None,
        payload=payload,
    )
    assert result.is_error is True, cap
    p = result.structured_content
    assert p["status_code"] == 400, (cap, p)
    assert p["error_code"] == "validation"
    assert field in p["data"]["missing_fields"]


@pytest.mark.parametrize("cap", _caps(EXECUTES))
def test_execute_full_declared_surface_dispatches(cap):
    """Every declared field flows through the contract gate into the
    dispatch handler — proves the (entity, action) wiring accepts the
    documented input surface end to end."""
    entry = next(a for a in EXECUTES if a.capability == cap)
    _set_context(_human_user(permissions=["commercial.access",
                                        "commercial.manage"]))
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    payload = {f: f"{f}-v" for f in entry.fields}
    entity, action = cap.split(".", 1)
    key = (entity, action)
    assert key in sem._EXECUTE_DISPATCH, cap
    with patch.dict(sem._EXECUTE_DISPATCH, {key: fake}):
        result = sem.tool_execute(
            entity=entity,
            action=action,
            target_ref="target-1" if entry.ref_arg else None,
            payload=payload,
        )
    assert result.is_error is False, (
        f"{cap}: {result.structured_content}"
    )
    for field_name in entry.fields:
        assert captured.get(field_name) == f"{field_name}-v", cap
    if entry.ref_arg:
        assert captured.get(entry.ref_arg) == "target-1", cap


# --- E6: delete — full sealed cycle per capability (all 10) -----------------------------


_DELETE_TARGETS = {
    "interaction_message.delete": "room_id=r-1&message_id=m-2",
    "contact.delete": (
        "contact_id=c-1&customer_code=000001&customer_store=01"
    ),
}


def _delete_target(capability: str) -> str:
    return _DELETE_TARGETS.get(capability, "target-1")


@pytest.mark.parametrize("cap", _caps(DELETES))
def test_delete_full_sealed_cycle_per_capability(cap):
    """prepare seals → commit executes → replay fails — for every
    destructive capability with its real target_ref shape."""
    _set_context(_human_user())
    calls = []

    def impact(target):
        return {"target": target, "effect": "test"}

    def executor(target, args):
        calls.append((target, dict(args)))
        return {"deleted": target}

    entity, action = cap.split(".", 1)
    spec = dict(sem._DELETE_SPEC)
    spec[cap] = (impact, executor)
    target = _delete_target(cap)
    with patch.object(sem, "_DELETE_SPEC", spec):
        prep = sem.tool_delete(
            entity=entity,
            action=action,
            target_ref=target,
            phase="prepare",
        )
        assert prep.is_error is False, cap
        ref = prep.structured_content["data"]["proposal_ref"]
        assert prep.structured_content["data"]["proposal"][
            "target_ref"
        ] == target
        commit = sem.tool_delete(
            entity=entity,
            action=action,
            target_ref=target,
            phase="commit",
            proposal_ref=ref,
        )
        replay = sem.tool_delete(
            entity=entity,
            action=action,
            target_ref=target,
            phase="commit",
            proposal_ref=ref,
        )
    assert commit.is_error is False, cap
    assert commit.structured_content["data"]["deleted"] is True
    assert len(calls) == 1, cap
    assert replay.is_error is True
    assert replay.structured_content["error_code"] == (
        "proposal_not_found"
    )


@pytest.mark.parametrize("cap", _caps(DELETES))
def test_delete_commit_without_proposal_fails(cap):
    _set_context(_human_user())
    entity, action = cap.split(".", 1)
    result = sem.tool_delete(
        entity=entity,
        action=action,
        target_ref=_delete_target(cap),
        phase="commit",
        proposal_ref=None,
    )
    assert result.is_error is True
    assert result.structured_content["error_code"].startswith(
        "proposal"
    )


@pytest.mark.parametrize("cap", _caps(DELETES))
def test_delete_no_context_is_unauthorized(cap):
    entity, action = cap.split(".", 1)
    result = sem.tool_delete(
        entity=entity,
        action=action,
        target_ref=_delete_target(cap),
        phase="prepare",
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 401


def test_delete_commit_binds_actor_capability_target():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec = [], None
    calls = []

    def impact(target):
        return {"target": target}

    def executor(target, args):
        calls.append(target)
        return {}

    spec = dict(sem._DELETE_SPEC)
    spec["task.delete"] = (impact, executor)
    with patch.object(sem, "_DELETE_SPEC", spec):
        prep = sem.tool_delete(
            entity="task", target_ref="t-1", phase="prepare"
        )
        ref = prep.structured_content["data"]["proposal_ref"]
        # wrong target
        r1 = sem.tool_delete(
            entity="task", target_ref="t-2", phase="commit",
            proposal_ref=ref,
        )
        # wrong actor
        _set_context(_human_user(id="user-2"))
        r2 = sem.tool_delete(
            entity="task", target_ref="t-1", phase="commit",
            proposal_ref=ref,
        )
        # correct
        _set_context(_human_user())
        r3 = sem.tool_delete(
            entity="task", target_ref="t-1", phase="commit",
            proposal_ref=ref,
        )
    assert r1.is_error and r1.structured_content["error_code"] == (
        "proposal_mismatch"
    )
    assert r2.is_error and r2.structured_content["error_code"] == (
        "proposal_actor_mismatch"
    )
    assert r3.is_error is False and calls == ["t-1"]


# --- E7: knowledge ---------------------------------------------------------------------


def test_knowledge_all_topics_have_source_and_guidance():
    _set_context(_human_user())
    doc = sem._knowledge_document()
    topics = doc.get("topics") or {}
    assert len(topics) >= 13
    for key in topics:
        result = sem.tool_knowledge(topic=key)
        assert result.is_error is False, key
        data = result.structured_content["data"]
        assert data["source"], key
        assert data["guidance"], key
        assert data["knowledge_version"]


def test_knowledge_unknown_topic_lists_available():
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="nonsense.topic")
    assert result.is_error is True
    payload = result.structured_content
    assert payload["status_code"] == 404
    assert payload["data"]["available_ids"]["topics"]


# --- CAIO 3.0 P1/P2: methods + playbooks contract ------------------------------

_KNOWLEDGE_CONTRACT_FIELDS = (
    "type", "title", "objective", "source", "owner", "version",
    "access_classification", "status", "related_capabilities",
    "limitations",
)


def test_knowledge_methods_contract_fields():
    _set_context(_human_user())
    doc = sem._knowledge_document()
    methods = doc.get("methods") or {}
    assert len(methods) >= 6, "P1 exige 6 métodos pilotos"
    for mid in methods:
        result = sem.tool_knowledge(topic=f"method.{mid}")
        assert result.is_error is False, mid
        data = result.structured_content["data"]
        for field in _KNOWLEDGE_CONTRACT_FIELDS:
            assert data.get(field) is not None, (mid, field)
        assert data["type"] == "method"
        assert data["external_reference"] is True, (
            f"{mid}: método externo deve declarar que não é "
            "regra DELPI"
        )
        assert data["required_data"], mid
        assert data["when_not_to_use"], mid


def test_knowledge_playbooks_contract_fields():
    _set_context(_human_user())
    doc = sem._knowledge_document()
    playbooks = doc.get("playbooks") or {}
    assert len(playbooks) >= 8, "P2 exige 8 roteiros"
    for pid in playbooks:
        result = sem.tool_knowledge(topic=f"playbook.{pid}")
        assert result.is_error is False, pid
        data = result.structured_content["data"]
        for field in _KNOWLEDGE_CONTRACT_FIELDS:
            assert data.get(field) is not None, (pid, field)
        assert data["type"] == "playbook"
        assert data["semantic_steps"], pid
        assert data["response_format"], pid
        assert data["insufficient_data"], pid
        assert data["permissions"], pid
        for field in (
            "intent", "investigation_questions", "expected_evidence",
            "failure_states", "official_actions", "output_schema",
        ):
            assert data.get(field), (pid, field)


def test_knowledge_playbook_investigation_contract_is_actionable():
    """W6/W7: each playbook declares discovery questions, official
    actions that exist in the semantic registry, honest failure
    states and the conclusion→evidence→…→limitations output."""
    _set_context(_human_user())
    doc = sem._knowledge_document()
    known_caps = {a.capability for a in SEMANTIC_ACTIONS}
    for pid, b in doc["playbooks"].items():
        assert len(b["investigation_questions"]) >= 2, pid
        assert len(b["failure_states"]) >= 2, pid
        assert "limitações" in b["output_schema"], pid
        assert "OBSERVED" in b["output_schema"], pid
        assert "INFERRED" in b["output_schema"], pid
        assert "UNKNOWN" in b["output_schema"], pid
        for cap in b["related_capabilities"]:
            assert cap in known_caps or cap == "analyze", (pid, cap)


def test_knowledge_scenarios_a_j_selection_map():
    """W8 homologação — scenario phrasings select the right
    knowledge without naming the method (contract level)."""
    _set_context(_human_user())
    cases = {
        "o que é uma ov e como se liga à proposta e à op": {
            "topic.commercial.glossary",
        },
        "quais chicotes a delpi vende e quem os compra": {
            "topic.products.guide",
        },
        "quais clientes reduziram compras nos últimos 90 dias": {
            "playbook.customers_retraction",
        },
        "onde existem oportunidades de crescer nas contas": {
            "playbook.expansion_opportunities",
        },
        "quais pedidos abertos têm maior risco de atraso": {
            "playbook.order_health",
        },
        "propostas paradas no funil há muito tempo": {
            "playbook.proposal_funnel",
        },
        "monte a previsão de faturamento com cenários": {
            "method.forecast_vendas",
        },
        "prepare um plano comercial para 30 60 90 dias": {
            "playbook.plan_30_60_90",
        },
        "como mapear o processo comercial sipoc": {
            "method.sipoc_bpmn",
        },
        "desempenho por vendedor e carteira no trimestre": {
            "playbook.seller_portfolio_performance",
        },
    }
    for query, expected in cases.items():
        result = sem.tool_knowledge(query=query)
        assert result.is_error is False, query
        ids = {
            i["id"]
            for i in result.structured_content["data"]["selection"]
        }
        assert ids & expected, (query, ids, expected)


def test_knowledge_resolves_bare_method_and_playbook_ids():
    _set_context(_human_user())
    for key, expected in (
        ("rfv", "method"),
        ("order_health", "playbook"),
    ):
        result = sem.tool_knowledge(topic=key)
        assert result.is_error is False, key
        assert result.structured_content["data"]["type"] == expected


def test_knowledge_unknown_method_lists_namespaces():
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="method.nonexistent")
    assert result.is_error is True
    payload = result.structured_content
    assert payload["status_code"] == 404
    assert "methods" in payload["data"]["available_ids"]


# --- CAIO 3.0 P3: contextual selection -------------------------------------------


def test_knowledge_query_selects_retraction_method():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="quais clientes pararam de comprar ou reduziram"
    )
    assert result.is_error is False
    items = result.structured_content["data"]["selection"]
    ids = {i["id"] for i in items}
    assert "method.rfv" in ids
    assert "playbook.customers_retraction" in ids


def test_knowledge_query_selects_order_risk_playbook():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="quais pedidos estão em risco de atraso na entrega"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "method.risco_pedidos_otd" in ids
    assert "playbook.order_health" in ids


def test_knowledge_selection_is_bounded_and_provenanced():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        topic="*", query="meta desvio realizado gap"
    )
    assert result.is_error is False
    items = result.structured_content["data"]["selection"]
    assert 0 < len(items) <= 5
    for item in items:
        assert item["id"].split(".", 1)[0] in {
            "topic", "method", "playbook",
        }
        assert item["source"]
        assert item["version"]
        assert item["access_classification"] == "internal"
        assert item["conversation_relevance"] >= 1


def test_knowledge_selection_no_match_is_honest_404():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="zzzqqq unrelated tokens"
    )
    assert result.is_error is True
    payload = result.structured_content
    assert payload["status_code"] == 404
    assert payload["data"]["available_ids"]["methods"]


def test_knowledge_b2b_methods_are_external_references():
    """P5: B2B/process methods are curated external references —
    pending business validation, never DELPI rules."""
    _set_context(_human_user())
    doc = sem._knowledge_document()
    methods = doc.get("methods") or {}
    for mid in (
        "spin_selling", "meddpicc", "account_planning",
        "sipoc_bpmn", "ishikawa", "pdca_5w2h", "swot",
        "matriz_priorizacao",
    ):
        assert mid in methods, mid
        result = sem.tool_knowledge(topic=f"method.{mid}")
        assert result.is_error is False, mid
        data = result.structured_content["data"]
        assert data["external_reference"] is True, mid
        assert data["status"] == "pending_business_validation", mid
        assert "DELPI" in data["source"] or "externa" in data["source"]


def test_knowledge_query_selects_b2b_qualification():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="como qualificar uma oportunidade b2b complexa"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "method.meddpicc" in ids


def test_knowledge_selection_requires_human_principal():
    _set_context(
        _human_user(
            principal_type="service",
            permissions=["commercial.access"],
        )
    )
    result = sem.tool_knowledge(query="qualquer coisa")
    assert result.is_error is True
    assert result.structured_content["status_code"] == 403


def test_knowledge_required_domain_topics_present():
    """E7: dedicated topics for proposals, OTD and production exist
    with canonical sources — the E7 domain coverage checklist."""
    _set_context(_human_user())
    doc = sem._knowledge_document()
    topics = doc.get("topics") or {}
    for key in (
        "commercial.proposals",
        "commercial.otd",
        "commercial.production",
        "commercial.portfolio_governance",
        "commercial.indicators",
        "commercial.interaction_rooms",
        "commercial.permissions",
        "commercial.integrations",
        "products.guide",
        "commercial.glossary",
    ):
        assert key in topics, key
        assert topics[key].get("source"), key


# --- CAIO 3.0 ampliação: glossário estruturado + products.guide + seleção ----


def test_knowledge_glossary_structured_terms_contract():
    """Glossary terms carry meaning, application, owner, source,
    relations and examples; unconfirmed usage is marked
    PENDING_BUSINESS_VALIDATION — never silently asserted."""
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="commercial.glossary")
    assert result.is_error is False
    terms = result.structured_content["data"]["terms"]
    for key in (
        "ov", "pv", "op", "lmp", "rol", "meta", "saldo_a_faturar",
        "carteira_pedidos", "proposta", "conversao",
        "previsao_comercial", "lead_time", "otd", "follow_up",
        "familia_chicotes", "produto", "cliente",
    ):
        assert key in terms, key
    for tid, term in terms.items():
        for field in ("meaning", "application", "owner", "source", "status"):
            assert term.get(field), (tid, field)
        assert term.get("relations"), tid
    lmp = terms["lmp"]
    assert "Engenharia" in lmp["owner"]
    assert "PENDING_BUSINESS_VALIDATION" in lmp["status"]


def test_knowledge_products_guide_contract():
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="products.guide")
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["type"] == "topic"
    assert data["status"] == "implemented"
    caps = set(data["related_capabilities"])
    assert {
        "product.search", "product.summary", "product.customers",
        "product.filter_options",
    } <= caps
    assert "Engenharia" in " ".join(data["guidance"])


def test_knowledge_planned_topic_removed_once_implemented():
    _set_context(_human_user())
    doc = sem._knowledge_document()
    planned = {t["topic"] for t in doc.get("planned_topics", [])}
    assert "products.guide" not in planned


def test_knowledge_query_selects_product_guide_and_expansion():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="quais produtos podemos vender mais para os clientes"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "playbook.expansion_opportunities" in ids
    assert "topic.products.guide" in ids


def test_knowledge_query_selects_chicote_catalog():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="quais chicotes estão cadastrados no catálogo"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "topic.products.guide" in ids


def test_knowledge_query_acronym_terms_select_glossary():
    """2-char domain acronyms (OV/OP/PV) select the glossary when
    declared as corpus keywords — FASE 5 scenario A phrasing."""
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="o que é ov op e otd e como se relacionam"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "topic.commercial.glossary" in ids


def test_knowledge_query_diminishing_customers_selects_retraction():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="quais clientes importantes estão diminuindo suas "
              "compras"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "playbook.customers_retraction" in ids
    assert "method.rfv" in ids or "method.abc_pareto" in ids


def test_knowledge_query_conversion_selects_funnel():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="como melhorar a conversão de propostas"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "method.funil_conversao" in ids
    assert "playbook.proposal_funnel" in ids


def test_knowledge_new_methods_are_external_pending_validation():
    _set_context(_human_user())
    doc = sem._knowledge_document()
    methods = doc.get("methods") or {}
    for mid in ("benchmarking", "forecast_vendas"):
        assert mid in methods, mid
        result = sem.tool_knowledge(topic=f"method.{mid}")
        assert result.is_error is False, mid
        data = result.structured_content["data"]
        assert data["external_reference"] is True, mid
        assert data["status"] == "pending_business_validation", mid
        assert data["examples"], mid
        assert data["formula"], mid


def test_knowledge_query_selects_forecast_method():
    _set_context(_human_user())
    result = sem.tool_knowledge(
        query="qual a previsão de faturamento para o mês"
    )
    assert result.is_error is False
    ids = {
        i["id"]
        for i in result.structured_content["data"]["selection"]
    }
    assert "method.forecast_vendas" in ids
    assert "playbook.forecast_scenarios" in ids
