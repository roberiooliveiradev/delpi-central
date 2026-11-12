"""INT-1 — business-identifier coverage and argument-schema feedback.

DELIA-C3-T2-INT1-IDENTIFIER-RESOLUTION-AND-PARTIAL-AUTHZ-SCHEMA-
REMEDIATION-01. Proves:

1. ``explain_arguments`` returns actionable field/type feedback for
   every rejection shape that previously blind-retried (unknown
   top-level field, missing required, wrong type, enum/const,
   orchestration-owned fields) — and never leaks argument values.
2. A governed ``arguments_schema_rejected`` attempt projects the
   INVALID_ARGUMENTS feedback to the model and carries the canonical
   limitation; the generic NO_PROGRESS continuity ModelRetry must NOT
   mask it.
3. Identifier coverage recognizes exact identifier values inside
   owner-structured fields (``codigo_processo=PROC-0034``, numeric
   ``code``) — not only DAVI-style ``data.root.code`` — while prose
   mentions never close coverage.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_NONE,
    _attempt_identifier_roots,
    _is_business_evidence_attempt,
    _uncovered_named_identifiers,
)
from app.application.interaction.argument_validation import (
    explain_arguments,
    validate_arguments,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    LIMITATION_ARGUMENT_SCHEMA_REJECTED,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _attempt_projection,
    continuity_model_retry_allowed,
    focus_arguments_on_next_identifier,
    uncovered_user_identifiers,
)


# --- explain_arguments -----------------------------------------------------

_TEO_READ_SCHEMA = {
    "type": "object",
    "properties": {
        "entity": {"type": "string"},
        "action": {"type": ["string", "null"]},
        "params": {"anyOf": [{"type": "object"}, {"type": "null"}]},
    },
    "required": ["entity"],
}


def test_explain_unknown_top_level_field_names_field_and_contract():
    # IG2 shape: the model put `id` next to entity/action instead of
    # inside params — previously a silent blind rejection.
    args = {"entity": "process", "action": "get", "id": "PROC-0034"}
    assert validate_arguments(args, _TEO_READ_SCHEMA) is None
    reason = explain_arguments(args, _TEO_READ_SCHEMA)
    assert reason is not None
    assert "unknown top-level field(s): id" in reason
    assert "entity" in reason and "params" in reason
    # The business value itself never leaks into feedback.
    assert "PROC-0034" not in reason


def test_explain_missing_required_field():
    args = {"action": "get", "params": {"id": "x"}}
    assert validate_arguments(args, _TEO_READ_SCHEMA) is None
    reason = explain_arguments(args, _TEO_READ_SCHEMA)
    assert reason == "missing required field(s): entity"


def test_explain_wrong_type_names_expected_shape():
    args = {"entity": "process", "params": "PROC-0034"}
    assert validate_arguments(args, _TEO_READ_SCHEMA) is None
    reason = explain_arguments(args, _TEO_READ_SCHEMA)
    assert reason is not None
    assert "'params'" in reason
    assert "rejects string" in reason
    assert "object" in reason


def test_explain_enum_rejection():
    schema = {
        "type": "object",
        "properties": {"action": {"enum": ["search", "get"]}},
    }
    args = {"action": "mutate"}
    assert validate_arguments(args, schema) is None
    reason = explain_arguments(args, schema)
    assert reason is not None
    assert "'action'" in reason


def test_explain_orchestrated_field():
    schema = {
        "type": "object",
        "properties": {"entity": {"type": "string"}},
    }
    args = {"entity": "process", "candidate_token": "tok"}
    assert validate_arguments(args, schema) is None
    reason = explain_arguments(args, schema)
    assert reason is not None
    assert "orchestration-managed" in reason
    assert "candidate_token" in reason


def test_explain_accepts_valid_instance():
    args = {"entity": "process", "action": "get", "params": {"id": "x"}}
    assert validate_arguments(args, _TEO_READ_SCHEMA) == args
    assert explain_arguments(args, _TEO_READ_SCHEMA) is None


def test_explain_no_schema_owner_rejects_any_arguments():
    assert explain_arguments({"q": "x"}, None) is not None
    assert explain_arguments({}, None) is None


def test_explain_never_leaks_argument_values():
    secret = "SECRET-BUSINESS-VALUE-7F3A"
    args = {"entity": "process", "undeclared": secret}
    reason = explain_arguments(args, _TEO_READ_SCHEMA)
    assert reason is not None
    assert secret not in reason


# --- rejected attempt projection + retry gate ------------------------------


def _schema_rejected_attempt() -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="c-args",
        content=(
            "INVALID_ARGUMENTS: unknown top-level field(s): id. "
            "Declared fields are: entity, action, params."
        ),
        limitations=(LIMITATION_ARGUMENT_SCHEMA_REJECTED,),
        error_code="arguments_schema_rejected",
    )


def test_rejected_attempt_projection_carries_actionable_feedback():
    projection = _attempt_projection(
        _schema_rejected_attempt(),
        observation_index=0,
        uncovered_after=("PROC-0034",),
    )
    assert projection["error_code"] == "arguments_schema_rejected"
    assert LIMITATION_ARGUMENT_SCHEMA_REJECTED in projection["limitations"]
    assert "INVALID_ARGUMENTS" in (projection["content"] or "")
    assert "unknown top-level field" in projection["content"]
    assert projection["evidence_citable"] is False


def test_rejected_attempt_coverage_note_keeps_same_capability():
    # R4 defect: the generic NO_PROGRESS note told the model to
    # "select a different live capability" — replaying the same bad
    # args on every tool. The rejection note must instead direct a
    # corrected retry on THIS capability.
    projection = _attempt_projection(
        _schema_rejected_attempt(),
        observation_index=0,
        uncovered_after=("PROC-0034",),
    )
    note = projection["coverage_note"]
    assert "different live capability" not in note
    assert "declared schema" in note or "declared object" in note
    assert "INVALID_ARGUMENTS" in note or "contract" in note


def test_continuity_retry_does_not_mask_schema_feedback():
    # A generic "select a different capability" retry must not fire on
    # argument rejection — the INVALID_ARGUMENTS observation is the
    # correct recovery signal for the SAME tool.
    assert (
        continuity_model_retry_allowed(
            attempt=_schema_rejected_attempt(),
            investigation_progress=INVESTIGATION_PROGRESS_NONE,
            uncovered=("PROC-0034",),
            already_used=False,
            under_tool_limit=True,
        )
        is False
    )


# --- focus narrowing must not inject undeclared fields ---------------------


_MULTI_ID_TEXT = (
    "Mostre a decomposição do processo PROC-0034 e a estrutura "
    "do produto 90260147."
)


def test_focus_never_injects_query_undeclared_by_schema():
    # PARTIAL_AUTHZ root cause: the focus helper wrote a top-level
    # ``query`` into arguments for tools whose schema never declares it
    # (teo.read/davi.read/get_context), so DÉLIA rejected its own
    # mutation as arguments_schema_rejected ×N with zero invocations.
    args = focus_arguments_on_next_identifier(
        {"entity": "decomposition_tree", "action": "get",
         "params": {"id": "PROC-0034"}},
        input_text=_MULTI_ID_TEXT,
        collected=(),
        declared_properties={"entity", "action", "params"},
    )
    assert "query" not in args


def test_focus_still_narrows_when_query_declared():
    args = focus_arguments_on_next_identifier(
        {"query": _MULTI_ID_TEXT},
        input_text=_MULTI_ID_TEXT,
        collected=(),
        declared_properties={"query"},
    )
    assert "PROC-0034" in args["query"]
    assert "90260147" not in args["query"]


# --- owner-structured identifier coverage ----------------------------------


def _business_attempt(structured: dict) -> GovernedCapabilityAttempt:
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="teo",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="c-teo",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text="Processo PROC-0034 DELPI Indicadores.",
        is_complete=True,
        structured=structured,
        limitations=(),
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c-teo",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="teo",
                    source_system="teo",
                    provider_name="teo",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="teo",
            remote_capability="read",
            action_id="process_get",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c-teo",
            is_complete=True,
        ),
        content="Processo PROC-0034 DELPI Indicadores.",
    )


def test_identifier_roots_recognize_codigo_processo_field():
    attempt = _business_attempt(
        {
            "processo_id": "9f1c2d34-0000-4000-8000-0000000000aa",
            "codigo_processo": "PROC-0034",
            "titulo": "DELPI Indicadores",
        }
    )
    roots = _attempt_identifier_roots(attempt)
    assert "PROC-0034" in roots
    # A UUID field is not a business-identifier literal — no coverage.
    assert not any("9f1c2d34" in item for item in roots)


def test_identifier_roots_recognize_numeric_code_field():
    attempt = _business_attempt({"item": {"code": 90260147, "qty": 1}})
    assert "90260147" in _attempt_identifier_roots(attempt)


def test_prose_mention_does_not_close_coverage():
    attempt = _business_attempt(
        {"descricao": "Registro relacionado ao PROC-0034 internamente"}
    )
    assert "PROC-0034" not in _attempt_identifier_roots(attempt)


def test_uncovered_identifiers_closed_by_owner_codigo_processo():
    attempt = _business_attempt({"codigo_processo": "PROC-0034"})
    assert _is_business_evidence_attempt(attempt)
    text = "Mostre a decomposição do processo PROC-0034 (DELPI)."
    assert uncovered_user_identifiers(text, [attempt]) == []
    assert _uncovered_named_identifiers(text, [attempt]) == []


def test_uncovered_identifiers_remain_when_owner_misses_code():
    attempt = _business_attempt({"codigo_processo": "PROC-9999"})
    text = "Mostre a decomposição do processo PROC-0034 (DELPI)."
    assert uncovered_user_identifiers(text, [attempt]) == ["PROC-0034"]


def test_structure_root_still_covers_davi_shape():
    attempt = _business_attempt(
        {"data": {"root": {"code": "90260147", "descricao": "Produto"}}}
    )
    text = "Mostre a estrutura do produto 90260147."
    assert uncovered_user_identifiers(text, [attempt]) == []
