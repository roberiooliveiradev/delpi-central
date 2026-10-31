"""Cycle-3/5 contract tests — Task 19 iterative reliability.

Trace-proven defects covered here:

- ``_build_arguments`` died on the first schema-rejected proposal —
  the 4B repeatedly appends invented optional fields (``page_size``,
  ``date_from``…) that ``validate_arguments`` must still reject. A
  bounded re-proposal now runs once on model-side failure; typed
  validation remains the gate and undeclared keys still invalidate.
- ``_select_candidate`` failed closed on a malformed model proposal
  (``{"applicable": null, "action_id": ""}`` observed on the 4B) —
  a bounded retry now runs once; an explicit ``applicable: false``
  stays a terminal no-match.
- The ``select_candidate`` instruction permitted ``null`` for
  ``applicable`` — v33 requires a strict boolean so the model cannot
  mirror a null back.
"""

from __future__ import annotations

import json
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "config",
    "orchestration_instructions.delpi.json",
)


def _instruction(name: str) -> str:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["instructions"][name]


# ---------- _build_arguments: bounded re-proposal on schema rejection ----------


def _arguments_orchestrator(proposals):
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _group,
        _outcome,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    group = _group("pa", "alpha", [_query_cap()])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    model = FakeProposalModel(list(proposals))
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, model, provider, group


def test_build_arguments_retries_on_schema_rejection():
    """Invented undeclared keys still invalidate the proposal — but
    the bounded retry lets a clean second proposal through."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )

    orch, model, provider, group = _arguments_orchestrator(
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "tubo", "injected": "x"}
                }
            },
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "tubo"}
                }
            },
        ]
    )
    descriptor = group.capabilities[0]
    validated, missing = orch._build_arguments(
        "busque tubo", descriptor, correlation="c"
    )
    assert validated == {"query": "tubo"}
    assert missing == ()


def test_build_arguments_still_fails_closed_on_persistent_noise():
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )

    orch, model, provider, group = _arguments_orchestrator(
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "tubo", "injected": "x"}
                }
            },
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"other_injected": "y"}
                }
            },
        ]
    )
    descriptor = group.capabilities[0]
    validated, _missing = orch._build_arguments(
        "busque tubo", descriptor, correlation="c"
    )
    assert validated is None


def test_build_arguments_null_literal_dropped_before_validation():
    """A literal ``"None"`` value is a model serialization artifact —
    dropping it pre-validation surfaces the required key as a missing
    input (resolver/clarify), never as an owner call with 'None'."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )

    orch, model, provider, group = _arguments_orchestrator(
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "None"}
                }
            },
        ]
    )
    descriptor = group.capabilities[0]
    validated, missing = orch._build_arguments(
        "busque tubo", descriptor, correlation="c"
    )
    # The marker is dropped before validation — the owner sees a clean
    # argument set, never the literal "None" string.
    assert validated == {}
    assert len(model.requests) == 1


def test_build_arguments_null_value_dropped_before_validation():
    """A real JSON ``null`` value is the same serialization artifact —
    dropped pre-validation like the string marker."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )

    orch, model, provider, group = _arguments_orchestrator(
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": None}
                }
            },
        ]
    )
    descriptor = group.capabilities[0]
    validated, missing = orch._build_arguments(
        "busque tubo", descriptor, correlation="c"
    )
    assert validated == {}
    assert len(model.requests) == 1


def test_build_arguments_declared_missing_not_retried():
    """A proposal that declares missing inputs without arguments is a
    semantic terminal — exactly one model call, no retry."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )

    orch, model, provider, group = _arguments_orchestrator(
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "missing_inputs": ["item_id"],
                    "arguments": None,
                }
            },
        ]
    )
    descriptor = group.capabilities[0]
    validated, missing = orch._build_arguments(
        "mostre o item", descriptor, correlation="c"
    )
    assert validated is None
    assert "item_id" in missing
    assert len(model.requests) == 1


# ---------- select_candidate bounded retry ----------


def _candidate_selection_orchestrator(proposals):
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _group,
        _outcome,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    group = _group("pa", "alpha", [_query_cap()])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    model = FakeProposalModel(list(proposals))
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, model


_CANDIDATES = [
    {
        "action_id": "search_items",
        "description": "Search items",
        "candidate_token": "tok-1",
    },
    {
        "action_id": "get_stock",
        "description": "Stock",
        "candidate_token": "tok-2",
    },
]


