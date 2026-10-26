"""DELIA-C3 — evidence & schema projection integrity (bounded rework).

Follow-on to the C2 selection-envelope fix. The independent review of
document 152 (§11) identified the same defect class outside selection:
``json.dumps(...)[:MAX_*]`` on structured stage payloads could sever
JSON mid-document, bisect a record/schema, or silently drop required
fields — the model would receive a syntactically invalid envelope or
apparently-complete-but-partial evidence.

These tests freeze the contract for every proven site:

- every stage block is always valid JSON — no mid-document cut;
- ``input_schema`` / ``schema`` is emitted whole (argument contract);
- required identifiers, record fields and provenance survive intact;
- bounded evidence excerpts shrink structurally before anything else;
- trailing omissions are truthfully marked (``*_omitted`` counts);
- when immutable mandatory content cannot fit the budget, the payload
  emits whole — the typed CONTEXT_TOO_LARGE boundary stays the guard,
  never a corrupt envelope.
"""

from __future__ import annotations

import json

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CANDIDATE_ARGUMENTS_INSTRUCTION_ID,
    CLARIFICATION_INSTRUCTION_ID,
    CONTINUATION_INSTRUCTION_ID,
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    INDEX_PROBE_INSTRUCTION_ID,
    INDEX_SELECT_INSTRUCTION_ID,
    MAX_ARGUMENTS_BLOCK_CHARS,
    MAX_RELEVANCE_EVIDENCE_CHARS,
    MAX_SURFACE_CHARS,
    RESOLVER_SELECTION_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _drop_block_fields,
    _fit_json_block,
    _json_block,
    _omit_tail_entries,
    _truncate_entry_field,
    _truncate_text_field,
)
from app.application.capability_provision.outcome_assessment import (
    EvidenceFacts,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from tests.conftest import load_test_orchestration_instructions

TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)


