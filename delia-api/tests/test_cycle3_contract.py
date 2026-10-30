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