def test_select_candidate_retries_after_malformed_output():
    orch, _model = _candidate_selection_orchestrator(
        [
            {"applicable": None, "action_id": ""},  # observed 4B shape
            {"applicable": True, "action_id": "search_items"},
        ]
    )
    result = orch._select_candidate(
        _CANDIDATES, "traga exemplos de terminal", correlation="c"
    )
    assert result is not None
    assert result["action_id"] == "search_items"


def test_select_candidate_explicit_false_is_terminal():
    orch, model = _candidate_selection_orchestrator(
        [{"applicable": False, "action_id": None}]
    )
    assert (
        orch._select_candidate(_CANDIDATES, "q", correlation="c") is None
    )
    # explicit decline — exactly one model call, no retry
    assert len(model.requests) == 1


def test_select_candidate_all_malformed_fails_closed():
    orch, model = _candidate_selection_orchestrator(
        [
            {"applicable": None, "action_id": ""},
            {"unexpected": True},
        ]
    )
    assert (
        orch._select_candidate(_CANDIDATES, "q", correlation="c") is None
    )
    assert len(model.requests) == 2  # bounded — at most one retry


def test_candidate_dead_end_requires_missing_identifier():
    """A candidate requiring an identifier the request never supplies
    is a dead end — same exclusion rule as the resolver stage."""
    from app.application.capability_provision.orchestration import (
        _candidate_needs_missing_identifier,
    )

    id_required = {"action_id": "get_stock", "required_arguments": ["code"]}
    no_required = {"action_id": "search_items", "required_arguments": []}

    assert _candidate_needs_missing_identifier(
        id_required, "traga três exemplos de terminal bala"
    )
    assert not _candidate_needs_missing_identifier(
        no_required, "traga três exemplos de terminal bala"
    )
    # a request that literally carries an identifier keeps the candidate
    assert not _candidate_needs_missing_identifier(
        id_required, "mostre o produto 10080092"
    )
    assert not _candidate_needs_missing_identifier(
        id_required, "detalhes do processo PROC-0105"
    )
    # non-identifier required args never mark a dead end
    assert not _candidate_needs_missing_identifier(
        {"required_arguments": ["description"]}, "busque tubo"
    )


def test_select_candidate_instruction_requires_strict_boolean():
    text = _instruction(
        "delia.capability_orchestration.select_candidate"
    ).lower()
    assert "strictly a boolean" in text
    assert "never null" in text


# ---------- Cycle 6: resolver viability + named-provider + id-retry ----------


def _resolver_group():
    from tests.test_goal_evidence_relevance import _cap, _group
    from app.domain.specialist_interop.model import (
        SpecialistOperationClass,
    )

    target = _cap(
        "alpha",
        "mcp",
        "get_process_timeline",
        schema={
            "type": "object",
            "required": ["process_id"],
            "properties": {"process_id": {"type": "string"}},
        },
    )
    record = _cap(
        "alpha",
        "mcp",
        "record_read",
        schema={
            "type": "object",
            "required": ["action", "entity"],
            "properties": {
                "action": {"type": "string"},
                "entity": {"type": "string"},
            },
        },
    )
    catalog = _cap(
        "alpha",
        "mcp",
        "get_catalog",
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    context = _cap(
        "alpha",
        "mcp",
        "get_process_context",
        schema={
            "type": "object",
            "required": ["process_id"],
            "properties": {"process_id": {"type": "string"}},
        },
    )
    group = _group("pa", "alpha", [target, record, catalog, context])
    return group, target, record


def _resolver_orchestrator(proposals):
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _outcome,
        FakeProposalModel,
        FakeProvider,
    )

    group, _target, _record = _resolver_group()
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "record_read"): _outcome("ok")},
    )
    clause = _cri_clause()
    model = FakeProposalModel(list(proposals))
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, model, group


def test_resolver_single_viable_still_model_proposal():
    """Dead-end/discovery exclusions leave exactly one viable
    resolver — but resolver selection is a declared bounded model
    proposal: the sole viable candidate still goes through the
    proposal stage and the model's pick is returned."""
    orch, model, group = _resolver_orchestrator(
        [{"applicable": True, "remote_name": "record_read"}]
    )
    _g, target, record = _resolver_group()
    picked = orch._select_resolver(
        "qual o último processo?",
        target,
        ("process_id",),
        group,
        None,
        (),
        "corr",
        None,
    )
    assert picked.remote_name == "record_read"
    assert len(model.requests) == 1