class _CaptureModel:
    """Captures every request; proposals are intentionally absent so
    stages degrade honestly — these tests assert transport integrity,
    not proposal semantics."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposals=None):
        self.requests = []
        self._proposals = dict(proposals or {})

    def invoke(self, request):
        self.requests.append(request)
        return ProviderInvocationPayload(
            structured_output=self._proposals.get(
                request.task_purpose_id
            ),
            generated_at="2026-01-01T00:00:00+00:00",
        )


def _orchestrator() -> tuple[OperationalCapabilityOrchestrator, _CaptureModel]:
    model = _CaptureModel()
    return (
        OperationalCapabilityOrchestrator(
            [],
            invoke_model=InvokeModel(model),
            model_ref=TEST_MODEL_REF,
            orchestration_instructions=(
                load_test_orchestration_instructions()
            ),
        ),
        model,
    )


def _deadline() -> TurnDeadline:
    clock = [1000.0]
    return TurnDeadline(ends_at=clock[0] + 25.0, clock=lambda: clock[0])


def _block(model, purpose: str, tag: str) -> str:
    """Raw inner payload of the captured request for ``purpose``."""
    for request in model.requests:
        if request.task_purpose_id == purpose:
            return request.input_text.split(f"<{tag}>", 1)[1].split(
                f"</{tag}>", 1
            )[0]
    raise AssertionError(f"no captured request for {purpose}")


def _cap(
    name: str,
    *,
    desc_len: int = 40,
    schema=None,
    op_class=None,
    group_id: str = "alpha",
) -> ProviderCapability:
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id="mcp",
        remote_name=name,
        owner=group_id,
        operation_class=op_class or SpecialistOperationClass.READ,
        description="d" * desc_len,
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _group(caps, group_id: str = "alpha") -> CapabilityGroup:
    return CapabilityGroup(
        provider_id="mcp",
        group_id=group_id,
        owner_ref=group_id,
        display_name=group_id,
        capabilities=tuple(caps),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=group_id,
        ),
    )


def _outcome(structured) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="mcp:alpha",
            remote_name="search_items",
            protocol=InteropProtocol.MCP,
            correlation_id="corr-proj",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="ok",
        is_complete=True,
        structured=structured,
        limitations=(),
    )


_FAT_SCHEMA = {
    "type": "object",
    "properties": {
        f"field_{i}": {
            "type": "string",
            "description": "d" * 300,
            "enum": [f"option_{i}_{j}" for j in range(20)],
        }
        for i in range(40)
    },
    "required": ["field_0"],
}

# Sized to exceed the arguments projection budget
# (MAX_ARGUMENTS_BLOCK_CHARS) while staying under the transport
# input bound — proves the payload emits WHOLE, never severed.
_BIG_SCHEMA = {
    "type": "object",
    "properties": {
        f"field_{i}": {
            "type": "string",
            "description": "d" * 450,
        }
        for i in range(30)
    },
    "required": ["field_0"],
}


# ---------------------------------------------------------------------------
# structural-fit helpers
# ---------------------------------------------------------------------------


def test_fit_json_block_small_payload_unchanged():
    block = {"a": 1, "items": [{"id": "x"}]}
    payload = _fit_json_block(block, MAX_SURFACE_CHARS)
    assert json.loads(payload) == block


def test_fit_json_block_ladder_shrinks_then_omits():
    block = {
        "notes": "n" * 5000,
        "records": [{"id": f"r{i}", "v": "v" * 900} for i in range(10)],
    }
    payload = _fit_json_block(
        block,
        MAX_SURFACE_CHARS,
        lambda: _truncate_text_field(block, "notes", 256),
        lambda: _omit_tail_entries(block, "records", "records_omitted"),
    )
    data = json.loads(payload)
    assert len(payload) <= MAX_SURFACE_CHARS
    assert len(data["notes"]) == 256
    omitted = data.get("records_omitted", 0)
    assert len(data["records"]) + omitted == 10


def test_fit_json_block_exhausted_emits_minimal_valid_document():
    """Immutable content that cannot fit emits whole valid JSON —
    never a mid-document cut; the typed boundary remains the guard."""
    block = {"schema": _FAT_SCHEMA, "capability": "cap"}
    payload = _fit_json_block(block, 500)
    assert len(payload) > 500
    assert json.loads(payload)["schema"] == _FAT_SCHEMA


def test_fit_json_block_unicode_escapes_roundtrip():
    block = {"text": 'açúcar "quoted" \\ \n çñü', "n": 1}
    payload = _fit_json_block(block, MAX_SURFACE_CHARS)
    assert json.loads(payload) == block


def test_truncate_text_field_bounds_in_place():
    block = {"desc": "d" * 100, "other": 5}
    assert _truncate_text_field(block, "desc", 10) is True
    assert block["desc"] == "d" * 10
    assert _truncate_text_field(block, "desc", 10) is False
    assert _truncate_text_field(block, "missing", 10) is False
    assert _truncate_text_field(block, "other", 1) is False


def test_truncate_entry_field_bounds_all_entries():
    block = {"items": [{"d": "x" * 50}, {"d": "y" * 5}]}
    assert _truncate_entry_field(block, "items", "d", 10) is True
    assert block["items"] == [{"d": "x" * 10}, {"d": "y" * 5}]
    assert _truncate_entry_field(block, "items", "d", 10) is False


def test_drop_block_fields_only_counts_present():
    block = {"a": 1, "b": None}
    assert _drop_block_fields(block, "a") is True
    assert "a" not in block
    assert _drop_block_fields(block, "a") is False


def test_omit_tail_entries_marks_count():
    block = {"items": [1, 2, 3]}
    assert _omit_tail_entries(block, "items", "items_omitted")
    assert block["items_omitted"] == 1
    assert _omit_tail_entries(block, "items", "items_omitted")
    assert block["items_omitted"] == 2
    assert _omit_tail_entries(block, "items", "items_omitted")
    assert block["items"] == []
    assert block["items_omitted"] == 3
    assert not _omit_tail_entries(block, "items", "items_omitted")


def test_json_block_handles_bare_list():
    assert json.loads(_json_block([1, 2])) == [1, 2]


# ---------------------------------------------------------------------------
# resolver candidates
# ---------------------------------------------------------------------------


def test_resolver_block_valid_json_with_omission_marker():
    orch, model = _orchestrator()
    descriptor = _cap("target")
    candidates = [
        _cap(f"resolver_{i}", desc_len=500, group_id="alpha")
        for i in range(40)
    ]
    group = _group([descriptor, *candidates])
    orch._select_resolver(
        "find the id",
        descriptor,
        ("filial",),
        group,
        None,
        (),
        "corr",
        _deadline(),
    )
    raw = _block(model, RESOLVER_SELECTION_INSTRUCTION_ID, "resolver")
    data = json.loads(raw)  # must not raise — never severed
    candidates_out = data["resolver_candidates"]
    omitted = data.get("candidates_omitted", 0)
    # truthfulness: listed + omitted never exceeds the eligible 40
    assert len(candidates_out) + omitted <= 40
    if omitted:
        assert len(candidates_out) + omitted == 40
    for entry in candidates_out:
        assert entry["remote_name"].startswith("resolver_")
        assert entry["operation_class"] in (
            "READ",
            "DISCOVERY",
            "ANALYSIS",
        )
    assert data["target"]["remote_name"] == "target"
    assert data["target"]["missing_inputs"] == ["filial"]


# ---------------------------------------------------------------------------
# argument/schema projection
# ---------------------------------------------------------------------------

_QUERY_DESCRIPTOR = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
}


def test_arguments_block_schema_survives_whole_over_budget():
    """Owner evidence shrinks; input_schema is never touched."""
    orch, model = _orchestrator()
    descriptor = _cap("search_items", schema=dict(_QUERY_DESCRIPTOR))
    orch._build_arguments(
        "term bala",
        descriptor,
        owner_evidence="vocab " * 40000,
        foreign_evidence="foreign " * 30000,
        business_subject="terminal bala",
        deadline=_deadline(),
    )
    raw = _block(model, ARGUMENTS_INSTRUCTION_ID, "schema")
    data = json.loads(raw)
    assert data["input_schema"] == _QUERY_DESCRIPTOR
    assert data["capability"] == "search_items"
    assert data["business_subject"] == "terminal bala"


def test_arguments_block_immutable_schema_emits_whole():
    """A schema bigger than the projection budget still arrives
    intact — valid JSON, never a severed contract."""
    assert len(json.dumps(_BIG_SCHEMA)) > MAX_ARGUMENTS_BLOCK_CHARS
    orch, model = _orchestrator()
    descriptor = _cap("big_schema_op", schema=_BIG_SCHEMA)
    orch._build_arguments(
        "anything",
        descriptor,
        deadline=_deadline(),
    )
    raw = _block(model, ARGUMENTS_INSTRUCTION_ID, "schema")
    data = json.loads(raw)
    assert data["input_schema"] == _BIG_SCHEMA
    assert set(data["input_schema"]["required"]) == {"field_0"}


def test_unfittable_schema_fails_closed_before_dispatch():
    """A schema that cannot fit the transport bound never reaches
    the model — the typed boundary rejects it, no severed envelope."""
    assert len(json.dumps(_FAT_SCHEMA)) > 16384
    orch, model = _orchestrator()
    descriptor = _cap("fat_schema_op", schema=_FAT_SCHEMA)
    orch._build_arguments(
        "anything",
        descriptor,
        deadline=_deadline(),
    )
    purposes = [r.task_purpose_id for r in model.requests]
    assert ARGUMENTS_INSTRUCTION_ID not in purposes


def test_arguments_block_evidence_provenance_matches_projection():
    """The declared-origin verification corpus must equal the text
    the model actually saw — no fail-open on unprojected evidence."""
    orch, model = _orchestrator()
    descriptor = _cap("search_items", schema=dict(_QUERY_DESCRIPTOR))
    huge_vocab = "TAILTOKEN " + "v" * (MAX_ARGUMENTS_BLOCK_CHARS * 3)
    orch._build_arguments(
        "term bala",
        descriptor,
        owner_evidence=huge_vocab,
        deadline=_deadline(),
    )
    raw = _block(model, ARGUMENTS_INSTRUCTION_ID, "schema")
    data = json.loads(raw)
    projected = data.get("owner_vocabulary")
    # when the excerpt shrinks to fit, the tail the model never saw
    # must not be part of the verification corpus
    if projected is not None:
        assert "TAILTOKEN" in projected
        assert len(projected) < len(huge_vocab)


# ---------------------------------------------------------------------------
# evidence/records projections
# ---------------------------------------------------------------------------


def test_relevance_block_valid_json_records_bounded():
    orch, model = _orchestrator()
    facts = EvidenceFacts(
        records=tuple(
            {"id": f"r{i}", "desc": "d" * 800} for i in range(16)
        ),
        has_business_evidence=True,
    )
    goal = OperationalCapabilityOrchestrator._TurnGoal(
        business_subject="terminal bala",
        declared=True,
    )
    orch._judge_goal_evidence(
        "traga terminais bala",
        facts,
        goal,
        workspace_context=None,
        prior_turns=(),
        correlation="corr",
        deadline=_deadline(),
    )
    raw = _block(
        model, GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID, "evidence"
    )
    data = json.loads(raw)
    listed = len(data["records"])
    omitted = data.get("records_omitted", 0)
    assert listed + omitted <= 16
    if omitted:
        assert listed + omitted == 16
    assert len(raw) <= MAX_RELEVANCE_EVIDENCE_CHARS
    for record in data["records"]:
        assert record["id"].startswith("r")


def test_synthesis_block_valid_json_records_bounded():
    orch, model = _orchestrator()
    outcome = _outcome(
        {
            "items": [
                {"code": f"10{i}", "name": "TERM " + "d" * 700}
                for i in range(20)
            ]
        }
    )
    orch._synthesize_content(
        "traga terminais",
        outcome,
        "corr",
        deadline=_deadline(),
        business_subject="terminal bala",
    )
    raw = _block(model, SYNTHESIS_INSTRUCTION_ID, "records")
    data = json.loads(raw)
    listed = len(data["records"])
    omitted = data.get("records_omitted", 0)
    assert listed + omitted <= 20
    assert len(raw) <= MAX_SURFACE_CHARS
    assert data["business_subject"] == "terminal bala"
    for record in data["records"]:
        assert record["code"].startswith("10")


# ---------------------------------------------------------------------------
# index probe / index select / candidate arguments
# ---------------------------------------------------------------------------


def test_index_probe_schema_emits_whole():
    orch, model = _orchestrator()
    descriptor = _cap("index_op", schema=_BIG_SCHEMA)
    orch._propose_index_probe(
        "consulta",
        descriptor,
        None,
        (),
        "corr",
        _deadline(),
    )
    raw = _block(model, INDEX_PROBE_INSTRUCTION_ID, "capability")
    data = json.loads(raw)
    assert data["input_schema"] == _BIG_SCHEMA
    assert data["remote_name"] == "index_op"


def test_index_probe_unfittable_schema_fails_closed():
    orch, model = _orchestrator()
    descriptor = _cap("index_op", schema=_FAT_SCHEMA)
    orch._propose_index_probe(
        "consulta",
        descriptor,
        None,
        (),
        "corr",
        _deadline(),
    )
    purposes = [r.task_purpose_id for r in model.requests]
    assert INDEX_PROBE_INSTRUCTION_ID not in purposes


def test_index_select_options_bounded_truthfully():
    orch, model = _orchestrator()
    options = tuple(
        {
            "identifier": f"id_{i}",
            "label": "label " + "l" * 400,
            "hints": "hints " + "h" * 400,
        }
        for i in range(8)
    )
    orch._propose_index_identifier(
        "consulta",
        options,
        ("codigo", "descricao"),
        workspace_context=None,
        prior_turns=(),
        correlation="corr",
        deadline=_deadline(),
    )
    raw = _block(model, INDEX_SELECT_INSTRUCTION_ID, "owner_index")
    data = json.loads(raw)
    listed = len(data["owner_index_options"])
    omitted = data.get("options_omitted", 0)
    assert listed + omitted <= 8
    if omitted:
        assert listed + omitted == 8
    for option in data["owner_index_options"]:
        assert option["identifier"].startswith("id_")
    assert data["argument_fields"] == ["codigo", "descricao"]


def test_candidate_arguments_schema_emits_whole():
    orch, model = _orchestrator()
    orch._propose_candidate_arguments(
        "consulta",
        _BIG_SCHEMA,
        correlation="corr",
        deadline=_deadline(),
        business_subject="terminal bala",
    )
    raw = _block(model, CANDIDATE_ARGUMENTS_INSTRUCTION_ID, "schema")
    data = json.loads(raw)
    assert data["schema"] == _BIG_SCHEMA
    assert data["business_subject"] == "terminal bala"


def test_candidate_arguments_default_schema_valid():
    orch, model = _orchestrator()
    orch._propose_candidate_arguments(
        "consulta",
        None,
        correlation="corr",
        deadline=_deadline(),
    )
    raw = _block(model, CANDIDATE_ARGUMENTS_INSTRUCTION_ID, "schema")
    assert json.loads(raw) == {"type": "object"}


# ---------------------------------------------------------------------------
# clarification wording + analysis continuation
# ---------------------------------------------------------------------------


def test_clarification_block_valid_json():
    orch, model = _orchestrator()
    descriptor = _cap("update_item", desc_len=400)
    orch._clarification_question(
        "atualize o item",
        tuple(f"field_{i}" for i in range(50)),
        descriptor,
        "corr",
        deadline=_deadline(),
    )
    raw = _block(model, CLARIFICATION_INSTRUCTION_ID, "missing_inputs")
    data = json.loads(raw)
    listed = len(data["missing_inputs"])
    omitted = data.get("inputs_omitted", 0)
    assert listed + omitted <= 50
    if omitted:
        assert listed + omitted == 50


def test_analysis_continuation_block_valid_json():
    orch, model = _orchestrator()
    prepare = _cap(
        "prepare_op",
        desc_len=300,
        op_class=SpecialistOperationClass.PREPARE,
    )
    group = _group([prepare])
    outcome = _outcome({"summary": "s" * 9000})
    orch._select_prepare_continuation(
        "continue",
        outcome,
        group,
        None,
        (),
        "corr",
        _deadline(),
    )
    raw = _block(model, CONTINUATION_INSTRUCTION_ID, "analysis_continuation")
    data = json.loads(raw)
    assert "prepare_candidates" in data
    assert isinstance(data.get("analysis"), str)