def test_resolver_dead_end_and_discovery_excluded():
    """Two dead ends remain excluded when a non-identifier input is
    missing — discovery stays eligible for non-id resolution."""
    orch, model, group = _resolver_orchestrator(
        [{"applicable": True, "remote_name": "record_read"}]
    )
    _g, target, record = _resolver_group()
    picked = orch._select_resolver(
        "qual o último processo?",
        target,
        ("entity",),
        group,
        None,
        (),
        "corr",
        None,
    )
    assert picked is record or picked.remote_name == "record_read"
    assert len(model.requests) == 1


def test_select_group_named_absent_provider_not_applicable():
    """'use o mcp sap' names a provider no live group owns — the
    declared clause is enforced before the model is ever asked."""
    from tests.test_goal_evidence_relevance import _group, _query_cap

    orch, model, _g = _resolver_orchestrator([])
    groups = {"pa:alpha": _group("pa", "alpha", [_query_cap()])}
    status, key = orch._select_group(
        "use o mcp sap para consultar produtos", groups
    )
    assert (status, key) == ("not_applicable", None)
    assert len(model.requests) == 0


def test_select_group_named_live_provider_still_consults_model():
    from tests.test_goal_evidence_relevance import _group, _query_cap
    from app.application.capability_provision.orchestration import (
        GROUP_SELECTION_INSTRUCTION_ID,
    )

    orch, _model, _g = _resolver_orchestrator(
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "pa:alpha",
                }
            }
        ]
    )
    groups = {"pa:alpha": _group("pa", "alpha", [_query_cap()])}
    status, key = orch._select_group(
        "use o mcp alpha para consultar itens", groups
    )
    assert (status, key) == ("selected", "pa:alpha")


def test_select_capability_retries_identifier_requiring_pick():
    """Picking a capability whose required identifier the request
    never supplies violates the declared clause — one bounded
    re-proposal may select an executable alternative."""
    from app.application.capability_provision.orchestration import (
        CAPABILITY_SELECTION_INSTRUCTION_ID,
    )

    orch, model, group = _resolver_orchestrator(
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "get_process_timeline",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "record_read",
                }
            },
        ]
    )
    status, descriptor = orch._select_capability(
        "qual o último processo?", group
    )
    assert status == "selected"
    assert descriptor.remote_name == "record_read"
    assert len(model.requests) == 2


def test_select_capability_literal_identifier_no_retry():
    """A request that literally carries an identifier does not
    trigger the clause retry — the pick stands on one proposal."""
    from app.application.capability_provision.orchestration import (
        CAPABILITY_SELECTION_INSTRUCTION_ID,
    )

    orch, model, group = _resolver_orchestrator(
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "get_process_timeline",
                }
            },
        ]
    )
    status, descriptor = orch._select_capability(
        "mostre o processo PROC-0105", group
    )
    assert status == "selected"
    assert descriptor.remote_name == "get_process_timeline"
    assert len(model.requests) == 1


# ---------- selection dead-end: orchestrator-supplied required input ----------


def _token_bound_group():
    from tests.test_goal_evidence_relevance import _cap, _group
    from app.domain.specialist_interop.model import (
        SpecialistOperationClass,
    )

    execute = _cap(
        "alpha",
        "mcp",
        "execute_information",
        schema={
            "type": "object",
            "required": ["candidate_token", "arguments"],
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {"type": "object"},
            },
        },
    )
    discover = _cap(
        "alpha",
        "mcp",
        "discover_information",
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    record = _cap(
        "alpha",
        "mcp",
        "record_read",
        schema={
            "type": "object",
            "required": ["action", "entity"],
            "properties": {
                "action": {"type": "string"},
                "entity": {"type": "string"},
            },
        },
    )
    return _group("pa", "alpha", [execute, discover, record])


def _token_bound_orchestrator(proposals):
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _outcome,
        FakeProposalModel,
        FakeProvider,
    )

    group = _token_bound_group()
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "record_read"): _outcome("ok")},
    )
    clause = _cri_clause()
    model = FakeProposalModel(list(proposals))
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, model, group


def test_orchestrated_input_dead_end_predicate():
    """``required ∩ ORCHESTRATED_FIELDS`` marks the capability as a
    typed dead-end; ordinary required business fields do not."""
    from app.application.capability_provision.orchestration import (
        _capability_dead_end,
        _capability_requires_orchestrated_input,
    )
    from tests.test_goal_evidence_relevance import _cap

    token_bound = _cap(
        "alpha",
        "mcp",
        "execute_information",
        schema={
            "type": "object",
            "required": ["candidate_token", "arguments"],
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {"type": "object"},
            },
        },
    )
    ordinary = _cap(
        "alpha",
        "mcp",
        "record_read",
        schema={
            "type": "object",
            "required": ["action", "entity"],
            "properties": {
                "action": {"type": "string"},
                "entity": {"type": "string"},
            },
        },
    )
    assert _capability_requires_orchestrated_input(token_bound)
    assert _capability_dead_end(token_bound, "buscar um fusível")
    assert not _capability_requires_orchestrated_input(ordinary)
    assert not _capability_dead_end(ordinary, "buscar um fusível")


def test_select_capability_retries_orchestrated_input_pick():
    """Picking a capability that requires orchestrator-issued state
    (``candidate_token``) violates the same dead-end clause as a
    missing-identifier pick — the token only exists after owner
    discovery, so one bounded re-proposal selects the executable
    alternative."""
    from app.application.capability_provision.orchestration import (
        CAPABILITY_SELECTION_INSTRUCTION_ID,
    )

    orch, model, group = _token_bound_orchestrator(
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "execute_information",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "discover_information",
                }
            },
        ]
    )
    status, descriptor = orch._select_capability(
        "traga dois exemplos de fusível cadastrado", group
    )
    assert status == "selected"
    assert descriptor.remote_name == "discover_information"
    assert len(model.requests) == 2


def test_select_capability_orchestrated_pick_stands_without_alternative():
    """When every listed capability is a dead-end, no executable
    alternative exists — the first pick stands (fail-closed path
    reports the honest limitation downstream)."""
    from app.application.capability_provision.orchestration import (
        CAPABILITY_SELECTION_INSTRUCTION_ID,
    )
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cap,
        _cri_clause,
        _group,
        FakeProposalModel,
        FakeProvider,
    )

    execute = _cap(
        "alpha",
        "mcp",
        "execute_information",
        schema={
            "type": "object",
            "required": ["candidate_token", "arguments"],
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {"type": "object"},
            },
        },
    )
    group = _group("pa", "alpha", [execute])
    provider = FakeProvider("pa", [group], outcomes={})
    clause = _cri_clause()
    model = FakeProposalModel(
        [
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "execute_information",
                }
            }
        ]
    )
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    status, descriptor = orch._select_capability(
        "traga dois exemplos de fusível cadastrado", group
    )
    assert status == "selected"
    assert descriptor.remote_name == "execute_information"
    assert len(model.requests) == 1


def test_v35_instruction_clauses_present():
    turn_goal = _instruction(
        "delia.capability_orchestration.turn_goal"
    ).lower()
    assert "canonical designation" in turn_goal
    assert "terminais bala" in turn_goal
    admission = _instruction(
        "delia.capability_orchestration.interaction_admission"
    ).lower()
    assert "compare x com y" in admission
    assert "quantos deles" in admission


def test_v36_instruction_clauses_present():
    """v36 — Task 21 trace-proven clauses:
    (a) the args contract declares the DISCOVERY surface carries the
    natural-language information need (operation_class keyed);
    (b) the with_goal subject rule excludes domain-state qualifiers
    the same way turn_goal already did."""
    arguments = _instruction(
        "delia.capability_orchestration.arguments"
    ).lower()
    assert "operation_class is discovery" in arguments
    assert "information need" in arguments
    with_goal = _instruction(
        "delia.capability_orchestration.select_capability#with_goal"
    ).lower()
    assert "domain-state qualifiers" in with_goal
    assert "cabo flexível cadastrado" in with_goal


# ---------- admission: surface_inquiry contradiction guard ----------


def _admission_orchestrator(proposals, model=None):
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cri_clause,
        _group,
        _outcome,
        _query_cap,
        FakeProposalModel,
        FakeProvider,
    )

    group = _group("pa", "alpha", [_query_cap()])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    if model is None:
        model = FakeProposalModel(list(proposals))
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, model


def test_admission_surface_inquiry_persistent_contradiction_lists():
    """The instruction defines surface_inquiry as requires=false — a
    true flag in the same proposal is a declared contradiction. One
    bounded retry runs; if the contradiction persists, the typed
    class wins — the deterministic surface listing never fabricates
    business facts."""
    from app.application.capability_provision.orchestration import (
        INTERACTION_ADMISSION_INSTRUCTION_ID,
    )
    from app.application.interaction.turn_budget import TurnDeadline

    orch, model = _admission_orchestrator([])
    model._last[INTERACTION_ADMISSION_INSTRUCTION_ID] = {
        "interaction_class": "surface_inquiry",
        "requires_owner_surface": True,
    }
    cls, owner = orch._admit_conversational_turn(
        "Use o TÉO para consultar o processo PROC-0105",
        workspace_context=None,
        prior_turns=(),
        correlation="c",
        deadline=TurnDeadline.start(30.0),
    )
    assert cls == "surface_inquiry"
    assert owner is True


def test_admission_contradiction_retry_restores_surface_listing():
    """A contradictory admission proposal gets one bounded retry —
    a coherent retry (surface_inquiry + requires=false) restores the
    live-surface listing."""
    from app.application.capability_provision.orchestration import (
        INTERACTION_ADMISSION_INSTRUCTION_ID,
    )
    from app.application.interaction.turn_budget import TurnDeadline
    from app.application.model_invocation.contracts import (
        ProviderInvocationPayload,
    )
    from tests.test_goal_evidence_relevance import FakeProposalModel

    class _AdmissionSeq(FakeProposalModel):
        def __init__(self, seq):
            super().__init__([])
            self._seq = list(seq)

        def invoke(self, request):
            self.requests.append(request)
            return ProviderInvocationPayload(
                structured_output=self._seq.pop(0),
                generated_at="2026-01-01T00:00:00+00:00",
            )

    seq_model = _AdmissionSeq(
        [
            {
                "interaction_class": "surface_inquiry",
                "requires_owner_surface": True,
            },
            {
                "interaction_class": "surface_inquiry",
                "requires_owner_surface": False,
            },
        ]
    )
    orch, _model = _admission_orchestrator([], model=seq_model)
    cls, owner = orch._admit_conversational_turn(
        "quais ferramentas você tem disponíveis?",
        workspace_context=None,
        prior_turns=(),
        correlation="c",
        deadline=TurnDeadline.start(30.0),
    )
    assert cls == "surface_inquiry"
    assert owner is True
    assert len(seq_model.requests) == 2


def test_admission_surface_inquiry_requires_false_lists_surface():
    """A coherent surface_inquiry (requires=false) still answers with
    the deterministic live-surface listing."""
    from app.application.capability_provision.orchestration import (
        INTERACTION_ADMISSION_INSTRUCTION_ID,
    )
    from app.application.interaction.turn_budget import TurnDeadline

    orch, model = _admission_orchestrator([])
    model._last[INTERACTION_ADMISSION_INSTRUCTION_ID] = {
        "interaction_class": "surface_inquiry",
        "requires_owner_surface": False,
    }
    cls, owner = orch._admit_conversational_turn(
        "quais especialistas você pode consultar?",
        workspace_context=None,
        prior_turns=(),
        correlation="c",
        deadline=TurnDeadline.start(30.0),
    )
    assert cls == "surface_inquiry"
    assert owner is True


# ---------- workspace entity refs: identifier resolvability ----------


def test_candidate_dead_end_workspace_literal_resolves():
    """A candidate requiring an identifier is executable when the
    declared workspace entity supplies a resolvable literal — the
    ref only widens the executable set; selection stays model."""
    from app.application.capability_provision.orchestration import (
        _candidate_needs_missing_identifier,
        _workspace_identifier_literals,
    )
    from app.application.interaction.workspace_context import (
        WorkspaceContext,
        WorkspaceEntityRef,
    )

    candidate = {"required_arguments": ["product_id"]}
    ctx = WorkspaceContext(
        host_app_id="public-hub",
        route="/apps/public-hub/catalogo",
        view_ref="product-detail",
        entity_refs=(
            WorkspaceEntityRef(
                entity_type="product",
                entity_id="80002437",
                source_system="delpi",
                label="produto selecionado",
            ),
        ),
    )
    literals = _workspace_identifier_literals(ctx)
    assert "80002437" in literals
    assert not _candidate_needs_missing_identifier(
        candidate, "mostre detalhes do produto", literals
    )
    # sibling: no workspace → same candidate is a dead-end
    assert _candidate_needs_missing_identifier(
        candidate, "mostre detalhes do produto"
    )
    # negative: unrelated workspace entity type still supplies the
    # literal only when it is identifier-shaped — a label without
    # entity_id contributes nothing
    ctx_empty = WorkspaceContext(
        host_app_id="public-hub",
        route="/r",
        view_ref="v",
        entity_refs=(),
    )
    assert _workspace_identifier_literals(ctx_empty) == ""



# ---------- discovery reformulation: zero-candidate bounded retry ----------


def _discovery_chain_orchestrator(discovery_outcomes, proposals):
    from tests.test_governed_attempt_contract import build_engine
    from tests.test_goal_evidence_relevance import (
        _cap,
        _cri_clause,
        _group,
        _outcome,
        FakeProposalModel,
        FakeProvider,
    )
    from app.domain.specialist_interop.model import (
        SpecialistOperationClass,
    )

    discover = _cap(
        "alpha",
        "mcp",
        "discover_information",
        op_class=SpecialistOperationClass.DISCOVERY,
        schema={
            "type": "object",
            "required": ["query"],
            "properties": {"query": {"type": "string"}},
        },
    )
    execute = _cap(
        "alpha",
        "mcp",
        "execute_information",
        schema={
            "type": "object",
            "required": ["candidate_token", "arguments"],
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {"type": "object"},
            },
        },
    )
    group = _group("pa", "alpha", [discover, execute])
    provider = FakeProvider(
        "pa",
        [group],
        outcomes={
            ("alpha", "discover_information"): list(discovery_outcomes),
            ("alpha", "execute_information"): _outcome(
                '[{"code": "301"}]'
            ),
        },
    )
    clause = _cri_clause()
    model = FakeProposalModel(list(proposals))
    orch = build_engine(
        "delia",
        providers=[provider],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orch, model, provider, group


_DISCOVERY_CANDIDATES = {
    "candidates": [
        {
            "action_id": "search_products",
            "candidate_token": "tok-owner-1",
            "argument_schema": {
                "type": "object",
                "required": ["description"],
                "properties": {"description": {"type": "string"}},
            },
            "required_arguments": ["description"],
        }
    ]
}


def test_discovery_zero_candidates_reformulates_once():
    """Zero-candidate discovery re-proposes the need once with the
    typed owner signal; the reformulated query surfaces the
    owner-issued candidate and the chain executes."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )
    from tests.test_goal_evidence_relevance import _outcome

    orch, model, provider, group = _discovery_chain_orchestrator(
        [
            _outcome("{}", structured={"candidates": []}),
            _outcome("{}", structured=_DISCOVERY_CANDIDATES),
        ],
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "buscar fita isolante"}
                }
            },
            {"arguments": {"description": "fita isolante"}},
        ],
    )
    result = orch._invoke_selected(
        "pa:alpha",
        "discover_information",
        {"query": "existe fita isolante?"},
        group,
        "existe fita isolante cadastrada?",
        "corr-reform",
    )
    assert result is not None
    outcome, action_id, used = result
    assert action_id == "search_products"
    assert used == "execute_information"
    names = [c[0] for c in provider.calls]
    assert names == [
        "discover_information",
        "discover_information",
        "execute_information",
    ]
    exec_args = provider.calls[-1][1]
    assert exec_args["candidate_token"] == "tok-owner-1"
    assert exec_args["arguments"] == {"description": "fita isolante"}


def test_discovery_identical_reformulation_no_second_invoke():
    """A reformulation identical to the first proposal cannot change
    the owner answer — no second invoke, fail-closed terminal."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )
    from tests.test_goal_evidence_relevance import _outcome

    orch, model, provider, group = _discovery_chain_orchestrator(
        [
            _outcome("{}", structured={"candidates": []}),
            _outcome("{}", structured=_DISCOVERY_CANDIDATES),
        ],
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "existe fita isolante?"}
                }
            },
        ],
    )
    result = orch._invoke_selected(
        "pa:alpha",
        "discover_information",
        {"query": "existe fita isolante?"},
        group,
        "existe fita isolante cadastrada?",
        "corr-reform2",
    )
    names = [c[0] for c in provider.calls]
    assert names == ["discover_information"]


# ---------- discovery reformulation: unresolvable-candidate retry ----------


_DETAIL_CANDIDATES = {
    "candidates": [
        {
            "action_id": "get_product_detail",
            "candidate_token": "tok-detail-1",
            "required_arguments": ["code"],
        },
        {
            "action_id": "get_product_drawing",
            "candidate_token": "tok-drawing-1",
            "required_arguments": ["code"],
        },
    ]
}

_DETAIL_SINGLE = {
    "candidates": [
        {
            "action_id": "get_product_detail",
            "candidate_token": "tok-detail-1",
            "required_arguments": ["code"],
        }
    ]
}


def test_discovery_detail_only_candidates_reformulate():
    """A discovery result whose only candidates are identifier-gated
    detail actions can never execute for an identifier-less ask —
    the resolution fails closed and the bounded reformulation
    restates the need, surfacing the collection action."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )
    from tests.test_goal_evidence_relevance import _outcome

    orch, model, provider, group = _discovery_chain_orchestrator(
        [
            _outcome("{}", structured=_DETAIL_CANDIDATES),
            _outcome("{}", structured=_DISCOVERY_CANDIDATES),
        ],
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "query": "buscar produtos por descrição "
                        "espaguete"
                    }
                }
            },
            {"arguments": {"description": "espaguete"}},
        ],
    )
    result = orch._invoke_selected(
        "pa:alpha",
        "discover_information",
        {"query": "detalhes do produto espaguete"},
        group,
        "traga um espaguete termorretrátil",
        "corr-detaildead",
    )
    assert result is not None
    outcome, action_id, used = result
    assert action_id == "search_products"
    assert used == "execute_information"
    names = [c[0] for c in provider.calls]
    assert names == [
        "discover_information",
        "discover_information",
        "execute_information",
    ]


def test_discovery_single_dead_candidate_reformulates():
    """Sibling: the single-candidate fast path honors the same
    dead-end exclusion — a lone identifier-gated candidate is as
    unresolvable as a dead pick inside a multi-candidate set."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )
    from tests.test_goal_evidence_relevance import _outcome

    orch, model, provider, group = _discovery_chain_orchestrator(
        [
            _outcome("{}", structured=_DETAIL_SINGLE),
            _outcome("{}", structured=_DISCOVERY_CANDIDATES),
        ],
        [
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {
                        "query": "buscar produtos por descrição "
                        "espaguete"
                    }
                }
            },
            {"arguments": {"description": "espaguete"}},
        ],
    )
    result = orch._invoke_selected(
        "pa:alpha",
        "discover_information",
        {"query": "detalhes do produto espaguete"},
        group,
        "traga um espaguete termorretrátil",
        "corr-singledead",
    )
    assert result is not None
    outcome, action_id, used = result
    assert used == "execute_information"
    names = [c[0] for c in provider.calls]
    assert names == [
        "discover_information",
        "discover_information",
        "execute_information",
    ]


def test_discovery_dead_candidate_stated_identifier_chains():
    """Negative: when the request DOES state an identifier literal,
    the same detail candidate is executable — no reformulation, the
    chain proceeds directly."""
    from app.application.capability_provision.orchestration import (
        ARGUMENTS_INSTRUCTION_ID,
    )
    from tests.test_goal_evidence_relevance import _outcome

    orch, model, provider, group = _discovery_chain_orchestrator(
        [
            _outcome("{}", structured=_DETAIL_SINGLE),
        ],
        [
            {"arguments": {"code": "80002437"}},
        ],
    )
    result = orch._invoke_selected(
        "pa:alpha",
        "discover_information",
        {"query": "detalhes do produto código 80002437"},
        group,
        "detalhes do produto código 80002437",
        "corr-detailok",
    )
    assert result is not None
    outcome, action_id, used = result
    assert action_id == "get_product_detail"
    assert used == "execute_information"
    names = [c[0] for c in provider.calls]
    assert names == ["discover_information", "execute_information"]
