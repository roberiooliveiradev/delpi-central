"""Provider-neutral operational capability orchestration.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
DÉLIA is the OPERATIONAL_CAPABILITY_ORCHESTRATOR. Capability
providers (MCP, OpenAPI, media/screen, future A2A/Automation) project
their live surfaces into provider-neutral capability groups; this
module is the central orchestration boundary over them — it holds no
provider mechanics and no local capability catalog authority.

Flow per user turn:

  live capability groups per provider
    -> sanitized semantic projection (class-projected, bounded)
    -> bounded workspace context (host/route/EntityRef hints —
       untrusted, never authority)
    -> model proposal (selection is a proposal, never authority)
    -> deterministic revalidation against the fresh projection
    -> provider-owned workflow preserved: candidate_token chains
       (DAVI-style) and PREPARE->ACT proposal_handle chains are
       detected structurally from the owner schema, never hardcoded;
       opaque envelope capabilities run a bounded DISCOVERY->target
       plan so owner-declared operation vocabulary feeds argument
       projection (§6.131 R1); when the target requires an input the
       turn cannot supply, one bounded same-owner RESOLVER step
       (DISCOVERY|READ|ANALYSIS evidence) may resolve it before a
       clarification ask-back — ambiguity yields a bounded candidate
       list, never a silent pick; a successful ANALYSIS target may
       continue into an applicable PREPARE when the user goal
       requires a change (§6.140)
    -> invoke through the provider adapter -> bounded provenance +
       truthful rendering
    -> write classes route through the generic governed-write chain:
       preview -> pending orchestration state -> structured
       confirmation -> fresh live revalidation -> ACT ->
       owner-authoritative outcome projection

Adding/removing/reclassifying ANY remote capability never requires a
DÉLIA code or config change — the next turn sees the fresh surface.
UNKNOWN-class capabilities stay discoverable but are never invocable.
Confirmation is never authorization: live Core AuthZ and owner/domain
revalidation still gate every ACT call.
"""

from __future__ import annotations

import contextvars
import dataclasses
import hashlib
import json
import logging
import re
import time
import unicodedata
import uuid
from typing import Any, Callable, Mapping, Sequence

from app.application.interaction.activity import (
    ActivityEventSink,
    ActivityOutcomeStatus,
    ActivityPhase,
    ActivityState,
    capability_ref as _activity_capability_ref,
    outcome_ref as _activity_outcome_ref,
    owner_ref as _activity_owner_ref,
    source_ref as _activity_source_ref,
)
from app.application.interaction.argument_validation import (
    MAX_ARGUMENT_KEYS,
    ORCHESTRATED_FIELDS,
    _apply_entity_defaults_to_arguments,
    _argument_completeness_gaps,
    normalize_arguments,
    validate_arguments as _validate_instance,
    validate_untyped_arguments,
    apply_evidence_bound_selections,
)
from app.application.interaction.capability_attempt import (
    OWNER_PATH_UNBOUND,
    EARLY_CONVERSATIONAL_ADMISSION,
    SURFACE_INQUIRY_ADMISSION,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
    GovernedCapabilityBinding,
    _error_attempt,
    _success_attempt,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    LIMITATION_CAPABILITY_SURFACE_LISTING,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    LIMITATION_PRIOR_TURN_CONTINUATION,
    LIMITATION_RESULT_TRUNCATED,
)
from app.domain.interaction.model import TurnKind
from app.application.interaction.pending_proposals import (
    DEFAULT_PENDING_TTL_SECONDS,
    PENDING_PURPOSE_SCOPE_CHOICE,
    PENDING_PURPOSE_SCOPE_PLUS_CONFIRMATION,
    PendingWrite,
    PendingWriteStore,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ModelInvocationRequest,
)
from app.application.interaction.turn_budget import (
    DEFAULT_TURN_BUDGET_SECONDS,
    TurnBudgetExhausted,
    TurnDeadline,
)
from app.application.interaction.turn_observability import (
    current_call_ledger,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.governed_retries import (
    LLM_CALL_MAX_ATTEMPTS,
    call_retry_eligible,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    ProviderCapability,
)
from app.application.capability_provision.conversational_response import (
    MAX_RENDER_CONTENT_CHARS,
    CriComposition,
    FieldLabels,
    _business_lines,
    _compose_answer,
    _format_structured,
    _insufficiency_content,
    _md_business_lines,
    _md_format_structured,
    _md_leaf,
    _render_synthesis,
    _selected_proven_differences,
    compose_cri_response,
    field_clause_label,
    field_display_label,
    ordering_presentation,
    presented_record,
    records_are_prior_excerpts,
)
from app.application.capability_provision.outcome_assessment import (
    GOAL_EVIDENCE_CORRESPONDS,
    GOAL_EVIDENCE_IRRELEVANT,
    OUTCOME_ANSWERED,
    OUTCOME_ENVELOPE_ONLY,
    OUTCOME_INSUFFICIENT,
    REASON_GOAL_MISMATCH,
    REASON_RELEVANCE_UNPROVEN,
    AnswerRequirements,
    EvidenceFacts,
    GoalEvidenceJudgment,
    OutcomeVerdict,
    apply_verdict_limitation,
    assess_outcome,
    distinct_delivered_count,
    outcome_facts,
    parse_answer_requirements,
    parse_goal_evidence_judgment,
    MAX_CANDIDATE_ENTRIES,
    MAX_DESCRIPTION_CHARS,
    MAX_EVIDENCE_RECORD_CHARS,
    MAX_MISMATCH_HINT_CHARS,
    MAX_MISSING_INPUTS,
    MAX_OWNER_EVIDENCE_CHARS,
    MAX_OWNER_EVIDENCE_ENTRY_CHARS,
    MAX_RELEVANCE_EVIDENCE_CHARS,
    MAX_RELEVANCE_RECORDS,
    MAX_RENDER_LIST_ITEMS,
    MAX_SURFACE_ENTRIES,
    MAX_SYNTHESIS_FIELDS,
    _CAPABILITY_VOCABULARY_KEYS,
    _CONTROL_PLANE_KEYS,
    _RESOLVER_ENTITY_KEYS,
    _RESOLVER_ENVELOPE_KEYS,
    _bound_owner_evidence,
    _candidate_contract_rows,
    _canonical_key,
    _comparable_scalar,
    _comparison_records,
    _contract_fact_rows,
    _entity_payload_slot,
    _extract_owner_entity_schemas,
    _is_generic_status,
    _mapping_items_excluding_control,
    _missing_inputs,
    _prior_supports_typed_attribute_compare,
    _record_identifier,
    _redact_text,
    _resolver_entities,
    _sanitize_renderable,
    _synthesis_selections,
    _unwrap_owner_payload,
    _value_present,
    _wording_leaks_technical,
)
from app.application.capability_provision.paginated_result_semantics import (
    DEFAULT_MAX_PAGES,
    PersonalTicketScope,
    ResultIntent,
    aggregate_paginated_pages,
    arguments_include_personal_assignee,
    arguments_include_requester_filter,
    classify_personal_ticket_scope,
    classify_result_intent,
    count_message_for_visible_query,
    extract_pagination_envelope,
    personal_scope_response,
    resolve_count_semantics,
    unique_structural_ticket_list_capability,
)
from app.application.capability_provision.ports import (
    CapabilityProviderPort,
)
from app.application.specialist_interop.errors import (
    MCP_PROTOCOL_ERROR,
)
from app.domain.capability_catalog.model import OperationCharacter
from app.domain.decision_path.model import DecisionPathInput
from app.domain.decision_path.rules import select_decision_path
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
from app.domain.planning.model import PlanCandidate, PlanStep
from app.domain.planning.rules import validate_plan_candidate
from app.domain.governed_write.model import (
    ConfirmationDecision,
    ConfirmationRecord,
    ConfirmationState,
    ProposalReadiness,
    StructuredConfirmation,
    WriteOutcomeStatus,
    WriteProposalPreview,
)
from app.domain.governed_write.rules import (
    bind_confirmation,
    evaluate_write_continuation,
    preview_fingerprint,
    project_proposal_preview,
    project_write_outcome,
    proposal_digest,
)
from app.application.interaction.workspace_context import (
    WorkspaceContext,
)
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultStatus,
)
from app.domain.specialist_interop.rules import (
    invocable_in_interactive_phase,
)

_logger = logging.getLogger(__name__)

# Candidate-flow and proposal-flow detection are structural,
# owner-defined: a capability whose input schema requires
# ``candidate_token`` is the second step of an owner
# discover->candidate->execute pattern (DAVI); a capability whose input
# schema requires ``proposal_handle`` is the ACT step of an owner
# prepare->proposal->commit pattern (TÉO/VISTA). DÉLIA never names the
# pairs — the owner schema carries them.
CANDIDATE_TOKEN_FIELD = "candidate_token"
PROPOSAL_HANDLE_FIELD = "proposal_handle"
# Orchestration-resolved schema fields live in
# argument_validation.ORCHESTRATED_FIELDS (re-exported above): never
# accepted from a model proposal — DÉLIA fills them from owner-issued
# state (candidate_token, proposal_handle) or from the governed-write
# decision itself (confirmation, idempotency_key); commit_now is
# generic orchestration-control semantics (collapses PREPARE+ACT,
# bypassing the DÉLIA confirmation gate).

MAX_SURFACE_CHARS = 6000
MAX_DISCOVERY_QUERY_CHARS = 400
MAX_STRUCTURED_RENDER_CHARS = 2000
# Bounded operational plan (§6.140): at most three steps — an optional
# owner-DISCOVERY vocabulary step, an optional same-owner RESOLVER
# step (any non-mutating class supplying evidence for a missing
# target input), and the target step; or ANALYSIS target -> one
# applicable PREPARE continuation. No loops, no arbitrary chains, no
# graph search. Owner evidence is sanitized and bounded before it
# reaches the argument-projection prompt — it is data, never
# instruction. ACT is never a semantic plan step: it remains the
# governed continuation of a valid prepared proposal.
MAX_OPERATIONAL_PLAN_STEPS = 3
MAX_ARGUMENTS_BLOCK_CHARS = 14000
MAX_RESOLVER_CANDIDATE_LABEL_CHARS = 120
# Catalog INDEX options may exceed resolver ambiguity shortlists.
# Keep bounded (budget/prompt), but large enough for owner registries.
MAX_INDEX_OPTION_ENTRIES = 48

# Hierarchical selection (R1): the model makes three bounded
# proposals — specialist, then capability on that specialist's live
# surface, then arguments projected into the owner's live inputSchema.
# Each stage is independently revalidated against fresh catalog data;
# a proposal is never authority.
SELECTION_INSTRUCTION_VERSION = "13"

GROUP_SELECTION_INSTRUCTION_ID = (
    "delia.capability_orchestration.select_group"
)

CAPABILITY_SELECTION_INSTRUCTION_ID = (
    "delia.capability_orchestration.select_capability"
)

# I02-R3B: cold-start may request capability selection and turn-goal
# fields in one typed proposal (same purpose id). Expected fields stay
# capability-only so legacy fixtures without goal_class still validate;
# when goal_class is present the runtime skips a second turn_goal call.

INDEX_PROBE_INSTRUCTION_ID = (
    "delia.capability_orchestration.index_probe"
)

INDEX_SELECT_INSTRUCTION_ID = (
    "delia.capability_orchestration.index_select"
)

ARGUMENTS_INSTRUCTION_ID = "delia.capability_orchestration.arguments"

RESOLVER_SELECTION_INSTRUCTION_ID = (
    "delia.capability_orchestration.select_resolver"
)

CONTINUATION_INSTRUCTION_ID = (
    "delia.capability_orchestration.analysis_continuation"
)

CLARIFICATION_INSTRUCTION_ID = (
    "delia.capability_orchestration.clarification_wording"
)

SYNTHESIS_INSTRUCTION_ID = (
    "delia.capability_orchestration.grounded_synthesis"
)

NATIVE_ASSESSMENT_INSTRUCTION_ID = (
    "delia.capability_orchestration.native_assessment"
)

FOREIGN_SELECTION_INSTRUCTION_ID = (
    "delia.capability_orchestration.foreign_selection"
)

GOAL_INSTRUCTION_ID = (
    "delia.capability_orchestration.turn_goal"
)

# CRI E2 (doc 73 §3-§6 / spec 75): when the response-intelligence
# switch is ON, the SAME goal stage also proposes typed sufficiency
# requirements — a hypothesis the runtime verifies against typed
# evidence at the outcome edge. The clause itself is a governed
# declarative resource (config/cri_instructions.delpi.json, E2-R3)
# injected by composition; baseline instructions stay byte-identical
# and the mode deactivates when the resource is absent.

COMPARISON_INSTRUCTION_ID = (
    "delia.capability_orchestration.comparison"
)

# Write-class operation classes (C3-CI-02): PREPARE and ACT carry
# material-effect potential — they are structurally incompatible
# with a non-action turn goal. Class is orchestration eligibility,
# never permission; owner write governance below is untouched.
_WRITE_OPERATION_CLASSES = frozenset(
    {
        SpecialistOperationClass.PREPARE,
        SpecialistOperationClass.ACT,
    }
)

# Deterministic bounded intent clarification (C3-CI-02): the model
# declared the turn genuinely ambiguous between guidance and action
# while selecting a write capability. A fixed business question —
# never derived from capability names or fields, never an offer to
# execute without the governed chain.
_INTENT_CLARIFICATION_CONTENT = (
    "Você quer que eu explique como fazer, ou que eu execute "
    "a ação para você?"
)
# R1 (doc 35): after a group was chosen but capability selection is
# inconclusive, prefer a bounded ask-back over bare NOT_APPLICABLE
# that previously fell through to a second model call → 504.
# Group-level applicable=false is different: it means no owner surface
# is required → NOT_APPLICABLE → conversational fallback (CONV recovery).
_SELECTION_INCONCLUSIVE_CONTENT = (
    "Não consegui identificar uma consulta ou ação adequada nas "
    "fontes disponíveis para este pedido. Pode dizer se precisa de "
    "dados cadastrais da DELPI, orientação de um especialista, ou se "
    "é uma pergunta geral / exemplo hipotético?"
)

def _lineage(
    instruction_id: str,
    content: str,
    version: str = SELECTION_INSTRUCTION_VERSION,
) -> InstructionLineage:
    return InstructionLineage(
        instruction_id=instruction_id,
        version=version,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )

CANDIDATE_ARGUMENTS_INSTRUCTION_ID = (
    "delia.capability_orchestration.candidate_arguments"
)

CANDIDATE_SELECTION_INSTRUCTION_ID = (
    "delia.capability_orchestration.select_candidate"
)

def _is_candidate_bound(descriptor: ProviderCapability) -> bool:
    """True when the owner schema declares a candidate_token input."""
    return _requires_field(descriptor, CANDIDATE_TOKEN_FIELD)

def _is_proposal_bound(descriptor: ProviderCapability) -> bool:
    """True when the owner schema declares a proposal_handle input —
    the ACT leg of an owner PREPARE->commit chain can never serve as a
    non-mutating resolver step."""
    return _requires_field(descriptor, PROPOSAL_HANDLE_FIELD)

def _requires_field(descriptor: ProviderCapability, field: str) -> bool:
    schema = descriptor.input_schema
    if not isinstance(schema, Mapping):
        return False
    properties = schema.get("properties")
    required = schema.get("required")
    names = set(properties) if isinstance(properties, Mapping) else set()
    if isinstance(required, (list, tuple)):
        names.update(str(name) for name in required)
    return field in names

def _is_open_vocabulary(node: object, depth: int = 0) -> bool:
    """True when a schema node leaves its inner vocabulary owner-defined.

    An object type without ``properties`` or an array type whose
    ``items`` carries no declared shape is an opaque envelope field —
    the JSON Schema alone cannot express which values the owner
    accepts. Combiner branches (anyOf/oneOf/allOf) are inspected
    recursively with a hard depth bound.
    """
    if depth > 4 or not isinstance(node, Mapping):
        return False
    node_type = node.get("type")
    if node_type == "object" and "properties" not in node:
        return True
    if node_type == "array":
        items = node.get("items")
        if not isinstance(items, Mapping) or not items:
            return True
        if _is_open_vocabulary(items, depth + 1):
            return True
    for combiner in ("anyOf", "oneOf", "allOf"):
        branches = node.get(combiner)
        if isinstance(branches, (list, tuple)) and any(
            _is_open_vocabulary(branch, depth + 1) for branch in branches
        ):
            return True
    return False

def _is_unconstrained_string(node: object) -> bool:
    """True when a schema node is a free string with no closed enum/const.

    A free string alone is legitimate open text (search, name, description)
    — it does **not** imply owner-catalog vocabulary. Closed ``enum`` /
    ``const`` declare values in-schema. Nullable optional strings from
    MCP/JSON Schema often use ``anyOf``/``oneOf`` with ``string|null``;
    those are treated as free strings when the non-null branch is a plain
    string. Structural only — never field-name or provider hardcode.
    """
    if not isinstance(node, Mapping):
        return False
    if "enum" in node or "const" in node:
        return False
    if node.get("type") == "string":
        return True
    for combiner in ("anyOf", "oneOf"):
        branches = node.get(combiner)
        if not isinstance(branches, (list, tuple)):
            continue
        non_null = [
            branch
            for branch in branches
            if isinstance(branch, Mapping) and branch.get("type") != "null"
        ]
        if len(non_null) != 1:
            continue
        branch = non_null[0]
        if branch.get("type") != "string":
            continue
        if "enum" in branch or "const" in branch:
            return False
        return True
    return False

def _requires_owner_vocabulary(descriptor: ProviderCapability) -> bool:
    """Detect when argument values live only in the owner's vocabulary.

    Only opaque envelope fields (object without properties / array
    without item shape — see ``_is_open_vocabulary``) demonstrate that
    the JSON Schema cannot express legal values and same-group DISCOVERY
    may supply them. Required free strings alone never trigger discovery
    (RW-S03-01): the contract cannot distinguish controlled vocabulary
    from open text without enum/const or an opaque envelope. Caller still
    requires ``_discovery_capability`` before discovery runs. Never
    provider-specific.
    """
    schema = descriptor.input_schema
    if not isinstance(schema, Mapping):
        return False
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return False
    return any(_is_open_vocabulary(node) for node in properties.values())

def _contract_declares_omit_returns_index(descriptor: ProviderCapability) -> bool:
    """True when the untrusted capability description declares that
    omitting optional identifiers returns an index of options.

    Covers English MCP contracts (omit/omitted + index/available/list)
    and Portuguese owner surfaces that use the same semantic pair
    (omitir/sem … + índice/lista de) without field-name or provider
    hardcode. Never treats optional fields alone as sufficient
    (RW-S03-01).
    """
    text = (descriptor.description or "").lower()
    if not text:
        return False
    omit_signal = (
        "omit" in text
        or "omitted" in text
        or "without the" in text
        or "when omitted" in text
        or "omitir" in text
        or "omita" in text
        or "omitido" in text
        # PT clause form: "Sem <field>: índice …" — only with index_signal.
        or "sem " in text
    )
    index_signal = (
        "index" in text
        or "índice" in text
        or "indice" in text
        or "available" in text
        or "list of" in text
        or "lists the" in text
        or "lista de" in text
    )
    return omit_signal and index_signal

def _optional_unconstrained_string_keys(
    descriptor: ProviderCapability,
) -> tuple[str, ...]:
    """Optional free-string property names (no field-name hardcode)."""
    schema = descriptor.input_schema
    if not isinstance(schema, Mapping):
        return ()
    properties = schema.get("properties")
    if not isinstance(properties, Mapping) or not properties:
        return ()
    required = {
        str(item)
        for item in (schema.get("required") or ())
        if isinstance(item, str)
    }
    keys: list[str] = []
    for name, node in properties.items():
        if not isinstance(name, str) or name in required:
            continue
        if _is_unconstrained_string(node):
            keys.append(name)
    return tuple(keys[:MAX_ARGUMENT_KEYS])

def _index_catalog_entities(
    structured: object,
) -> tuple[Mapping[str, Any], ...]:
    """Catalog entities from an INDEX payload (broader than resolver).

    Same shape rules as ``_resolver_entities``, but sized with
    ``MAX_INDEX_OPTION_ENTRIES`` so owner registries are not silently
    truncated before identifier selection.
    """
    doc = _unwrap_owner_payload(structured)
    if not isinstance(doc, Mapping):
        return ()

    def _mappings(value: object) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, (list, tuple)):
            return ()
        return tuple(
            item
            for item in list(value)[:MAX_INDEX_OPTION_ENTRIES]
            if isinstance(item, Mapping)
        )

    for key in _RESOLVER_ENTITY_KEYS:
        entities = _mappings(doc.get(key))
        if entities:
            return entities
    for value in list(doc.values())[:MAX_SURFACE_ENTRIES]:
        if isinstance(value, (list, tuple)):
            entities = _mappings(value)
            if entities:
                return entities
        elif isinstance(value, Mapping):
            for key in _RESOLVER_ENTITY_KEYS:
                entities = _mappings(value.get(key))
                if entities:
                    return entities
    return ()

def _index_option_rows(
    structured: object,
    field_keys: tuple[str, ...],
) -> tuple[Mapping[str, str], ...]:
    """Bounded identifier/label rows from a structured owner index.

    Reuses unwrap/entity-key conventions and ``_entity_identifier`` —
    exact owner-declared identifiers only; labels are descriptive.
    """
    entities = _index_catalog_entities(structured)
    if not entities:
        return ()
    rows: list[dict[str, str]] = []
    for entity in entities:
        identifier = _entity_identifier(entity, field_keys)
        if not identifier:
            continue
        label = ""
        for token in _RESOLVER_LABEL_KEYS:
            value = next(
                (
                    v
                    for k, v in entity.items()
                    if token in _canonical_key(k)
                    and _canonical_key(k) != "id"
                    and _canonical_key(k) not in {
                        _canonical_key(f) for f in field_keys
                    }
                ),
                None,
            )
            if isinstance(value, str) and value.strip():
                label = value.strip()
                break
        if not label:
            label = next(
                (
                    str(v).strip()
                    for k, v in entity.items()
                    if isinstance(v, str)
                    and v.strip()
                    and str(v).strip() != identifier
                    and _canonical_key(k) not in {
                        _canonical_key(f) for f in field_keys
                    }
                ),
                "",
            )
        hint_parts: list[str] = []
        for key, value in entity.items():
            canon = _canonical_key(key)
            if canon in {
                _canonical_key(f) for f in field_keys
            } or canon in {"id", "identifier"}:
                continue
            if isinstance(value, str) and value.strip():
                text = value.strip()
                if text != identifier and text != label:
                    hint_parts.append(text)
            elif isinstance(value, (list, tuple)):
                for item in value[:6]:
                    if isinstance(item, str) and item.strip():
                        hint_parts.append(item.strip())
        hints = _redact_text(" | ".join(hint_parts))[
            : MAX_RESOLVER_CANDIDATE_LABEL_CHARS * 2
        ]
        rows.append(
            {
                "identifier": identifier,
                "label": _redact_text(label)[
                    :MAX_RESOLVER_CANDIDATE_LABEL_CHARS
                ],
                "hints": hints,
            }
        )
    return tuple(rows[:MAX_INDEX_OPTION_ENTRIES])

def _index_declared_identifiers(
    structured: object,
    field_keys: tuple[str, ...],
) -> frozenset[str]:
    """Exact owner-declared index identifiers (never description text)."""
    return frozenset(
        row["identifier"]
        for row in _index_option_rows(structured, field_keys)
        if row.get("identifier")
    )

def _post_self_index_argument_gaps(
    arguments: Mapping[str, Any] | None,
    descriptor: ProviderCapability,
    declared_identifiers: frozenset[str] | None,
) -> tuple[str, ...]:
    """After a self-index probe, require an exact declared identifier.

    Empty args and values that merely appear in descriptive text are
    rejected — only exact membership in ``declared_identifiers``
    proves provenance. Provider/field-name neutral.
    """
    if not declared_identifiers:
        return ()
    keys = _optional_unconstrained_string_keys(descriptor)
    if not keys:
        return ()
    args = arguments or {}
    proven = False
    gaps: list[str] = []
    for key in keys:
        raw = args.get(key)
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            gaps.append(key)
            continue
        text = str(raw).strip()
        if text not in declared_identifiers:
            gaps.append(key)
            continue
        proven = True
    if proven:
        return tuple(
            key
            for key in gaps
            if key in args
            and args.get(key) not in (None, "")
            and str(args.get(key)).strip() not in declared_identifiers
        )[:MAX_MISSING_INPUTS]
    return tuple(dict.fromkeys(gaps))[:MAX_MISSING_INPUTS]

def _project_selected_index_identifier(
    descriptor: ProviderCapability,
    selected_identifier: str,
    argument_field: str,
    declared_identifiers: frozenset[str],
) -> dict[str, Any] | None:
    """Project a validated index identifier into one schema field."""
    if selected_identifier not in declared_identifiers:
        return None
    keys = _optional_unconstrained_string_keys(descriptor)
    if argument_field not in keys:
        return None
    return _validate_instance(
        {argument_field: selected_identifier},
        descriptor.input_schema,
    )

def _eligible_self_index_probe(descriptor: ProviderCapability) -> bool:
    """True when a non-mutating capability may legally be invoked empty
    to obtain an owner index of optional free-string identifiers.

    Structural only: READ/ANALYSIS, empty invoke schema-valid (no
    required fields), at least one optional unconstrained string, and
    not an opaque-envelope case (those use same-group DISCOVERY).
    A probe still requires either an explicit owner-contract omit→index
    declaration or a model ``probe_index`` proposal. Never field-name
    or provider hardcode.
    """
    if descriptor.operation_class not in (
        SpecialistOperationClass.READ,
        SpecialistOperationClass.ANALYSIS,
    ):
        return False
    if _requires_owner_vocabulary(descriptor):
        return False
    schema = descriptor.input_schema
    if not isinstance(schema, Mapping):
        return False
    required = schema.get("required")
    if isinstance(required, (list, tuple)) and required:
        # Empty index invoke is only schema-valid when nothing is
        # required; required free strings remain RW-S03-01 / opaque path.
        return False
    return bool(_optional_unconstrained_string_keys(descriptor))

# SpecialistOperationClass -> canonical OperationCharacter for the
# shared plan validator. OperationCharacter intentionally models
# side-effect character only: DISCOVERY, READ and ANALYSIS are all
# non-mutating for planning purposes and project as READ — the
# specialist class stays authoritative on the descriptor itself
# (ANALYSIS is never collapsed on the capability contract).
_PLAN_OPERATION_CHARACTER: Mapping[SpecialistOperationClass, OperationCharacter] = {
    SpecialistOperationClass.DISCOVERY: OperationCharacter.READ,
    SpecialistOperationClass.READ: OperationCharacter.READ,
    SpecialistOperationClass.ANALYSIS: OperationCharacter.READ,
    SpecialistOperationClass.PREPARE: OperationCharacter.PREPARE,
    SpecialistOperationClass.ACT: OperationCharacter.ACT,
}

@dataclasses.dataclass(frozen=True, slots=True)
class _PlanCapabilityView:
    """Provider-neutral adapter so the shared plan validator governs
    live provider capabilities without a CapabilityProjection."""

    capability_id: str
    operation_character: OperationCharacter

def _plan_views(group: CapabilityGroup) -> tuple[_PlanCapabilityView, ...]:
    views: list[_PlanCapabilityView] = []
    for cap in group.capabilities:
        character = _PLAN_OPERATION_CHARACTER.get(cap.operation_class)
        if character is None:
            continue
        views.append(
            _PlanCapabilityView(
                capability_id=cap.capability_id,
                operation_character=character,
            )
        )
    return tuple(views)

def _discovery_capability(group: CapabilityGroup) -> ProviderCapability | None:
    """The group's owner-vocabulary source — exactly one live DISCOVERY
    capability is required for it to be usable; ambiguity fails closed."""
    discovery = [
        cap
        for cap in group.capabilities
        if cap.operation_class is SpecialistOperationClass.DISCOVERY
    ]
    return discovery[0] if len(discovery) == 1 else None

_MAX_DISCOVERY_SURFACE_LINES = 6

def _owner_eligible_action_count(
    structured: Mapping[str, Any] | None,
) -> int | None:
    """Owner-declared eligible catalog size when present.

    Provider-neutral common count keys. Missing field ≠ empty catalog.
    """
    if not isinstance(structured, Mapping):
        return None
    for key in (
        "eligible_action_count",
        "eligible_count",
        "action_count",
    ):
        value = structured.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value if value >= 0 else None
    return None

def _discovery_empty_result_class(
    structured: Mapping[str, Any] | None,
) -> str:
    """Classify a zero-candidate discovery envelope.

    Conceptual classes for observability/tests — not public DTOs.
    ``0 SEARCH RESULTS != CAPABILITY ABSENT``.
    """
    eligible = _owner_eligible_action_count(structured)
    if eligible is not None and eligible > 0:
        return "CAPABILITY_NOT_MATCHED"
    if eligible == 0:
        return "CAPABILITY_UNAVAILABLE"
    return "CAPABILITY_NOT_ENUMERABLE"

def _live_interop_surface_lines(
    group: CapabilityGroup,
) -> tuple[str, ...]:
    """Bounded lines from the live tools/list surface (owner-declared).

    Never invents Domain API action ids. Excludes PREPARE/ACT. Descriptions
    are untrusted display text — never authorization.
    """
    lines: list[str] = []
    for capability in group.capabilities:
        if capability.operation_class not in (
            SpecialistOperationClass.DISCOVERY,
            SpecialistOperationClass.READ,
            SpecialistOperationClass.ANALYSIS,
        ):
            continue
        name = (capability.remote_name or "").strip()
        if not name:
            continue
        description = _redact_text(
            (capability.description or "").strip()
        )[:180]
        if description:
            lines.append(f"- {name}: {description}")
        else:
            lines.append(f"- {name}")
        if len(lines) >= _MAX_DISCOVERY_SURFACE_LINES:
            break
    return tuple(lines)

def _render_zero_candidate_discovery(
    structured: Mapping[str, Any] | None,
    group: CapabilityGroup,
) -> str:
    """User-facing terminal for DISCOVERY with zero candidates.

    Distinguishes semantic search miss (catalog still exists) from
    unavailable/non-enumerable catalogs. Never leaks agent_directives,
    capability_surface blobs, tokens or telemetry keys.
    """
    result_class = _discovery_empty_result_class(structured)
    eligible = _owner_eligible_action_count(structured)
    surface = _live_interop_surface_lines(group)

    if result_class == "CAPABILITY_NOT_MATCHED":
        parts = [
            "A busca semântica não encontrou uma ação correspondente "
            "a este pedido.",
            (
                f"A fonte declara {eligible} capacidades de leitura "
                "elegíveis — resultado vazio de busca não prova "
                "ausência de capability."
            ),
            "Reformule com o tipo de informação desejada "
            "(por exemplo produto, estoque, pedido ou indicador). "
            "Discovery não autoriza execução.",
        ]
        if surface:
            parts.append(
                "Ferramentas de interoperabilidade observadas "
                "neste especialista:"
            )
            parts.extend(surface)
        return "\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]

    if result_class == "CAPABILITY_UNAVAILABLE":
        return (
            "Consulta concluída na fonte: nenhuma capacidade de "
            "leitura elegível está disponível para este escopo."
        )[:MAX_RENDER_CONTENT_CHARS]

    # CAPABILITY_NOT_ENUMERABLE — owner did not expose catalog size.
    if surface:
        parts = [
            "A busca não retornou correspondência e o contrato do "
            "owner não enumerou o catálogo de ações neste resultado.",
            "Não é possível listar todas as possibilidades "
            "informacionais a partir deste envelope.",
            "Ferramentas de interoperabilidade observadas "
            "neste especialista:",
        ]
        parts.extend(surface)
        parts.append(
            "Reformule com um pedido informacional específico. "
            "Discovery não autoriza execução."
        )
        return "\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]

    return (
        "Consulta concluída na fonte: nenhuma ação correspondente "
        "foi encontrada para este pedido."
    )[:MAX_RENDER_CONTENT_CHARS]


# ---------------------------------------------------------------------------
# Declared-contract bond (D5-schema remediation, doc 134/135)
#
# A discovery envelope that returned candidates but could not execute
# any may legitimately project owner-published contract rows ONLY when
# the model-declared contract subject provably bonds the selected
# capability's identity or a specific returned candidate. Token
# overlap uses the same ``_canonical_key`` fold the evidence pipeline
# applies (lowercase + non-alnum strip), with a bounded prefix
# tolerance so sibling vocabulary ("produtos" ~ "products") bonds
# while unrelated subjects stay honestly silent. No provider, entity
# or vocabulary blacklist — the bond derives solely from the typed
# declared subject and the owner-published identity text.
# ---------------------------------------------------------------------------

_BOND_STOP_TOKENS = frozenset(
    {
        "a", "o", "as", "os", "de", "do", "da", "dos", "das", "e",
        "em", "no", "na", "nos", "nas", "um", "uma", "para", "por",
        "com", "que", "the", "of", "and", "in", "for", "to",
    }
)
def _bond_token(part: object) -> str:
    """Canonical comparable bond token — accent-folded, lowercase,
    alphanumerics only. Deterministic canonicalization, never a
    semantic inference."""
    folded = unicodedata.normalize("NFKD", str(part))
    return re.sub(
        r"[^a-z0-9]", "", folded.encode("ascii", "ignore").decode()
    )


def _bond_forms(token: str) -> frozenset[str]:
    """Comparison forms of one canonical token: the verbatim token
    plus a bounded singular fold (trailing ``s`` on tokens of length
    >= 5) so same-vocabulary plurals bond — never prefix or
    substring matching."""
    forms = {token}
    if len(token) >= 5 and token.endswith("s"):
        forms.add(token[:-1])
    return frozenset(forms)


def _subject_bond_tokens(subject: object) -> frozenset[str]:
    """Comparable canonical tokens of the model-declared business
    subject (subject phrases are copied from user words)."""
    if not isinstance(subject, str) or not subject.strip():
        return frozenset()
    return frozenset(
        token
        for token in (
            _bond_token(part)
            for part in re.split(r"[^0-9A-Za-zÀ-ÿ]+", subject)
        )
        if len(token) >= 3 and token not in _BOND_STOP_TOKENS
    )


def _identity_tokens_bond(
    subject_tokens: frozenset[str], identity_text: str
) -> bool:
    """True when a declared-subject token provably bonds an owner-
    published typed identity token — exact canonical match on the
    expanded singular/plural forms. A shared prefix is never
    sufficient proof of semantic relevance."""
    identity_forms: set[str] = set()
    for part in re.split(r"[^0-9A-Za-zÀ-ÿ_]+|_", identity_text):
        token = _bond_token(part)
        if len(token) >= 3 and token not in _BOND_STOP_TOKENS:
            identity_forms.update(_bond_forms(token))
    return any(
        form in identity_forms
        for token in subject_tokens
        for form in _bond_forms(token)
    )


def _capability_identity_text(capability: ProviderCapability) -> str:
    """Owner-published TYPED identity surface of the selected
    capability — identifiers only; free-text descriptions never
    establish a contract bond."""
    return " ".join(
        part
        for part in (
            capability.remote_name,
            capability.capability_id,
        )
        if isinstance(part, str)
    )


def _candidate_identity_text(candidate: Mapping[str, Any]) -> str:
    """Owner-published TYPED identity surface of a discovery
    candidate — action/entity identifiers and owner-declared
    semantic hints only; description prose never establishes a
    contract bond."""
    parts: list[str] = [
        str(part)
        for part in (
            candidate.get("action_id"),
            candidate.get("name"),
            candidate.get("entity"),
        )
        if isinstance(part, str)
    ]
    hints = candidate.get("semantic_hints")
    if isinstance(hints, Mapping):
        entity = hints.get("entity")
        if isinstance(entity, str):
            parts.append(entity)
        tags = hints.get("tags")
        if isinstance(tags, (list, tuple)):
            parts.extend(
                str(tag) for tag in tags if isinstance(tag, str)
            )
    return " ".join(parts)


def _iter_bond_candidates(
    resolved: Mapping[str, Any] | None,
    structured: Mapping[str, Any] | None,
):
    """Yield the resolved candidate first, then envelope candidates —
    bounded scan, no duplicates."""
    seen: set[int] = set()
    pool: list[Mapping[str, Any]] = []
    if isinstance(resolved, Mapping):
        pool.append(resolved)
    candidates = (
        structured.get("candidates")
        if isinstance(structured, Mapping)
        else None
    )
    if isinstance(candidates, (list, tuple)):
        pool.extend(
            item
            for item in list(candidates)[:MAX_CANDIDATE_ENTRIES]
            if isinstance(item, Mapping)
        )
    for item in pool:
        if id(item) in seen:
            continue
        seen.add(id(item))
        yield item


def _contract_subject_bond(
    *,
    contract_subject: bool,
    business_subject: object,
    capability: ProviderCapability | None,
    resolved_candidate: Mapping[str, Any] | None,
    structured: Mapping[str, Any] | None,
) -> tuple[str, Mapping[str, Any] | None] | None:
    """Typed bond between the declared contract goal and owner
    vocabulary. Returns ``("candidate", candidate)`` when a specific
    candidate's published identity bonds, ``("capability", None)``
    when the selected capability's identity bonds, or ``None`` —
    honest silence when no legitimate contract scope is provable."""
    if not contract_subject:
        return None
    subject_tokens = _subject_bond_tokens(business_subject)
    if not subject_tokens:
        return None
    for candidate in _iter_bond_candidates(
        resolved_candidate, structured
    ):
        if _identity_tokens_bond(
            subject_tokens, _candidate_identity_text(candidate)
        ):
            return "candidate", candidate
    if capability is not None and _identity_tokens_bond(
        subject_tokens, _capability_identity_text(capability)
    ):
        return "capability", None
    return None


def _render_unusable_candidate_discovery(
    action_label: object,
) -> str:
    """User-facing terminal for DISCOVERY that located candidate(s)
    the declared arguments cannot execute — honest and bounded; the
    published contract is declared, never executed."""
    label = _redact_text(
        str(action_label) if isinstance(action_label, str) else ""
    ).strip()[:80]
    if label:
        lead = (
            f"A busca localizou a ação publicada '{label}', mas os "
            "dados informados não permitem executá-la com segurança."
        )
    else:
        lead = (
            "A busca localizou uma ação publicada pelo especialista, "
            "mas os dados informados não permitem executá-la com "
            "segurança."
        )
    return (
        lead
        + " Nenhuma operação foi realizada — discovery não autoriza "
        "execução."
    )[:MAX_RENDER_CONTENT_CHARS]


_MAX_SURFACE_INQUIRY_GROUPS = 8

def _surface_inquiry_content(
    groups: Mapping[str, CapabilityGroup],
    failures: list[str] | tuple[str, ...],
) -> str:
    """Deterministic projection of the LIVE governed surface (S1).

    Enumerates the capability groups observed this turn: owner-declared
    display names plus their DISCOVERY/READ/ANALYSIS consultation
    lines (same bounded shape as ``_live_interop_surface_lines``).
    Unreachable surfaces are declared honestly; publication is never
    presented as permission — listing grants nothing.
    """
    parts: list[str] = []
    if groups:
        parts.append(
            "Superfícies de especialistas publicadas e alcançáveis "
            "neste momento:"
        )
        group_keys = sorted(groups)
        for group_key in group_keys[:_MAX_SURFACE_INQUIRY_GROUPS]:
            group = groups[group_key]
            name = _redact_text(
                (group.display_name or group.group_id or "").strip()
            )[:80]
            if not name:
                continue
            lines = _live_interop_surface_lines(group)
            if lines:
                parts.append(f"- {name}:")
                parts.extend(f"  {line}" for line in lines)
            else:
                parts.append(f"- {name}")
        if len(group_keys) > _MAX_SURFACE_INQUIRY_GROUPS:
            parts.append(
                f"... e mais "
                f"{len(group_keys) - _MAX_SURFACE_INQUIRY_GROUPS} "
                "superfícies publicadas."
            )
    elif failures:
        parts.append(
            "Não consegui observar nenhuma superfície de "
            "especialistas neste momento — as fontes consultadas "
            "não responderam."
        )
    else:
        parts.append(
            "Nenhuma superfície de especialistas está publicada "
            "neste momento."
        )
    if groups and failures:
        parts.append(
            "Uma ou mais superfícies não responderam a esta consulta "
            "e não puderam ser listadas agora."
        )
    parts.append(
        "Uma superfície publicada respondeu a esta consulta agora; a "
        "permissão de uso é verificada a cada solicitação concreta — "
        "esta lista não garante autorização."
    )
    return "\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]

_PATH_FOREIGN_CLASSES = frozenset(
    {
        SpecialistOperationClass.DISCOVERY,
        SpecialistOperationClass.READ,
        SpecialistOperationClass.ANALYSIS,
    }
)

def _find_capability(
    groups: Mapping[str, CapabilityGroup],
    capability_id: str,
) -> tuple[str, ProviderCapability] | None:
    """Locate a capability id across the live groups.

    An id declared by more than one group is ambiguous — resolves to
    None; fail closed, never guess.
    """
    matches = [
        (group_key, cap)
        for group_key, group in groups.items()
        for cap in group.capabilities
        if cap.capability_id == capability_id
    ]
    return matches[0] if len(matches) == 1 else None

# Provenance/transport-only scalar keys — excluded from the shared
# context gate: differing technical metadata never forces INCONCLUSIVE
# (LOOP-03R1 §17). Canonical key forms, never owner names.
_COMPARISON_TECHNICAL_KEYS = frozenset(
    {
        "candidatetoken",
        "proposalhandle",
        "correlationid",
        "operationid",
        "remotename",
        "capabilityid",
        "providerid",
        "groupid",
        "observedat",
        "timestamp",
        "createdat",
        "updatedat",
        "revision",
        "etag",
        "requestid",
        "score",
        "rank",
    }
)

_INCONCLUSIVE_INSUFFICIENT = (
    "Comparação inconclusiva: contexto de comparação insuficiente."
)
_INCONCLUSIVE_SCOPE = (
    "Comparação inconclusiva: escopo não equivalente entre as fontes."
)

def _compare_records(
    left_records: tuple[Mapping[str, Any], ...],
    right_records: tuple[Mapping[str, Any], ...],
    proposal: Mapping[str, Any] | None,
) -> tuple[str, str] | None:
    """Deterministic comparison verdict from a bounded selection.

    The model only selects which records/fields are confronted; the
    runtime computes the verdict — ``agreement``, ``conflict`` or
    ``inconclusive`` — and renders evidence values verbatim. Context
    fields must match for the values to be comparable at all; any
    missing or non-scalar value is INCONCLUSIVE, never a guess.

    LOOP-03R1 (D01): beyond the model-selected context pairs, every
    shared scalar business context field present in BOTH records must
    carry equal values — a differing shared context the model omitted
    is a material contradiction and yields INCONCLUSIVE, never a false
    agreement/conflict.
    """

    def _side(
        raw: object, records: tuple[Mapping[str, Any], ...]
    ) -> tuple[Mapping[str, Any], tuple[str, ...], tuple[str, ...]] | None:
        if not isinstance(raw, Mapping):
            return None
        index = raw.get("record_index")
        if not isinstance(index, int) or isinstance(index, bool):
            return None
        if index < 0 or index >= len(records):
            return None
        context = raw.get("context_fields")
        values = raw.get("value_fields")
        if not isinstance(context, (list, tuple)) or not isinstance(
            values, (list, tuple)
        ):
            return None
        record = records[index]
        context_fields = tuple(f for f in context if isinstance(f, str))
        value_fields = tuple(f for f in values if isinstance(f, str))
        if len(context_fields) != len(context) or len(
            value_fields
        ) != len(values):
            return None
        if not value_fields or any(
            field not in record
            for field in context_fields + value_fields
        ):
            return None
        return record, context_fields, value_fields

    if not isinstance(proposal, Mapping):
        return None
    left = _side(proposal.get("left"), left_records)
    right = _side(proposal.get("right"), right_records)
    if left is None or right is None:
        return None
    left_record, left_context, left_values = left
    right_record, right_context, right_values = right
    if len(left_values) != len(right_values) or len(
        left_context
    ) != len(right_context):
        return None
    # Comparability gate (LOOP-02R1): at least one context pair is
    # required and both sides must declare canonically equivalent
    # field names — no semantic alias inference. Empty context or any
    # mismatch is INCONCLUSIVE, never agreement/conflict.
    if not left_context:
        return "inconclusive", _INCONCLUSIVE_INSUFFICIENT
    for left_field, right_field in zip(left_context, right_context):
        if _canonical_key(left_field) != _canonical_key(right_field):
            return "inconclusive", _INCONCLUSIVE_INSUFFICIENT
        left_value = _comparable_scalar(left_record.get(left_field))
        right_value = _comparable_scalar(right_record.get(right_field))
        if (
            left_value is None
            or right_value is None
            or left_value != right_value
        ):
            return "inconclusive", _INCONCLUSIVE_SCOPE
    # LOOP-03R1 (D01): independent of the model's selection, every
    # scalar field shared by BOTH records is material context — when
    # such a field differs, the two observations are not provably
    # about the same scope and the verdict must be INCONCLUSIVE.
    # Technical/provenance keys and the value fields themselves are
    # excluded by contract.
    value_canons = {_canonical_key(field) for field in left_values}
    left_scalars: dict[str, Any] = {}
    for key, value in left_record.items():
        canon = _canonical_key(key)
        if canon not in left_scalars:
            left_scalars[canon] = value
    for key, right_raw in right_record.items():
        canon = _canonical_key(key)
        if canon in value_canons or canon in _COMPARISON_TECHNICAL_KEYS:
            continue
        if canon not in left_scalars:
            continue
        left_scalar = _comparable_scalar(left_scalars[canon])
        right_scalar = _comparable_scalar(right_raw)
        if left_scalar is None or right_scalar is None:
            continue
        if left_scalar != right_scalar:
            return "inconclusive", _INCONCLUSIVE_SCOPE
    pairs: list[tuple[str, str]] = []
    conflict = False
    for left_field, right_field in zip(left_values, right_values):
        if _canonical_key(left_field) != _canonical_key(right_field):
            return "inconclusive", _INCONCLUSIVE_INSUFFICIENT
        left_value = _comparable_scalar(left_record.get(left_field))
        right_value = _comparable_scalar(right_record.get(right_field))
        if left_value is None or right_value is None:
            return "inconclusive", _INCONCLUSIVE_INSUFFICIENT
        pairs.append(
            (str(left_record.get(left_field)),
             str(right_record.get(right_field)))
        )
        if left_value != right_value:
            conflict = True
    headline = (
        "Comparação: valores divergentes."
        if conflict
        else "Comparação: valores convergentes."
    )
    lines = [headline]
    for left_value, right_value in pairs:
        lines.append(f"- fonte 1: {left_value} | fonte 2: {right_value}")
    verdict = "conflict" if conflict else "agreement"
    return verdict, "\n".join(lines)[:MAX_RENDER_CONTENT_CHARS]

# Bounded owner-published contract rows for DISCOVERY-class outcomes —
# capability-surface metadata, never domain facts.

# Capability-catalog descriptor collections — vocabulary about how the
# owner is operated (ops, schemas, guides, hints), never business
# evidence and never user-facing contract facts. Only unambiguous
# canonical collection names live here; homonymous business field
# names (``operations``, ``tools``) are handled by descriptor-shape
# detection or by envelope-context exclusion, never by name alone.

# Discovery-execution fields at the top level of a discovery payload —
# transport/orchestration data (the echoed query, counters, the
# candidate list, envelope status, the owner op-catalog sections).
# Excluded only at the digest's envelope level: homonymous fields
# inside entity contracts or business records are preserved.

# Capability-descriptor field signatures — an entry carrying a strong
# vocabulary field (an operation identifier, when-to-use guidance, an
# IO schema, a side-effect hint, a tool reference) is a capability
# descriptor, not a business record. Weak fields only count in pairs
# or alongside a strong field, so sparse homonymous business records
# stay eligible.

# Owner-published entity contracts (catalog DISCOVERY). Untrusted data
# used only for structural completeness against nested payloads — never
# Domain business rules, never AuthZ, never invented defaults.






# --- user-facing wording gates (C3-INTELLIGENCE-LOOP-01) ---------------
#
# Internal missing-input names are internal metadata, never user copy.
# A model may propose business wording; deterministic gates decide what
# may reach the user surface: no snake_case internals, no provider
# mechanics, no handles/tokens, no authority or execution claims.

# Evidence-bound synthesis bounds (§6.144/§6.145): the model proposes
# record selection only — there is no model-authored prose channel;
# factual leaf values are always copied verbatim by the runtime from
# sanitized owner evidence.
# Prior-turn continuity: deterministic excerpts for synthesis reuse
# (Stage 05 semantic continuity — never a literal full-result copy).
MAX_PRIOR_EXCERPTS = 12
_PRIOR_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")

# Provider-semantic errors where the capability surface changed under
# the initial selection — eligible for one bounded repair round.
_REPAIRABLE_SURFACE_CODES = frozenset(
    {
        "capability_not_on_surface",
        "capability_not_live",
        "capability_unknown",
        "unknown_capability",
    }
)

# Owner-side contract/admissibility rejections (a remote capability
# error reported by the specialist itself — never transport, auth or
# timeout): eligible for ONE bounded contextual-recovery round that
# consults the group's DISCOVERY vocabulary and re-proposes
# arguments under the real owner contract (C3 contextual discovery).
_OWNER_REMOTE_ERROR_CODES = frozenset({MCP_PROTOCOL_ERROR})

def _clarification_content(
    missing_inputs: tuple[str, ...],
    *,
    user_message: str | None = None,
) -> str:
    """Deterministic bounded clarification ask-back (§6.131/§6.144).

    The fallback never derives wording from the internal field names —
    even humanized labels still leak field vocabulary (``source_route``
    becomes "source route"). It never invents owner requirements
    (código/filtro/escopo) that the contract did not prove missing.
    The model wording stage supplies richer business phrasing when
    available; ``user_message`` is unused for phrasing to avoid quoting
    the request as a cosmetic cover for a generic ask.
    """
    del user_message  # retained for call-site compatibility only
    if len(missing_inputs) > 1:
        return (
            "Preciso de mais informações para continuar. "
            "Quais itens ou informações você quer usar?"
        )[:MAX_RENDER_CONTENT_CHARS]
    return (
        "Preciso de mais uma informação para continuar. "
        "Qual item ou informação você quer usar?"
    )[:MAX_RENDER_CONTENT_CHARS]






def _is_prior_list_item(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", line))

def _prior_paragraph_units(paragraph: str) -> list[str]:
    """Split one prior paragraph into selectable units.

    List markers stay atomic. A following heading is not part of the
    previous item. Non-list runs still split on sentence boundaries.
    """
    lines = paragraph.splitlines() or [paragraph]
    units: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if _is_prior_list_item(line):
            base = len(line) - len(line.lstrip(" "))
            chunk = [line.strip()]
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip() or _is_prior_list_item(nxt):
                    break
                indent = len(nxt) - len(nxt.lstrip(" "))
                if indent <= base:
                    break
                chunk.append(nxt.strip())
                index += 1
            units.append("\n".join(chunk)[:MAX_DESCRIPTION_CHARS])
            continue
        run = [line.strip()]
        index += 1
        while index < len(lines):
            nxt = lines[index]
            if not nxt.strip() or _is_prior_list_item(nxt):
                break
            run.append(nxt.strip())
            index += 1
        pieces = _PRIOR_SENTENCE_SPLIT_RE.split(" ".join(run))
        for piece in pieces:
            cleaned = piece.strip()
            if cleaned:
                units.append(cleaned[:MAX_DESCRIPTION_CHARS])
    return units

def _prior_excerpt_records(
    content: str,
) -> tuple[Mapping[str, str], ...]:
    """Split prior DELIA_RESULT text into deterministic excerpt records.

    Provider-neutral punctuation and list-line split — never owner
    keyword routing. Excerpts are untrusted conversational data for
    selection-only synthesis; they are never live owner facts.
    """
    text = (content or "").strip()
    if not text:
        return ()
    paragraphs = [
        part.strip()
        for part in re.split(r"\n\s*\n+", text)
        if part.strip()
    ]
    units: list[str] = []
    for paragraph in paragraphs or [text]:
        # A list item is only its own line plus more-indented
        # continuation. The next heading stays a separate unit so a
        # follow-up cannot inherit a dangling section label.
        units.extend(_prior_paragraph_units(paragraph))
    if not units:
        units = [text[:MAX_DESCRIPTION_CHARS]]
    return tuple(
        {"excerpt": unit} for unit in units[:MAX_PRIOR_EXCERPTS]
    )

def _prior_transform_probe_eligible(
    input_text: str,
    goal: "OperationalCapabilityOrchestrator._TurnGoal",
) -> bool:
    """True when typed goal authorizes a prior-transform probe.

    Q02-A: lexical continuity/live-fact cues removed. Only typed goal
    signals (compare/analyze / comparison_requested) authorize the
    probe. Dynamic output modes and write/clarify goals never probe.
    """
    if goal.goal_class in {"create_or_modify", "clarify"}:
        return False
    if goal.output_mode == "dynamic":
        return False
    if not (input_text or "").strip():
        return False
    return bool(
        goal.comparison_requested
        or goal.goal_class in {"compare", "analyze"}
    )


# Loose identifier candidates are business codes first — a field whose
# canonical name *starts* with a code/number family is as anchorable
# as a suffixed one (``codigo_processo``, ``numero_serie``,
# ``code_product``).

# A UUID-valued identifier is a surrogate key — acceptable verbatim
# evidence, but a poor conversational subject when a human-readable
# business code exists in the same record.





def _project_paginated_personal_or_count(
    input_text: str,
    structured: object,
    *,
    invocation_arguments: Mapping[str, Any] | None = None,
) -> tuple[str, tuple[str, ...]] | None:
    """Deterministic R4/R5 projection before model synthesis.

    Returns a (content, limitations) pair when personal-scope gates or
    count semantics apply; ``None`` leaves the ordinary synthesis /
    deterministic render path unchanged.
    """
    scope = classify_personal_ticket_scope(input_text)
    intent = classify_result_intent(input_text)
    envelope = extract_pagination_envelope(structured)

    if scope is PersonalTicketScope.MY_TICKETS_AMBIGUOUS and intent in {
        ResultIntent.COUNT,
        ResultIntent.LIST,
    }:
        text = personal_scope_response(scope)
        if text:
            return text, ()

    if scope is PersonalTicketScope.ASSIGNED_TO_ME and intent in {
        ResultIntent.COUNT,
        ResultIntent.LIST,
    }:
        if not arguments_include_personal_assignee(invocation_arguments):
            text = personal_scope_response(scope)
            if text:
                return text, ()

    if scope is PersonalTicketScope.REQUESTED_BY_ME and intent in {
        ResultIntent.COUNT,
        ResultIntent.LIST,
    }:
        if not arguments_include_requester_filter(invocation_arguments):
            text = personal_scope_response(scope)
            if text:
                return text, ()

    if intent is ResultIntent.COUNT and envelope is not None:
        resolution = resolve_count_semantics(envelope)
        if scope in {
            PersonalTicketScope.ALL_VISIBLE_TICKETS,
            PersonalTicketScope.NOT_APPLICABLE,
        }:
            return count_message_for_visible_query(resolution), ()
        # Personal scopes with proven filters: report count semantics
        # without the visible-query disclaimer.
        return resolution.message, ()

    return None

# Generic resolver-step helpers (§6.140): a RESOLVER is a role, never
# a tool class — any non-mutating same-owner capability whose result
# may supply evidence for a missing target input. All owner data is
# sanitized/bounded; resolved values must provably occur in the owner
# result, and multiple plausible entities produce a bounded
# clarification — never a silent selection.
_RESOLVER_LABEL_KEYS = (
    "name",
    "title",
    "label",
    "nome",
    "titulo",
    "descricao",
    "description",
    "codigo",
    "code",
)

# Owner control-plane metadata — orchestration data, never business
# evidence: structurally excluded from synthesis records and from the
# deterministic user-facing projection.

# Provider-neutral guidance section families (I02). Canonical keys only
# — never specialist/product names. Used to project selectable records
# and to prioritize deterministic fallback under truncation/budget.
_GUIDANCE_SECTION_FAMILIES: Mapping[str, frozenset[str]] = {
    "prerequisites": frozenset(
        {
            "prerequisites",
            "prerequisite",
            "requiredinputs",
            "requiredinput",
            "requiredinformation",
            "inputs",
            "informacoesnecessarias",
            "informacoes",
            "preconditions",
            "beforestarting",
            "antesdeiniciar",
            "datatorequire",
            "informationneeded",
        }
    ),
    "steps": frozenset(
        {
            "steps",
            "step",
            "etapas",
            "etapasrecomendadas",
            "stages",
            "procedure",
            "procedures",
            "methods",
            "method",
            "metodos",
            "metodologia",
            "methodology",
            "playbook",
            "playbooks",
            "recommendedsteps",
            "howtoconduct",
            "analysissteps",
            "howtouse",
            "comousar",
        }
    ),
    "objective": frozenset(
        {
            "objective",
            "objetivo",
            "purpose",
            "proposito",
            "goal",
            "overview",
            "summary",
            "resumo",
            "title",
            "productguide",
            "guideindex",
        }
    ),
    "when": frozenset(
        {
            "when",
            "quando",
            "whentouse",
            "usewhen",
            "applicability",
            "aplicabilidade",
        }
    ),
    "criteria": frozenset(
        {
            "criteria",
            "criterios",
            "criterio",
            "legibility",
            "legibilidade",
            "contrast",
            "contraste",
            "hierarchy",
            "hierarquia",
            "visualization",
            "visualizacao",
            "blocktypes",
            "choicecriteria",
            "designcriteria",
            "readability",
            "displayformats",
            "displayformat",
            "formats",
            "formatos",
        }
    ),
    "limitations": frozenset(
        {
            "limitations",
            "limitation",
            "limitacoes",
            "limitacao",
            "constraints",
            "restricoes",
            "invariants",
            "invariant",
            "caveats",
            "warnings",
            "donotusewhen",
            "donotuse",
            "naousarquando",
        }
    ),
}

# Nested owner envelopes commonly wrapping guidance sections (not
# transport data/result keys — those are handled by unwrap).
_GUIDANCE_NESTED_KEYS = frozenset(
    {
        "guide",
        "content",
        "body",
        "methodology",
        "playbook",
        "guidance",
        "document",
    }
)

# Transport/meta keys deprioritized when truncating guidance dumps —
# still renderable if space remains; never invented or dropped silently
# from the full structured payload without declaring truncation.
_GUIDANCE_META_KEYS = frozenset(
    {
        "guideversion",
        "authority",
        "readonly",
        "writes",
        "provenance",
        "evidencestates",
        "diagramrule",
        "read_only",
        "version",
        "schemaversion",
    }
)

# Stable presentation order for guidance sections — a deterministic
# priority, never a lexical intent cue (Q02-A). The LLM goal /
# synthesis path chooses which records to emphasize.
_GUIDANCE_FAMILY_ORDER: tuple[str, ...] = (
    "objective",
    "when",
    "steps",
    "prerequisites",
    "criteria",
    "limitations",
)

def _guidance_family_for_key(key: object) -> str | None:
    canon = _canonical_key(key)
    if not canon or canon in _CONTROL_PLANE_KEYS:
        return None
    if canon in _GUIDANCE_META_KEYS:
        return "meta"
    for family, keys in _GUIDANCE_SECTION_FAMILIES.items():
        if canon in keys or any(
            canon.startswith(k) or k.startswith(canon) for k in keys
        ):
            return family
    return None

# Technical structure keys inside an owner guidance section — schema
# and registry revisions, capability pointers, content-type markers.
# They are provenance/transport metadata, never user-facing content;
# business homonyms outside a guidance section map are unaffected.
_GUIDANCE_RENDER_SKIP_KEYS = frozenset(
    {
        "schema",
        "registryversion",
        "readcapability",
        "capabilityversion",
        "contenttype",
        "envelopeversion",
    }
)

# Guide-index sections are pointer structures (topic summaries that
# select a doc), never the answer itself. Their excerpt gets a bounded
# preview so concrete sibling sections — catalogs, criteria — share
# the render budget instead of being starved by the index.
_GUIDANCE_INDEX_KEYS = frozenset({"productguide", "guideindex"})
_GUIDANCE_INDEX_PREVIEW_CHARS = MAX_DESCRIPTION_CHARS * 2

# Context-folded discovery retry (P3/D8-R): a referential follow-up
# ("esse material") can miss the owner semantic search where a
# re-asked concrete question would hit. When prior turns exist the
# bounded fold lets the owner resolve the referenced concept — one
# retry, still a plain owner READ, never a fabricated identifier.
MAX_DISCOVERY_CONTEXT_TURNS = 4
MAX_DISCOVERY_CONTEXT_EXCERPT_CHARS = 120

def _render_guidance_value(
    value: object,
    *,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> str:
    """Bounded owner-value projection for one guidance section leaf."""
    if depth > 3 or value is None:
        return ""
    if isinstance(value, Mapping):
        sanitized = _sanitize_renderable(value)
        if not isinstance(sanitized, Mapping):
            return ""
        filtered = {
            key: item
            for key, item in sanitized.items()
            if _canonical_key(key) not in _GUIDANCE_META_KEYS
            and _canonical_key(key) not in _GUIDANCE_RENDER_SKIP_KEYS
        }
        lines = _format_structured(
            filtered, depth=0, field_labels=field_labels
        )
        return "\n".join(lines).strip()
    if isinstance(value, (list, tuple)):
        parts: list[str] = []
        for item in list(value)[:MAX_RENDER_LIST_ITEMS]:
            if isinstance(item, Mapping):
                line = _render_guidance_value(
                    item, depth=depth + 1, field_labels=field_labels
                )
                if line:
                    parts.append(line)
            elif item is not None and str(item).strip():
                parts.append(f"- {_redact_text(str(item).strip())}")
        return "\n".join(parts).strip()
    text = _redact_text(str(value).strip())
    return text

def _guidance_hit_count(items: tuple[tuple[str, object], ...]) -> int:
    return sum(
        1
        for key, _ in items
        if (_guidance_family_for_key(key) or "meta") != "meta"
    )

def _iter_guidance_doc_items(
    structured: object,
) -> tuple[tuple[str, object], ...]:
    """Guidance items under a business or nested guide envelope."""
    doc = _unwrap_owner_payload(structured)
    if not isinstance(doc, Mapping):
        return ()
    for key in _RESOLVER_ENVELOPE_KEYS:
        inner = doc.get(key)
        if isinstance(inner, Mapping) and inner:
            doc = inner
            break
    items = _mapping_items_excluding_control(doc)
    if _guidance_hit_count(items) >= 2:
        return items
    # Nested guide/body envelopes (e.g. {"schema":..., "guide": {...}}).
    for key, value in doc.items():
        if (
            isinstance(value, Mapping)
            and value
            and _canonical_key(key) in _GUIDANCE_NESTED_KEYS
        ):
            nested = _mapping_items_excluding_control(value)
            if _guidance_hit_count(nested) >= 2:
                return nested
    nested_maps = [
        value
        for key, value in doc.items()
        if isinstance(value, Mapping)
        and value
        and _canonical_key(key) not in _CONTROL_PLANE_KEYS
        and _canonical_key(key) not in _GUIDANCE_META_KEYS
    ]
    if len(nested_maps) == 1:
        nested = _mapping_items_excluding_control(nested_maps[0])
        if _guidance_hit_count(nested) >= 2:
            return nested
    return items

def _guidance_section_records(
    structured: object,
    field_labels: FieldLabels | None = None,
) -> tuple[Mapping[str, str], ...]:
    """Project guidance-shaped owner payloads into selectable records.

    Each named section becomes ``{section, excerpt, family}``. Returns
    () when fewer than two guidance/meta sections exist — ordinary
    entity/scalar shapes keep the prior synthesis path.
    """
    items = _iter_guidance_doc_items(structured)
    if not items:
        return ()
    records: list[Mapping[str, str]] = []
    guidance_hits = 0
    for key, value in items:
        family = _guidance_family_for_key(key)
        if family is None:
            continue
        if family != "meta":
            guidance_hits += 1
        rendered = _render_guidance_value(
            value, field_labels=field_labels
        )
        if not rendered:
            continue
        # Pointer/index sections and record enumerations (catalogs,
        # topic lists) are previews — never the whole answer. They get
        # a bounded excerpt marked partial so sibling concrete sections
        # share the render budget. Prose/steps stay whole-or-omitted
        # (the guidance presentation contract).
        is_pointer = _canonical_key(key) in _GUIDANCE_INDEX_KEYS
        is_enumeration = isinstance(value, (list, tuple)) and any(
            isinstance(item, Mapping) for item in value
        )
        if (
            (is_pointer or is_enumeration)
            and len(rendered) > _GUIDANCE_INDEX_PREVIEW_CHARS
        ):
            cut = rendered[:_GUIDANCE_INDEX_PREVIEW_CHARS]
            if "\n" in cut:
                cut = cut.rsplit("\n", 1)[0]
            rendered = cut.rstrip() + "\n\u2026(se\u00e7\u00e3o parcial \u2014 truncada)"
        records.append(
            {
                "section": str(key),
                "excerpt": rendered[: MAX_DESCRIPTION_CHARS * 8],
                "family": family,
            }
        )
        if len(records) >= MAX_PRIOR_EXCERPTS:
            break
    if guidance_hits < 2 or len(records) < 2:
        return ()
    return tuple(records)

def _omitted_sections_line(names: list[str], max_chars: int) -> str:
    """Disclose omitted guidance section names without their bodies."""
    if not names or max_chars < 24:
        return ""
    prefix = "Seções do guia não exibidas neste turno: "
    shown: list[str] = []
    for name in names:
        trial = prefix + ", ".join(shown + [name])
        if len(trial) <= max_chars:
            shown.append(name)
            continue
        break
    if not shown:
        return "Há seções do guia não exibidas neste turno."[:max_chars]
    text = prefix + ", ".join(shown)
    hidden = len(names) - len(shown)
    if hidden:
        suffix = f" (+{hidden})"
        if len(text) + len(suffix) <= max_chars:
            text += suffix
    return text

def _pack_guidance_sections(
    blocks: list[tuple[str, str]],
    max_chars: int,
) -> tuple[str, tuple[str, ...]]:
    """Fit whole guidance sections into the existing render cap.

    A section is not cut to make room for the next one. Names of
    sections that do not fit are disclosed. One oversized section is
    cut on a line boundary and still marked partial.
    """
    if not blocks or max_chars <= 0:
        return "", ()
    chosen: list[str] = []
    for index, (_name, block) in enumerate(blocks):
        rest = [name for name, _block in blocks[index + 1 :]]
        already_len = len("\n\n".join(chosen))
        separator = 2 if chosen else 0
        room_for_disclosure = max_chars - (already_len + separator + len(block))
        if room_for_disclosure < 0:
            break
        disclosure = (
            _omitted_sections_line(rest, room_for_disclosure) if rest else ""
        )
        disc_len = (2 + len(disclosure)) if disclosure else 0
        if already_len + separator + len(block) + disc_len <= max_chars:
            chosen.append(block)
            continue
        break
    if chosen:
        omitted = tuple(name for name, _block in blocks[len(chosen) :])
        body = "\n\n".join(chosen)
        if omitted:
            room = max_chars - len(body) - 2
            line = _omitted_sections_line(list(omitted), room)
            if line:
                body = f"{body}\n\n{line}"
        return body[:max_chars], omitted
    name, block = blocks[0]
    rest = [item for item, _block in blocks[1:]]
    disclosure = _omitted_sections_line([name, *rest], max_chars)
    marker = "\n…(resultado parcial — truncado)"
    disc = f"\n\n{disclosure}" if disclosure else ""
    room = max_chars - len(marker) - len(disc)
    if room < 1:
        room = max(1, max_chars - len(marker))
        disc = ""
    cut = block[:room]
    if "\n" in cut:
        cut = cut.rsplit("\n", 1)[0]
    body = cut.rstrip() + marker + disc
    if len(body) > max_chars:
        body = body[:max_chars].rstrip()
    return body, tuple(item for item, _block in blocks)

def _deterministic_guidance_content(
    structured: object,
    *,
    max_chars: int = MAX_RENDER_CONTENT_CHARS,
    owner_truncated: bool = False,
    field_labels: FieldLabels | None = None,
) -> tuple[str, tuple[str, ...]] | None:
    """Goal-aligned deterministic projection of guidance owner data.

    Selection-only: copies owner section text; never invents leaves.
    Returns None when the payload is not guidance-shaped or no
    intent-matching section has content.
    """
    selected = _select_guidance_records(
        structured, field_labels=field_labels
    )
    if not selected:
        return None
    blocks: list[tuple[str, str]] = []
    for record in selected:
        section = record.get("section") or "section"
        excerpt = (record.get("excerpt") or "").strip()
        if not excerpt:
            continue
        label = (
            field_display_label(
                _canonical_key(section), section, field_labels
            )
            if field_labels is not None
            else section
        )
        blocks.append((section, f"{label}:\n{excerpt}"))
    if not blocks:
        return None
    body, omitted = _pack_guidance_sections(blocks, max_chars)
    if not body:
        return None
    limitations: list[str] = []
    if owner_truncated or omitted:
        limitations.append(LIMITATION_RESULT_TRUNCATED)
    return body, tuple(limitations)

# Pagination/control-plane scalar keys — presence of these never
# disqualifies an explicitly empty business collection.

def _synthesis_records(
    structured: object,
    field_labels: FieldLabels | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Bounded business records available to grounded synthesis.

    Extends the resolver entity extraction: preferred collection keys
    and lists of mappings first, then guidance sections as selectable
    records (I02), then a single business record — a flat scalar
    object nested under exactly one non-control key or a flat scalar
    object as the whole payload. Transport envelopes are unwrapped
    structurally; control-plane siblings are never promoted.
    """
    entities = _resolver_entities(structured)
    if entities:
        return entities
    guidance = _guidance_section_records(
        structured, field_labels=field_labels
    )
    if guidance:
        return guidance
    doc = _unwrap_owner_payload(structured)
    if not isinstance(doc, Mapping):
        return ()
    containers = [
        value
        for key, value in doc.items()
        if isinstance(value, Mapping)
        and _canonical_key(key) not in _CONTROL_PLANE_KEYS
        and _canonical_key(key) not in _CAPABILITY_VOCABULARY_KEYS
    ]
    if len(containers) == 1:
        candidate = containers[0]
        if any(
            not isinstance(value, (Mapping, list, tuple))
            and value is not None
            for value in candidate.values()
        ):
            return (candidate,)
        return ()
    if containers:
        # Ambiguous shape — several candidate records; never pick
        # silently, the deterministic projection renders the payload.
        return ()
    if any(
        isinstance(value, (Mapping, list, tuple))
        for value in doc.values()
    ):
        return ()
    if any(
        value is not None and str(value).strip()
        for value in doc.values()
    ):
        return (doc,)
    return ()

def _entity_identifier(
    entity: Mapping[str, Any], missing_inputs: tuple[str, ...]
) -> str | None:
    """The identifier value an entity supplies for a missing input.

    Priority: an entity key canonically equal to the missing input
    name, then a bare ``id``. Scalar values only — never invented.
    """
    canon_missing = {_canonical_key(name) for name in missing_inputs}
    for key, value in entity.items():
        if _canonical_key(key) in canon_missing and isinstance(
            value, (str, int, float)
        ):
            return str(value).strip()
    bare = entity.get("id")
    if isinstance(bare, (str, int, float)):
        return str(bare).strip()
    for key, value in entity.items():
        if (
            _canonical_key(key).endswith("id")
            and _canonical_key(key) != "id"
            and isinstance(value, (str, int, float))
        ):
            return str(value).strip()
    return None

def _resolver_ambiguous(
    entities: tuple[Mapping[str, Any], ...],
    missing_inputs: tuple[str, ...],
) -> bool:
    """True when the owner returned more than one plausible entity.

    Entities sharing the same identifier collapse; distinct
    identifier values mean the owner could not disambiguate and
    DÉLIA must not pick silently.
    """
    if len(entities) < 2:
        return False
    identifiers = {
        _entity_identifier(entity, missing_inputs) for entity in entities
    }
    identifiers.discard(None)
    return len(identifiers) != 1

def _prior_observation_context(
    prior_turns: tuple[ConversationContextTurn, ...],
) -> dict[str, Any] | None:
    """Bounded untrusted prior observation for the selection proposal.

    The model interprets references. This block does not count
    identifiers, detect list wording, or grant provenance.
    """
    prior = OperationalCapabilityOrchestrator._prior_result_turn(
        prior_turns
    )
    if (
        prior is None
        or prior.epistemic_class is not EpistemicClass.OBSERVATION
    ):
        return None
    content = (prior.content or "").strip()
    if not content:
        return None
    return {
        "prior_result_available": True,
        "authoritative": False,
        "untrusted_excerpt": content[:MAX_OWNER_EVIDENCE_ENTRY_CHARS],
    }

def _context_folded_discovery_query(
    input_text: str,
    prior_turns: tuple[ConversationContextTurn, ...],
) -> str | None:
    """Bounded context-folded discovery query — or ``None``.

    A referential follow-up ("esse material", "consulte de novo") can
    miss the owner's semantic search where the re-asked concrete
    question hits. The fold keeps the user text first and appends
    bounded prior-turn excerpts — untrusted context, never authority,
    never a fabricated identifier.
    """
    base = (input_text or "").strip()
    if not base or not prior_turns:
        return None
    excerpts: list[str] = []
    for turn in prior_turns[-MAX_DISCOVERY_CONTEXT_TURNS:]:
        content = (turn.content or "").strip()
        if content:
            excerpts.append(
                content[:MAX_DISCOVERY_CONTEXT_EXCERPT_CHARS]
            )
    if not excerpts:
        return None
    folded = f"{base} {' '.join(excerpts)}".strip()
    if folded == base:
        return None
    return folded[:MAX_DISCOVERY_QUERY_CHARS]

def _fill_missing_from_entity(
    descriptor: ProviderCapability,
    missing_inputs: tuple[str, ...],
    entity: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Deterministically fill missing identifier fields from one entity."""
    filled: dict[str, Any] = {}
    for name in missing_inputs:
        canon = _canonical_key(name)
        value: Any = None
        for key, raw in entity.items():
            if _canonical_key(key) == canon and isinstance(
                raw, (str, int, float)
            ):
                value = raw
                break
        if value is None:
            value = _entity_identifier(entity, (name,))
        if value is None or not str(value).strip():
            return None
        filled[str(name)] = (
            str(value).strip()
            if isinstance(value, str)
            else value
        )
    if not filled:
        return None
    validated = _validate_instance(filled, descriptor.input_schema)
    return validated

def _candidate_clarification_content(
    entities: tuple[Mapping[str, Any], ...],
    missing_inputs: tuple[str, ...],
) -> str:
    """Bounded, sanitized candidate list for an ambiguous resolution.

    Values and labels are copied from owner evidence only — never
    invented. Identifier first, then the first short label-ish string.
    """
    lines = ["Encontrei mais de um registro correspondente:"]
    for entity in entities[:MAX_CANDIDATE_ENTRIES]:
        identifier = _entity_identifier(entity, missing_inputs) or ""
        label = ""
        for token in _RESOLVER_LABEL_KEYS:
            value = next(
                (
                    v
                    for k, v in entity.items()
                    if token in _canonical_key(k)
                    and _canonical_key(k) != "id"
                ),
                None,
            )
            if isinstance(value, str) and value.strip():
                label = value.strip()
                break
        if not label:
            label = next(
                (
                    str(v).strip()
                    for v in entity.values()
                    if isinstance(v, str)
                    and v.strip()
                    and str(v).strip() != identifier
                ),
                "",
            )
        row = _redact_text(
            f"{identifier} — {label}"
            if identifier and label
            else (identifier or label or "(registro)")
        )[:MAX_RESOLVER_CANDIDATE_LABEL_CHARS]
        lines.append(f"- {row}")
    lines.append("Qual deles você quer usar?")
    return "\n".join(lines)[:MAX_RENDER_CONTENT_CHARS]

def _missing_inputs_bound(
    arguments: Mapping[str, Any],
    missing_inputs: tuple[str, ...],
) -> bool:
    """Every input the target was missing is present in the rebuilt
    instance — provenance checks skip absent fields, so coverage is
    asserted separately to keep an under-filtered rebuild from
    resolving into an invocation that drops the required filter."""
    bound = {_canonical_key(key) for key in arguments}
    return all(
        _canonical_key(name) in bound for name in missing_inputs
    )


def _resolved_values_proven(
    arguments: Mapping[str, Any],
    missing_inputs: tuple[str, ...],
    resolver_payload: object,
) -> bool:
    """Provenance check: a resolved scalar must occur in owner
    evidence — the model never invents identifiers (§21)."""
    serialized = json.dumps(
        resolver_payload, ensure_ascii=False, default=str
    )[:MAX_OWNER_EVIDENCE_CHARS * 4]
    canon_args = {_canonical_key(k): v for k, v in arguments.items()}
    for name in missing_inputs:
        value = canon_args.get(_canonical_key(name))
        if value is None:
            continue
        if isinstance(value, (str, int, float)):
            if str(value) not in serialized:
                return False
    return True

def _schema_declared_literals(descriptor: ProviderCapability) -> str:
    """Bounded serialization of owner-declared literal values
    (``enum``/``const``/``default``). A value the owner itself declares
    in the schema is owner vocabulary, not a model invention."""
    schema = descriptor.input_schema
    literals: list[str] = []

    def _walk(node: object, depth: int = 0) -> None:
        if depth > 4 or len(literals) >= MAX_ARGUMENT_KEYS * 4:
            return
        if isinstance(node, Mapping):
            for key in ("enum", "const", "default"):
                value = node.get(key)
                values = (
                    value if isinstance(value, (list, tuple)) else (value,)
                )
                for item in values:
                    if isinstance(item, (str, int, float)):
                        literals.append(str(item))
            for value in list(node.values())[:MAX_SURFACE_ENTRIES]:
                if isinstance(value, (Mapping, list, tuple)):
                    _walk(value, depth + 1)
        elif isinstance(node, (list, tuple)):
            for item in list(node)[:MAX_SURFACE_ENTRIES]:
                _walk(item, depth + 1)

    _walk(schema)
    return json.dumps(literals, ensure_ascii=False, default=str)[
        :MAX_ARGUMENTS_BLOCK_CHARS
    ]

def _unproven_identifier_inputs(
    arguments: Mapping[str, Any],
    descriptor: ProviderCapability,
    input_text: str,
    workspace_context: WorkspaceContext | None,
    owner_evidence: str | None,
) -> tuple[str, ...]:
    """Identifier-typed arguments whose proposed scalar occurs in no
    provenance source — an invented id is demoted to a missing input
    so the resolver/clarification path handles it (§10/§21,
    fail closed).

    Provenance sources: the current user message, workspace-supplied
    identifier provenance (WorkspaceContext is untrusted
    client-supplied targeting context — it may identify the current
    selected entity but is never authority or permission; owner/domain
    revalidation still applies), owner evidence already obtained this
    turn, and literal values the owner itself declares in the input
    schema (``enum``/``const``/``default``). Only keys canonically
    equal to ``id`` or ending in ``id`` are gated — enums and free
    text are not identifiers.

    ``prior_turns`` is deliberately NOT a provenance source: client-
    supplied conversation history is untrusted and non-authoritative
    (``_validate_prior_context``) — a DELIA_RESULT line mentioning an
    identifier cannot prove it for owner invocation. Prior context
    remains available to model proposals as semantic context, but an
    identifier whose only occurrence is in history is demoted to a
    missing input and must be resolved through live owner evidence
    or clarified with the user.
    """
    haystack_parts = [input_text or ""]
    if owner_evidence:
        haystack_parts.append(owner_evidence)
    if workspace_context is not None:
        haystack_parts.append(workspace_context.to_prompt_block())
    haystack_parts.append(_schema_declared_literals(descriptor))
    haystack = "\n".join(haystack_parts)
    unproven: list[str] = []
    for key, value in list(arguments.items())[:MAX_ARGUMENT_KEYS]:
        canon = _canonical_key(key)
        if not (canon == "id" or canon.endswith("id")):
            continue
        if not isinstance(value, (str, int, float)):
            continue
        text = str(value).strip()
        if text and text not in haystack:
            unproven.append(str(key))
    return tuple(unproven[:MAX_MISSING_INPUTS])

CONFIRMATION_POLICY_DIRECT = "direct"
CONFIRMATION_POLICY_CONFIRM = "explicit_confirmation_required"
CONFIRMATION_POLICY_INVALID = "owner_policy_invalid"

def _effective_confirmation_policy(
    preview: WriteProposalPreview,
) -> str:
    """Deterministic provider-neutral confirmation decision (§6.140).

    The sole authority is the structural confirmation requirement
    carried by the owner PREPARE proposal itself
    (``confirmation_requirement.explicit_user_confirmation`` — both
    active owners seal it owner-side; owner-local policy labels such
    as ``execution_policy`` remain evidence/display data, never a
    second policy engine). ``true`` -> explicit user confirmation;
    ``false`` -> governed direct continuation. Missing, malformed or
    contradictory declarations fail closed as owner-policy-invalid —
    never auto-ACT and never a lazy confirmation prompt guessed from
    capability names, owner names or operation vocabulary.
    """
    requirement = preview.confirmation_requirement
    if isinstance(requirement, Mapping):
        declared = [
            requirement[key]
            for key in ("explicit_user_confirmation", "required")
            if key in requirement
        ]
        if declared and all(value is True for value in declared):
            return CONFIRMATION_POLICY_CONFIRM
        if declared and all(value is False for value in declared):
            return CONFIRMATION_POLICY_DIRECT
        # Mixed declarations (one field true, the other false) are a
        # contradictory owner contract — fail closed below.
    return CONFIRMATION_POLICY_INVALID

def _schema_keys(
    descriptor: ProviderCapability,
) -> tuple[frozenset[str], frozenset[str]]:
    """Owner-declared (properties, required) names; bounded projection."""
    schema = descriptor.input_schema
    if not isinstance(schema, Mapping):
        return frozenset(), frozenset()
    properties = schema.get("properties")
    required = schema.get("required")
    return (
        frozenset(
            str(k) for k in list(properties)[:MAX_ARGUMENT_KEYS]
        )
        if isinstance(properties, Mapping)
        else frozenset(),
        frozenset(
            str(r) for r in required if isinstance(r, str)
        )
        if isinstance(required, (list, tuple))
        else frozenset(),
    )

def _property_node(
    schema: Mapping[str, Any] | None, key: str
) -> Mapping[str, Any] | None:
    if not isinstance(schema, Mapping):
        return None
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return None
    node = properties.get(key)
    return node if isinstance(node, Mapping) else None

def _sole_unconstrained_string_field(
    descriptor: ProviderCapability,
) -> str | None:
    """Name of the only non-orchestrated free-string field, if any.

    Used for budget-safe projection of the user message into a single
    query-like argument — never invents identifiers or multi-field
    payloads.
    """
    keys, required = _schema_keys(descriptor)
    material = sorted((keys | required) - ORCHESTRATED_FIELDS)
    if len(material) != 1:
        return None
    field = material[0]
    schema = (
        descriptor.input_schema
        if isinstance(descriptor.input_schema, Mapping)
        else None
    )
    node = _property_node(schema, field)
    if not _is_unconstrained_string(node):
        return None
    return field

def _single_free_text_argument_from_input(
    input_text: str,
    descriptor: ProviderCapability,
) -> dict[str, Any] | None:
    """Project user text into a sole free-string schema field.

    Fail closed when the schema needs more than one material field or
    the projected instance is schema-invalid.
    """
    text = (input_text or "").strip()
    if not text:
        return None
    field = _sole_unconstrained_string_field(descriptor)
    if field is None:
        return None
    candidate = {field: text[:MAX_DESCRIPTION_CHARS]}
    return _validate_instance(candidate, descriptor.input_schema)

def _deterministic_arguments_from_schema(
    descriptor: ProviderCapability,
) -> dict[str, Any] | None:
    """Build arguments without a model when every non-orchestrated key
    is owner-closed (single enum/const or default) — never invent ids.

    Returns None when any required/non-orchestrated field needs
    interpretation (free string, multi-enum, opaque object/array).
    """
    keys, required = _schema_keys(descriptor)
    material = (keys | required) - ORCHESTRATED_FIELDS
    if not material:
        return {}
    schema = (
        descriptor.input_schema
        if isinstance(descriptor.input_schema, Mapping)
        else None
    )
    arguments: dict[str, Any] = {}
    for key in sorted(material)[:MAX_ARGUMENT_KEYS]:
        node = _property_node(schema, key)
        if node is None:
            return None
        if "const" in node:
            value = node["const"]
            if not isinstance(value, (str, int, float, bool)):
                return None
            arguments[key] = value
            continue
        enum_values = node.get("enum")
        if isinstance(enum_values, (list, tuple)) and len(enum_values) == 1:
            value = enum_values[0]
            if not isinstance(value, (str, int, float, bool)):
                return None
            arguments[key] = value
            continue
        if "default" in node and key not in required:
            value = node["default"]
            if not isinstance(value, (str, int, float, bool)):
                return None
            arguments[key] = value
            continue
        # Free string / multi-enum / opaque → model or clarification.
        return None
    for key in required - ORCHESTRATED_FIELDS:
        if key not in arguments:
            return None
    return arguments

def _index_selection_is_member(
    selected: str,
    options: tuple[Mapping[str, str], ...],
) -> bool:
    """True when selected id is an exact owner-declared identifier.

    Q02-A removes lexical score/veto; membership is the only gate.
    """
    if not selected or not options:
        return False
    return any(
        str(row.get("identifier") or "") == selected for row in options
    )

def _compare_insufficiency_attempt(
    correlation: str,
    *,
    decision: str,
) -> GovernedCapabilityAttempt:
    """Honest insufficiency for compare without typed prior attributes."""
    _logger.info(
        "orchestration stage=prior_continuation "
        "decision=%s correlation_id=%s",
        decision,
        correlation,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id=correlation,
        content=_insufficiency_content(),
        limitations=(
            LIMITATION_PRIOR_TURN_CONTINUATION,
            LIMITATION_INSUFFICIENT_EVIDENCE,
        ),
    )

def _project_surface(
    groups: Mapping[str, CapabilityGroup],
) -> list[tuple[str, ProviderCapability]]:
    """Bounded orchestratable surface: all owner-typed known classes.

    DISCOVERY/READ/ANALYSIS/PREPARE/ACT are visible to the
    selection proposal; UNKNOWN is excluded (never invocable). Class
    visibility is orchestration eligibility only — writes route
    through the governed-write chain downstream.
    """
    surface: list[tuple[str, ProviderCapability]] = []
    for group_key, group in groups.items():
        for capability in group.capabilities:
            if not invocable_in_interactive_phase(
                capability.operation_class
            ):
                continue
            surface.append((group_key, capability))
    return surface[:MAX_SURFACE_ENTRIES]

def _resolve_live_group_key(
    proposed: str,
    groups: Mapping[str, CapabilityGroup],
) -> str | None:
    """Map a model-proposed group id to exactly one live catalog key.

    Exact catalog keys win. A bare ``group_id`` (or a unique
    ``*:group_id`` suffix) is accepted only when membership is
    unambiguous — never by display-name / lexical similarity.
    """
    if not proposed:
        return None
    if proposed in groups:
        return proposed
    matches = [
        key
        for key, group in groups.items()
        if group.group_id == proposed or key.endswith(f":{proposed}")
    ]
    if len(matches) == 1:
        return matches[0]
    return None

def _group_summaries(
    groups: Mapping[str, CapabilityGroup],
    *,
    prior_observation: Mapping[str, Any] | None = None,
) -> str:
    """Fair bounded per-group summaries for stage-1 selection.

    Every provider capability group with live capabilities is
    represented — the budget is shared equally so a large surface can
    never push another group out of the model's view. Runtime
    projection only — nothing is persisted. Provider identity is
    metadata, never a ranking signal. Optional ``prior_observation``
    is untrusted prior-turn text used only to resolve references.
    """
    group_keys = sorted(groups)
    if not group_keys:
        return "[]"
    per_group_budget = max(
        512, MAX_SURFACE_CHARS // len(group_keys)
    )
    summaries = []
    for group_key in group_keys:
        group = groups[group_key]
        capabilities = [
            cap
            for cap in group.capabilities
            if invocable_in_interactive_phase(cap.operation_class)
        ]
        entries = [
            {
                "capability_id": cap.capability_id,
                "remote_name": cap.remote_name,
                "operation_class": cap.operation_class.value,
                "description": (cap.description or "")[
                    :MAX_DESCRIPTION_CHARS
                ],
            }
            for cap in capabilities
        ]
        # Graduated description compaction — every capability stays
        # listed; only description length shrinks under budget.
        body: dict[str, Any] = {
            "capability_group_id": group_key,
            "owner": group.owner_ref,
            "display_name": group.display_name,
            "source_system": group.source.source_system,
            "capabilities": entries,
        }
        for cap_chars in (MAX_DESCRIPTION_CHARS, 80, 32):
            for entry in entries:
                entry["description"] = entry["description"][:cap_chars]
            payload = json.dumps(
                body,
                ensure_ascii=False,
                default=str,
            )
            if len(payload) <= per_group_budget:
                break
        summaries.append(body)
    if prior_observation is None:
        return json.dumps(
            summaries, ensure_ascii=False, default=str
        )
    return json.dumps(
        {
            "capability_groups": summaries,
            "prior_observation": dict(prior_observation),
        },
        ensure_ascii=False,
        default=str,
    )[:MAX_SURFACE_CHARS]

def _capability_payload(
    group: CapabilityGroup,
    *,
    prior_observation: Mapping[str, Any] | None = None,
) -> str:
    """Bounded semantic payload of ONE group's live surface.

    Graduated compaction keeps every capability reachable — entries
    are never dropped, descriptions shrink to fit the budget.
    Optional ``prior_observation`` is untrusted prior-turn text.
    """
    capabilities = [
        cap
        for cap in group.capabilities
        if invocable_in_interactive_phase(cap.operation_class)
    ]
    entries = []
    for cap in capabilities:
        entry: dict[str, Any] = {
            "remote_name": cap.remote_name,
            "description": (cap.description or "")[
                :MAX_DESCRIPTION_CHARS
            ],
            "operation_class": cap.operation_class.value,
            "argument_keys": sorted(_schema_keys(cap)[0]),
            "required": sorted(_schema_keys(cap)[1]),
        }
        # R2: compact role derived only from operation_class — helps
        # coverage-inquiry selection without provider-specific names.
        if cap.operation_class is SpecialistOperationClass.DISCOVERY:
            entry["role"] = "owner_vocabulary_discovery"
        entries.append(entry)
    for cap_chars in (MAX_DESCRIPTION_CHARS, 120, 60, 24, 0):
        for entry in entries:
            entry["description"] = entry["description"][:cap_chars]
        body: Any = entries
        if prior_observation is not None:
            body = {
                "capabilities": entries,
                "prior_observation": dict(prior_observation),
            }
        payload = json.dumps(body, ensure_ascii=False, default=str)
        if len(payload) <= MAX_SURFACE_CHARS:
            break
    return payload[:MAX_SURFACE_CHARS]

# Canonical sensitive credential concepts. Keys are normalized
# (lowercase, separators stripped) before comparison so snake_case,
# kebab-case, camelCase, PascalCase and spaced variants all match.
# Canonical exact names only — substring matching would produce false
# positives on legitimate fields such as token_count or
# authorization_status.

# Deterministic text redaction for untrusted owner content_text.
# Ordered: PEM blocks first, then header lines, bearer material,
# named credential assignments, JWT-shaped values last.






# ---------------------------------------------------------------------------
# presentation.v2 (G3): deterministic Markdown projection of the SAME
# admitted structured payload. Format variant of the existing projection —
# identical keys, values, order, redaction, control-plane exclusion and
# bounds; only the surface syntax differs. Leaf values and keys escape the
# Markdown metacharacters so owner data never becomes formatting
# instructions. Links are never synthesized — no admitted public-URL
# source exists at this boundary.
# ---------------------------------------------------------------------------








def _select_guidance_records(
    structured: object,
    field_labels: FieldLabels | None = None,
) -> list[Mapping]:
    """Shared selection of goal-aligned guidance records (plain and
    Markdown projections consume the same deterministic order)."""
    records = _guidance_section_records(
        structured, field_labels=field_labels
    )
    if not records:
        return []
    selected: list[Mapping[str, str]] = []
    for family in _GUIDANCE_FAMILY_ORDER:
        for record in records:
            if record.get("family") == family and record not in selected:
                selected.append(record)
    substantive = [
        r for r in selected if r.get("family") != "limitations"
    ]
    if not selected or not substantive:
        selected = [
            r for r in records if r.get("family") != "meta"
        ][:6]
    return selected

def _md_guidance_content(
    structured: object,
    *,
    max_chars: int = MAX_RENDER_CONTENT_CHARS,
    owner_truncated: bool = False,
    field_labels: FieldLabels | None = None,
) -> tuple[str, tuple[str, ...]] | None:
    """Markdown variant of ``_deterministic_guidance_content`` — same
    record selection and packing budget; sections become headings."""
    selected = _select_guidance_records(
        structured, field_labels=field_labels
    )
    if not selected:
        return None
    blocks: list[tuple[str, str]] = []
    for record in selected:
        section = record.get("section") or "section"
        excerpt = (record.get("excerpt") or "").strip()
        if not excerpt:
            continue
        blocks.append(
            (
                section,
                "### "
                + _md_leaf(
                    field_display_label(
                        _canonical_key(section), section, field_labels
                    )
                    if field_labels is not None
                    else section
                )
                + "\n\n"
                + _md_leaf(excerpt),
            )
        )
    if not blocks:
        return None
    body, omitted = _pack_guidance_sections(blocks, max_chars)
    if not body:
        return None
    limitations: list[str] = []
    if owner_truncated or omitted:
        limitations.append(LIMITATION_RESULT_TRUNCATED)
    return body, tuple(limitations)

@dataclasses.dataclass(frozen=True, slots=True)
class RenderedSpecialistOutcome:
    """Bounded governed projection of one specialist outcome.

    ``content`` is the existing plain bounded body. ``markdown`` is the
    deterministic ``markdown_safe`` projection of the SAME admitted
    structured payload — present only when structured data drove the
    projection, never for owner free text (Category B), model prose
    (Category C), empty results or lexical guesses.
    """

    content: str
    limitations: tuple[str, ...]
    markdown: str | None = None

def render_specialist_outcome(
    outcome: SpecialistOutcome,
    *,
    input_text: str | None = None,
    invocation_arguments: Mapping[str, Any] | None = None,
    field_labels: FieldLabels | None = None,
) -> tuple[str, tuple[str, ...]]:
    rendered = render_specialist_outcome_rich(
        outcome,
        input_text=input_text,
        invocation_arguments=invocation_arguments,
        field_labels=field_labels,
    )
    return rendered.content, rendered.limitations

def render_specialist_outcome_rich(
    outcome: SpecialistOutcome,
    *,
    input_text: str | None = None,
    invocation_arguments: Mapping[str, Any] | None = None,
    field_labels: FieldLabels | None = None,
) -> RenderedSpecialistOutcome:
    """Bounded truthful rendering of any specialist outcome.

    The remote payload is untrusted content: owner text is preferred and
    size-bounded; structured data is projected verbatim-bounded only
    when no text exists. When ``input_text`` is provided and the
    structured payload is guidance-shaped, a goal-aligned section
    projection is preferred over a metadata-first text dump (I02).
    An empty authoritative result is GROUNDED + empty, never a failure.

    R4/R5: when ``input_text`` carries personal-ticket or count intent
    over a paginated owner envelope, project deterministically before
    any list dump that could equate page size with total.
    """
    limitations = list(outcome.limitations)
    text = _redact_text(outcome.content_text or "").strip()
    structured = outcome.structured
    if isinstance(structured, Mapping) and structured:
        if input_text:
            paginated = _project_paginated_personal_or_count(
                input_text,
                structured,
                invocation_arguments=invocation_arguments,
            )
            if paginated is not None:
                body, extra = paginated
                for item in extra:
                    if item not in limitations:
                        limitations.append(item)
                return RenderedSpecialistOutcome(
                    body, tuple(limitations)
                )
        # I02: guidance-shaped structured data — prefer goal-aligned
        # section projection over truncating embedded content_text from
        # the front (which kept authority/meta and dropped methods).
        if input_text:
            aligned = _deterministic_guidance_content(
                structured,
                owner_truncated=(
                    LIMITATION_RESULT_TRUNCATED in limitations
                ),
                field_labels=field_labels,
            )
            if aligned is not None:
                body, extra = aligned
                for item in extra:
                    if item not in limitations:
                        limitations.append(item)
                md_aligned = _md_guidance_content(
                    structured, field_labels=field_labels
                )
                return RenderedSpecialistOutcome(
                    body,
                    tuple(limitations),
                    markdown=(
                        md_aligned[0][:MAX_RENDER_CONTENT_CHARS]
                        if md_aligned
                        else None
                    ),
                )
        # Owner data lives in the structured payload; generic status
        # text alone (e.g. "Execution completed.") is not an answer.
        # Owners that already embed the same payload in content_text
        # are not duplicated.
        sanitized = _sanitize_renderable(structured)
        full_payload = json.dumps(
            sanitized,
            ensure_ascii=False,
            default=str,
        )
        if text and full_payload.strip() in text:
            markdown_body: str | None = None
            if text.lstrip()[:1] in ("{", "["):
                # content_text is the raw JSON payload itself — render
                # the deterministic business projection instead.
                lines = _business_lines(
                    sanitized, field_labels=field_labels
                ) or (
                    _format_structured(
                        sanitized, field_labels=field_labels
                    )
                )
                body = (
                    "\n".join(lines) if lines else text
                )[:MAX_RENDER_CONTENT_CHARS]
                if lines:
                    md_lines = _md_business_lines(
                        sanitized, field_labels=field_labels
                    ) or (
                        _md_format_structured(
                            sanitized, field_labels=field_labels
                        )
                    )
                    if md_lines:
                        markdown_body = "\n".join(md_lines)[
                            :MAX_RENDER_CONTENT_CHARS
                        ]
            else:
                # Embedded non-JSON text that already contains the
                # structured payload: still prefer structured projection
                # when guidance sections exist — avoids meta-first cut.
                aligned = _deterministic_guidance_content(
                    structured,
                    owner_truncated=(
                        LIMITATION_RESULT_TRUNCATED in limitations
                    ),
                    field_labels=field_labels,
                )
                if aligned is not None:
                    body, extra = aligned
                    for item in extra:
                        if item not in limitations:
                            limitations.append(item)
                    md_aligned = _md_guidance_content(structured)
                    return RenderedSpecialistOutcome(
                        body,
                        tuple(limitations),
                        markdown=(
                            md_aligned[0][:MAX_RENDER_CONTENT_CHARS]
                            if md_aligned
                            else None
                        ),
                    )
                body = text[:MAX_RENDER_CONTENT_CHARS]
            if len(body) >= MAX_RENDER_CONTENT_CHARS and (
                LIMITATION_RESULT_TRUNCATED not in limitations
            ):
                limitations.append(LIMITATION_RESULT_TRUNCATED)
            return RenderedSpecialistOutcome(
                body, tuple(limitations), markdown=markdown_body
            )
        business = _business_lines(
            sanitized, field_labels=field_labels
        )
        markdown_body = None
        if business is not None:
            # Authoritative business payload exists — it is the
            # primary answer. Transport envelope and generic
            # completion text stay out of the user-facing body.
            body_text = "" if _is_generic_status(text) else text
            body = (
                (body_text + "\n\n" if body_text else "")
                + "\n".join(business)
            )
            md_business = _md_business_lines(
                sanitized, field_labels=field_labels
            )
            if md_business:
                markdown_body = (
                    (_md_leaf(body_text) + "\n\n" if body_text else "")
                    + "\n".join(md_business)
                )
        else:
            # Unknown shape — fall back to the generic sanitized
            # structured render rather than discarding data.
            lines = _format_structured(
                sanitized, field_labels=field_labels
            )
            payload = (
                "\n".join(lines)
                if lines
                else full_payload[:MAX_STRUCTURED_RENDER_CHARS]
            )
            body = (
                (text + "\n\n" if text else "")
                + "Resultado do especialista:\n"
                + payload
            )
            if lines:
                markdown_body = (
                    (_md_leaf(text) + "\n\n" if text else "")
                    + "**Resultado do especialista:**\n\n"
                    + "\n".join(
                        _md_format_structured(
                            sanitized, field_labels=field_labels
                        )
                    )
                )
        content = body[:MAX_RENDER_CONTENT_CHARS]
        if len(body) > MAX_RENDER_CONTENT_CHARS:
            if LIMITATION_RESULT_TRUNCATED not in limitations:
                limitations.append(LIMITATION_RESULT_TRUNCATED)
            content += "\n…(resultado parcial — truncado)"
        if markdown_body is not None:
            markdown_body = markdown_body[:MAX_RENDER_CONTENT_CHARS]
        return RenderedSpecialistOutcome(
            content, tuple(limitations), markdown=markdown_body
        )
    if text:
        content = text[:MAX_RENDER_CONTENT_CHARS]
        if len(text) > MAX_RENDER_CONTENT_CHARS:
            if LIMITATION_RESULT_TRUNCATED not in limitations:
                limitations.append(LIMITATION_RESULT_TRUNCATED)
            content += "\n…(resultado parcial — truncado)"
        return RenderedSpecialistOutcome(content, tuple(limitations))
    return RenderedSpecialistOutcome(
        "O especialista retornou um resultado vazio.",
        tuple(limitations),
    )

# ---------------- governed-write orchestration helpers ----------------

_READINESS_NOTE = {
    ProposalReadiness.NOT_READY: (
        "O especialista não concluiu a preparação da alteração."
    ),
    ProposalReadiness.EXPIRED: (
        "A proposta retornada pelo especialista já está expirada."
    ),
    ProposalReadiness.INVALID: (
        "O especialista não retornou uma proposta confirmável."
    ),
    ProposalReadiness.UNKNOWN: (
        "O estado da proposta retornada pelo especialista é "
        "indeterminado."
    ),
}

_OUTCOME_NOTE = {
    WriteOutcomeStatus.VERIFIED: (
        "Alteração aplicada e verificada pela fonte proprietária."
    ),
    WriteOutcomeStatus.EXECUTION_REPORTED: (
        "O especialista reportou execução, mas sem verificação "
        "autoritativa do resultado."
    ),
    WriteOutcomeStatus.OUTCOME_VERIFICATION_FAILED: (
        "O especialista reportou execução, mas a verificação do "
        "resultado falhou."
    ),
    WriteOutcomeStatus.FAILED: "O especialista reportou falha na escrita.",
    WriteOutcomeStatus.UNKNOWN: (
        "O resultado da escrita não pôde ser determinado."
    ),
}

def _find_act_capability(
    group: CapabilityGroup, *, require_proposal_handle: bool
):
    """Structural owner pairing: the ACT capability whose schema
    requires ``proposal_handle`` is the commit step of the owner's
    PREPARE flow — detected live, never registered locally."""
    for capability in group.capabilities:
        if capability.operation_class is not SpecialistOperationClass.ACT:
            continue
        if not require_proposal_handle:
            return capability
        keys, required = _schema_keys(capability)
        if (
            PROPOSAL_HANDLE_FIELD in keys
            or PROPOSAL_HANDLE_FIELD in required
        ):
            return capability
    return None

def _act_arguments(
    act_capability: ProviderCapability,
    proposal_ref: str,
    *,
    confirmed: bool,
) -> dict[str, Any]:
    """Build ACT invocation args from the owner's declared schema.

    Only owner-declared fields are populated: the proposal handle is
    passed back verbatim, ``confirmation`` carries the real execution
    mode — true only after an explicit user confirmation bound to the
    exact preview, false for owner-declared direct execution (DÉLIA
    never fakes a user confirmation) — and an ``idempotency_key`` is
    generated per attempt when declared. Nothing else is invented.
    """
    keys, required = _schema_keys(act_capability)
    declared = keys | required
    arguments: dict[str, Any] = {}
    if PROPOSAL_HANDLE_FIELD in declared:
        arguments[PROPOSAL_HANDLE_FIELD] = proposal_ref
    if "confirmation" in declared:
        arguments["confirmation"] = bool(confirmed)
    if "idempotency_key" in declared:
        arguments["idempotency_key"] = str(uuid.uuid4())
    return arguments

def _preview_render(preview: WriteProposalPreview) -> str:
    """Bounded confirmation surface — deterministic preview only.

    Owner ``content_text`` is never appended: an opaque proposal handle
    embedded mid-sentence has no key context the text redactor can
    detect, so the confirmation surface renders only the bounded
    WriteProposalPreview projection (exact change, resource, impact).
    The raw ``proposal_ref`` is never rendered — digests only.
    """
    sections: list[str] = [
        "Confirmação necessária — revise a alteração exata:"
    ]
    if preview.resource_ref:
        sections.append(f"Recurso: {preview.resource_ref}")
    if isinstance(preview.exact_change, Mapping):
        lines = _format_structured(
            _sanitize_renderable(preview.exact_change)
        )
        if lines:
            sections.append("\n".join(lines))
    if isinstance(preview.consequential_impact, Mapping):
        impact = _format_structured(
            _sanitize_renderable(preview.consequential_impact)
        )
        if impact:
            sections.append("Impacto:\n" + "\n".join(impact))
    body = "\n".join(sections)
    return body[:MAX_RENDER_CONTENT_CHARS]

# Per-call model proposal bound (seconds); the turn deadline can only
# shorten it (LOOP-03R2A).
# DELIA-C3 (doc 103 PO decision): a real model invocation may take up
# to 60s — the previous generic 10s stage cap is superseded. This is a
# per-CALL ceiling, never a mandatory wait: a 1s answer still returns
# in 1s. Stage-specific protections that are not generic call limits
# (admission fast-path cap, conversational fallback reserve) remain.
MODEL_STAGE_TIMEOUT_SECONDS = 60.0
# Do not start a model stage that cannot finish usefully within the
# remaining turn budget (Stage 05 multiturn latency).
MIN_VIABLE_MODEL_STAGE_SECONDS = 2.0
# Reserve wall-clock for the handler conversational fallback after an
# admission/selection miss — prevents cold greetings from burning the
# entire turn inside select_group when stage env cap equals the turn
# budget (live doc 47: ~29s group propose → 504).
CONVERSATIONAL_FALLBACK_RESERVE_SECONDS = 8.0
# Doc 103: no stage-local sub-cap — every logical LLM call shares the
# same governed per-call ceiling (settings.model_stage_timeout_seconds,
# 60s); the global interaction cap and call retry bound the turn.

# CP4 governed stage resume (docs 88 §10.2 / 90 Option B; budget
# approved 22/10/2026): ephemeral, in-request recovery from a
# recoverable model-stage timeout. Governed attempts run under ONE
# monotonic interaction budget — never reset. Doc 103: the artificial
# 30s per-attempt wall is superseded; each attempt simply receives the
# remaining global budget (LLM calls carry their own 60s ceiling and
# up to 3 invocations via governed call retry — retry of the call,
# never of the turn or of a material invoke).
DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS = 300.0
MAX_GOVERNED_ATTEMPTS = 2

INTERACTION_ADMISSION_INSTRUCTION_ID = (
    "delia.capability_orchestration.interaction_admission"
)

# Semantic relevance (plan 125 adendum /
# DELIA-C3-SEMANTIC-RELEVANCE-GOVERNED-RECOVERY-CROSSCUTTING-01): the
# bounded model judgment of whether the returned owner evidence
# corresponds to the stated goal — a proposal, never authority.
GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID = (
    "delia.capability_orchestration.goal_evidence_relevance"
)

# Refactor R1 (plan 125 / M01): instruction *text* lives in the
# governed versioned resource config/orchestration_instructions
# .delpi.json, loaded fail-closed by composition and injected at
# construction — never a second copy inside this module. The
# instruction ids below remain the typed lineage contract; the fused
# capability+goal variant shares the selection instruction id and is
# keyed distinctly in the resource.
CAPABILITY_GOAL_INSTRUCTION_KEY = (
    CAPABILITY_SELECTION_INSTRUCTION_ID + "#with_goal"
)
ORCHESTRATION_INSTRUCTION_KEYS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        CAPABILITY_GOAL_INSTRUCTION_KEY,
        INDEX_PROBE_INSTRUCTION_ID,
        INDEX_SELECT_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        RESOLVER_SELECTION_INSTRUCTION_ID,
        CONTINUATION_INSTRUCTION_ID,
        CLARIFICATION_INSTRUCTION_ID,
        SYNTHESIS_INSTRUCTION_ID,
        NATIVE_ASSESSMENT_INSTRUCTION_ID,
        FOREIGN_SELECTION_INSTRUCTION_ID,
        GOAL_INSTRUCTION_ID,
        COMPARISON_INSTRUCTION_ID,
        CANDIDATE_ARGUMENTS_INSTRUCTION_ID,
        CANDIDATE_SELECTION_INSTRUCTION_ID,
        INTERACTION_ADMISSION_INSTRUCTION_ID,
        GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    }
)

# ------------- progressive activity observation (doc 70 §16) -------------
#
# The request-scoped sink is propagated inside the calling context: the
# orchestrator instance is shared across requests (composition root),
# so per-turn state can NEVER live on `self` — threaded WSGI workers
# run concurrent turns. `attempt` binds the sink once; real
# instrumentation points read it. When no sink is bound (legacy JSON
# mode) every emission is a no-op.
_ACTIVITY_SINK: contextvars.ContextVar[ActivityEventSink | None] = (
    contextvars.ContextVar("delia_activity_sink", default=None)
)

def _emit_activity(
    *,
    phase: ActivityPhase,
    correlation: str | None = None,
    **kwargs: Any,
) -> None:
    sink = _ACTIVITY_SINK.get()
    if sink is None:
        return
    sink.emit(phase=phase, correlation_id=correlation, **kwargs)

# CP4 ephemeral resume: only provably non-mutating invocation
# outcomes may be replayed — DISCOVERY/READ/ANALYSIS. PREPARE/ACT
# (and UNKNOWN or any class not explicitly allowlisted) fail closed
# to the material frontier: once a mutating invocation has STARTED,
# no further attempt may run, so it is never silently re-executed.
_RESUMABLE_OPERATION_CLASSES = frozenset(
    {
        SpecialistOperationClass.DISCOVERY,
        SpecialistOperationClass.READ,
        SpecialistOperationClass.ANALYSIS,
    }
)

@dataclasses.dataclass(slots=True)
class _AttemptCheckpoint:
    """CP4 ephemeral typed checkpoint — one per interaction,
    request-scoped, never persisted, never on the wire.

    Records ONLY what provably completed: model-stage proposals keyed
    by the fingerprint of their exact stage input, and non-mutating
    invocation outcomes keyed by (group, capability, canonical
    arguments). A replayed proposal re-enters the same deterministic
    gates against the fresh live surface — it is data, never
    authority. No chain-of-thought, no tokens, no secrets, no presumed
    permissions, no unsanitized payloads.
    """

    proposals: dict[str, Mapping[str, Any]] = dataclasses.field(
        default_factory=dict
    )
    invoke_outcomes: dict[str, SpecialistOutcome] = dataclasses.field(
        default_factory=dict
    )
    mutating_invoke_started: bool = False

# Request-scoped checkpoint binding — same ContextVar pattern as the
# activity sink: the orchestrator instance is shared across threads,
# so per-interaction state can NEVER live on `self`.
_RESUME_STATE: contextvars.ContextVar[_AttemptCheckpoint | None] = (
    contextvars.ContextVar("delia_resume_checkpoint", default=None)
)

class _TurnCancelled(Exception):
    """CP5/R3: request cancellation was observed inside an attempt —
    the NEXT real operation (model stage or provider invoke) must not
    start. Distinct from a deadline: the cause is the client, not the
    clock."""

# Request-scoped cancellation probe — same ContextVar pattern. The
# transport sets it (NDJSON disconnect event); in-process callers may
# pass any predicate. Never consulted when absent.
_CANCEL_CHECK: contextvars.ContextVar[Callable[[], bool] | None] = (
    contextvars.ContextVar("delia_turn_cancel_check", default=None)
)

def _cancel_observed() -> bool:
    """True only when the request's cancellation probe is bound AND
    reports a disconnect — checked once per real-operation seam."""
    check = _CANCEL_CHECK.get()
    return check is not None and bool(check())

# Prompt 5: request-scoped governed-attempt index (1-based) so a real
# model call can be honestly attributed to the attempt that ran it —
# replayed checkpoint proposals never produce a ledger entry at all.
_ATTEMPT_INDEX: contextvars.ContextVar[int] = contextvars.ContextVar(
    "delia_governed_attempt_index", default=1
)

# Semantic-relevance recovery (plan 125 adendum): at most ONE
# governed READ recovery round per interaction — request-scoped
# guard, never instance state, same ContextVar pattern.
_RELEVANCE_RECOVERY_USED: contextvars.ContextVar[bool] = (
    contextvars.ContextVar(
        "delia_relevance_recovery_used", default=False
    )
)

def _resume_stage_key(
    instruction_id: str,
    input_text: str,
    block_tag: str,
    block_payload: str,
) -> str:
    """Fingerprint one model-stage request. A recorded proposal
    replays only for the byte-identical stage input — a changed live
    context yields a different key and a fresh bounded call."""
    return hashlib.sha256(
        "\x00".join(
            (instruction_id, input_text, block_tag, block_payload)
        ).encode("utf-8")
    ).hexdigest()

def _resume_invoke_key(
    group_id: str, remote_name: str, arguments: Mapping[str, Any]
) -> str:
    """Fingerprint one provider invocation. A recorded outcome
    replays only for the identical capability on the identical group
    with canonically identical validated arguments."""
    canonical = json.dumps(
        arguments, sort_keys=True, ensure_ascii=False, default=str
    )
    return hashlib.sha256(
        "\x00".join((group_id, remote_name, canonical)).encode("utf-8")
    ).hexdigest()

def _group_activity_refs(group: CapabilityGroup) -> dict[str, Any]:
    """Disclosure-safe group projection — the approved specialist
    identity and declared business source only. Never bindings,
    endpoints, or provider internals."""
    return {
        "owner_ref": _activity_owner_ref(
            display_name=group.display_name,
            owner_ref=group.owner_ref,
        ),
        "source_ref": (
            _activity_source_ref(
                source_system=group.source.source_system,
                source_id=group.source.source_id,
            )
            if group.source is not None
            else None
        ),
    }

def _activity_outcome_summary(
    outcome: SpecialistOutcome,
) -> dict[str, Any] | None:
    """Safe result projection: a truthful classification plus a record
    count only when a bounded list is complete enough to count.

    Never treats an unsigned/incomplete page slice (``has_more=True``)
    as ``record_count`` — that was surfacing as "10 registro(s)
    localizado(s)" for a page size. Never infers data from transport
    success; never carries payload.
    """
    if outcome.status is SpecialistResultStatus.PARTIAL:
        return _activity_outcome_ref(status=ActivityOutcomeStatus.PARTIAL)
    envelope = extract_pagination_envelope(outcome.structured)
    if envelope is not None and envelope.has_more is True:
        return _activity_outcome_ref(
            status=ActivityOutcomeStatus.RETURNED_DATA
        )
    records = _synthesis_records(outcome.structured)
    if records:
        return _activity_outcome_ref(
            status=ActivityOutcomeStatus.RETURNED_DATA,
            record_count=len(records),
        )
    has_content = (
        isinstance(outcome.content_text, str)
        and bool(outcome.content_text.strip())
    ) or bool(outcome.structured)
    return _activity_outcome_ref(
        status=(
            ActivityOutcomeStatus.RETURNED_DATA
            if has_content
            else ActivityOutcomeStatus.COMPLETED_NO_DATA
        )
    )

class _StageDeadlineExceeded(Exception):
    """Internal: a governed stage exceeded its deadline or the turn
    budget ran out.

    Propagates to the ``attempt`` boundary which renders the canonical
    deterministic terminal result — a selection/argument/goal stage
    timeout is never a NOT_APPLICABLE that silently falls through to a
    general-model answer (LOOP-03R2A).
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        # "model_timeout" | "turn_budget_exhausted"
        self.reason = reason

class OperationalCapabilityOrchestrator:
    """Provider-neutral governed capability orchestration — no local
    catalog authority.

    Attempts at most one bounded operational plan per turn
    (``MAX_OPERATIONAL_PLAN_STEPS``): capability groups are fetched
    live from every provider, selection is a bounded model proposal
    revalidated against the fresh projection, and when the selected
    capability's schema carries owner-defined vocabulary (opaque
    envelope fields) a required DISCOVERY step runs first so argument
    projection consumes the owner's own declared vocabulary — never an
    invented one. Every invocation still passes the provider's own
    enforcement boundaries plus owner/domain AuthZ. Write-class
    selections route through the generic governed-write chain:
    preview -> pending orchestration state -> structured confirmation
    -> fresh live revalidation -> ACT -> owner-authoritative outcome
    projection.
    """

    def __init__(
        self,
        providers: Sequence[CapabilityProviderPort],
        *,
        invoke_model: InvokeModel | None = None,
        model_ref=None,
        pending_writes: PendingWriteStore | None = None,
        turn_budget_seconds: float = DEFAULT_TURN_BUDGET_SECONDS,
        model_stage_timeout_seconds: float = MODEL_STAGE_TIMEOUT_SECONDS,
        interaction_total_budget_seconds: float = (
            DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS
        ),
        max_governed_attempts: int = 1,
        llm_call_max_attempts: int = 1,
        response_intelligence_enabled: bool = False,
        cri_instruction_clause: str | None = None,
        cri_instruction_version: str | None = None,
        cri_presentation_vocabulary: (
            Mapping[str, Mapping[str, str]] | None
        ) = None,
        field_labels: FieldLabels | None = None,
        orchestration_instructions: Mapping[str, str] | None = None,
    ) -> None:
        self._providers = {p.provider_id: p for p in providers}
        # R1/M01: declarative instruction text is composition-injected
        # from the governed resource; absent in tests -> empty map.
        self._instructions = dict(orchestration_instructions or {})
        self._invoke_model = invoke_model
        self._model_ref = model_ref
        self._pending_writes = pending_writes or PendingWriteStore()
        self._turn_budget_seconds = float(turn_budget_seconds)
        self._model_stage_timeout_seconds = float(
            model_stage_timeout_seconds
        )
        # CP4 (docs 88 §10.2 / 90): ephemeral governed resume — OFF by
        # default (single attempt, legacy behavior). The approved
        # ceiling is two attempts under one monotonic interaction
        # budget; a configured value above the ceiling is clamped,
        # never honored.
        self._interaction_total_budget_seconds = max(
            0.0, float(interaction_total_budget_seconds)
        )
        self._max_governed_attempts = max(
            1, min(int(max_governed_attempts), MAX_GOVERNED_ATTEMPTS)
        )
        # Doc 103 GATE 1: governed per-LOGICAL-CALL retry limit — a
        # mechanism distinct from turn resume above. Defaults to 1
        # (OFF); clamped to the PO-approved ceiling, never raised.
        self._llm_call_max_attempts = max(
            1, min(int(llm_call_max_attempts), LLM_CALL_MAX_ATTEMPTS)
        )
        # CRI E1/E2: composition-resolved response mode — when ON, the
        # goal stage may propose typed answer requirements and the
        # outcome binding edge runs the governed sufficiency
        # assessment. OFF keeps baseline prompts and verdicts
        # byte-identical.
        self._response_intelligence_enabled = bool(
            response_intelligence_enabled
        )
        # CRI E2-R3: the answer-requirements clause is a governed
        # declarative resource injected by composition — never embedded
        # in this module. The CRI enhancement activates only when BOTH
        # the flag and a validated clause are present; a missing or
        # invalid resource degrades the whole mode to baseline.
        clause = (
            cri_instruction_clause.strip()
            if isinstance(cri_instruction_clause, str)
            else ""
        )
        self._cri_active = (
            self._response_intelligence_enabled and bool(clause)
        )
        self._goal_instruction = (
            self._instruction(GOAL_INSTRUCTION_ID) + clause
            if self._cri_active
            else self._instruction(GOAL_INSTRUCTION_ID)
        )
        self._capability_goal_instruction = (
            self._instruction(CAPABILITY_GOAL_INSTRUCTION_KEY)
            + clause
            if self._cri_active
            else self._instruction(CAPABILITY_GOAL_INSTRUCTION_KEY)
        )
        self._cri_instruction_version = (
            f"{SELECTION_INSTRUCTION_VERSION}+cri.{cri_instruction_version}"
            if self._cri_active and cri_instruction_version
            else SELECTION_INSTRUCTION_VERSION
        )
        # CRI E3: the grounded conversational composer needs its own
        # governed declarative vocabulary — a different consumer, a
        # different resource. It activates only when CRI is active AND
        # a validated vocabulary was injected; without it the verdict
        # still runs but presentation stays at the baseline render.
        self._cri_vocabulary = cri_presentation_vocabulary
        # Governed presentation labels resolve field names in every
        # path (CRI, detail, list, comparison) — independent of the
        # CRI activation flag; absent the fallback stays neutral.
        self._field_labels = dict(field_labels or {})
        self._cri_present_active = (
            self._cri_active
            and isinstance(cri_presentation_vocabulary, Mapping)
            and bool(cri_presentation_vocabulary)
        )

    def _instruction(self, key: str) -> str:
        """Declarative instruction text by resource key — injected,
        never authored here; empty only in tests without the resource."""
        return self._instructions.get(key, "")

    def attempt(
        self,
        input_text: str,
        *,
        correlation_id: str | None = None,
        actor_user_id: str | None = None,
        session_id: str | None = None,
        confirmation: Mapping[str, Any] | None = None,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        max_execution_stage: str | None = None,
        turn_deadline: TurnDeadline | None = None,
        activity_sink: ActivityEventSink | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> GovernedCapabilityAttempt:
        """Attempt boundary: one monotonic interaction budget governs
        every stage of every governed attempt.

        A model-stage timeout or an exhausted turn budget is a governed
        orchestration failure — it terminates as PROCESSING_TIMEOUT
        (deterministic, HYPOTHESIS-class at the interaction layer),
        never as SOURCE_UNAVAILABLE when no authoritative source was
        consulted (doc 88 CP2), and can NEVER degrade into a
        general-model answer (LOOP-03R2A).

        CP4 (docs 88 §10.2 / 90): when enabled, a recoverable timeout
        triggers ONE further bounded attempt on the same interaction.
        The typed checkpoint replays only what provably completed;
        every deterministic gate re-runs against the fresh live
        surface. Resume is refused when the budget is gone, the
        attempt ceiling is reached, the request was cancelled, a
        mutating invoke already started, or the turn is a typed
        confirmation — material work is never re-executed.
        """
        correlation = correlation_id or str(uuid.uuid4())
        first_deadline = turn_deadline or TurnDeadline.start(
            self._turn_budget_seconds
        )
        # The checkpoint exists only when recovery is enabled for this
        # interaction — confirmation turns and legacy single-attempt
        # mode never checkpoint, never resume.
        checkpoint = (
            _AttemptCheckpoint()
            if self._max_governed_attempts > 1 and confirmation is None
            else None
        )
        # Bind the request-scoped activity sink, resume checkpoint and
        # cancellation probe for this call's context only — the
        # instance is shared across concurrent turns.
        sink_token = _ACTIVITY_SINK.set(activity_sink)
        resume_token = _RESUME_STATE.set(checkpoint)
        cancel_token = _CANCEL_CHECK.set(cancel_check)
        relevance_token = _RELEVANCE_RECOVERY_USED.set(False)
        try:
            # Monotonic interaction end: anchored at the REAL start of
            # the interaction's clock (TurnDeadline.start), never at
            # this boundary — time already consumed before the
            # orchestrator counts against the approved total. Each
            # further attempt receives the remaining global budget —
            # no artificial per-attempt wall (doc 103).
            interaction_start = (
                first_deadline.started_at
                if first_deadline.started_at is not None
                else first_deadline.clock()
            )
            interaction_end = (
                interaction_start + self._interaction_total_budget_seconds
            )
            deadline = first_deadline
            attempts = 0
            while True:
                try:
                    _ATTEMPT_INDEX.set(attempts + 1)
                    completed = self._attempt(
                        input_text,
                        correlation=correlation,
                        actor_user_id=actor_user_id,
                        session_id=session_id,
                        confirmation=confirmation,
                        workspace_context=workspace_context,
                        prior_turns=prior_turns,
                        max_execution_stage=max_execution_stage,
                        deadline=deadline,
                    )
                    # Presentation-only accounting: how many governed
                    # attempts this turn actually needed. Never
                    # authority — resume stays deterministic.
                    return dataclasses.replace(
                        completed, governed_attempts=attempts + 1
                    )
                except _StageDeadlineExceeded as exc:
                    reason = exc.reason
                except TurnBudgetExhausted:
                    reason = "turn_budget_exhausted"
                except _TurnCancelled:
                    reason = "cancelled"
                attempts += 1
                _logger.info(
                    "orchestration stage=turn_budget decision=%s "
                    "attempt=%d correlation_id=%s",
                    reason,
                    attempts,
                    correlation,
                )
                remaining = interaction_end - deadline.clock()
                # Doc 103: no artificial per-attempt wall — an attempt
                # receives the remaining global budget; the 60s per-call
                # ceiling and 3-call retry bound model work inside it.
                per_attempt = max(0.0, remaining)
                if (
                    checkpoint is None
                    or attempts >= self._max_governed_attempts
                    or checkpoint.mutating_invoke_started
                    or (cancel_check is not None and cancel_check())
                    or per_attempt < MIN_VIABLE_MODEL_STAGE_SECONDS
                    # A model_timeout reaching this boundary already
                    # consumed the governed per-call retry budget —
                    # resuming the turn would re-invoke the same
                    # logical call a forbidden fourth time. Only
                    # budget exhaustion resumes the turn (checkpoint
                    # replays provably completed work).
                    or reason == "model_timeout"
                ):
                    # Stage 6 attribution: which responsibility ended
                    # the turn — model stage timeout, shared budget
                    # exhaustion or client cancellation — recorded in
                    # coarse terms for the observability projection.
                    term_ledger = current_call_ledger()
                    if term_ledger is not None:
                        term_ledger.record_terminal_timeout(
                            {
                                "model_timeout": "model",
                                "turn_budget_exhausted": "budget",
                                "cancelled": "cancelled",
                            }.get(reason, "budget")
                        )
                    return GovernedCapabilityAttempt(
                        status=GovernedCapabilityStatus.PROCESSING_TIMEOUT,
                        correlation_id=correlation,
                        error_code=reason,
                        governed_attempts=attempts,
                    )
                # A new bounded attempt on the SAME interaction: fresh
                # deadline inside the monotonic budget; the checkpoint
                # replays only what provably completed.
                deadline = TurnDeadline(
                    ends_at=deadline.clock() + per_attempt,
                    clock=deadline.clock,
                )
                _emit_activity(
                    phase=ActivityPhase.CONTINUING,
                    correlation=correlation,
                )
                _logger.info(
                    "orchestration stage=governed_resume "
                    "decision=continue attempt=%d remaining_ms=%d "
                    "correlation_id=%s",
                    attempts + 1,
                    int(remaining * 1000),
                    correlation,
                )
        finally:
            _ACTIVITY_SINK.reset(sink_token)
            _RESUME_STATE.reset(resume_token)
            _CANCEL_CHECK.reset(cancel_token)
            _RELEVANCE_RECOVERY_USED.reset(relevance_token)

    def _attempt(
        self,
        input_text: str,
        *,
        correlation: str,
        actor_user_id: str | None = None,
        session_id: str | None = None,
        confirmation: Mapping[str, Any] | None = None,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        max_execution_stage: str | None = None,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt:
        correlation = correlation
        # Request-scoped execution ceiling (LOOP-03R1): "prepare" caps
        # the governed chain at PREPARE — it can only reduce authority.
        prepare_only = max_execution_stage == "prepare"
        # LOOP-03R2A: no stage — not even the live surface listing —
        # may start once the shared turn budget is exhausted.
        deadline.check("turn_start")
        _emit_activity(phase=ActivityPhase.CONTEXTUALIZING, correlation=correlation)
        if confirmation is not None:
            return self._attempt_confirmation(
                confirmation,
                actor_user_id=actor_user_id,
                correlation=correlation,
                prepare_only=prepare_only,
                deadline=deadline,
            )

        # SEM recovery: cheap typed admission BEFORE listing providers /
        # select_group. Skips expensive catalog+selection when the turn
        # is conversational (doc 47 cold greeting FAIL). A typed
        # surface_inquiry still consults the LIVE surface listing — the
        # answer is a deterministic projection of it, never a model
        # list and never an owner invocation.
        admission_class, admission_owner_required = (
            self._admit_conversational_turn(
                input_text,
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        )
        # DELIA-C3-S5-REWORK (D8): when admission declared an owner
        # need, any post-admission NOT_APPLICABLE fizzle is marked so
        # the interaction layer answers with deterministic
        # insufficiency, never free-form model prose. When admission
        # could not run (no model / exhausted budget) the marker
        # stays None and the existing conversational fallback applies.
        unbound_outcome = (
            OWNER_PATH_UNBOUND if admission_owner_required else None
        )
        if admission_class == "surface_inquiry":
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=surface_inquiry correlation_id=%s",
                correlation,
            )
            groups, failures = self._groups(correlation, deadline)
            return self._surface_inquiry_attempt(
                groups, failures, correlation
            )
        if admission_class is not None:
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=conversational class=%s correlation_id=%s",
                admission_class,
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=EARLY_CONVERSATIONAL_ADMISSION,
            )

        groups, failures = self._groups(correlation, deadline)
        surface = _project_surface(groups)
        if not surface:
            # No orchestratable surface observed. When at least one
            # provider group could not be consulted a capability may
            # have been needed — truthful source-unavailable beats
            # a silent NOT_APPLICABLE.
            status = (
                GovernedCapabilityStatus.SOURCE_UNAVAILABLE
                if failures
                else GovernedCapabilityStatus.NOT_APPLICABLE
            )
            return GovernedCapabilityAttempt(
                status=status,
                correlation_id=correlation,
                error_code=(failures[0] if failures else None),
            )

                # Stage 05 / I01 multiturn: interpret the goal first. When the
        # model declares prior evidence sufficient — or a provider-
        # neutral continuity probe applies — transform prior OBSERVATION
        # content without a new owner call. Never AuthZ reuse; never
        # fresh grounding from conversation history.
        goal: OperationalCapabilityOrchestrator._TurnGoal | None = None
        if prior_turns:
            goal = self._understand_goal(
                input_text,
                correlation,
                workspace_context,
                prior_turns,
                deadline,
            )
            if goal.goal_class != "create_or_modify":
                prior_turn = self._prior_result_turn(prior_turns)
                if (
                    prior_turn is None
                    or prior_turn.epistemic_class
                    is not EpistemicClass.OBSERVATION
                ):
                    if goal.prior_evidence_sufficient:
                        _logger.info(
                            "orchestration stage=prior_continuation "
                            "decision=prior_not_observation "
                            "correlation_id=%s",
                            correlation,
                        )
                else:
                    committed = goal.prior_evidence_sufficient
                    probe = (
                        not committed
                        and _prior_transform_probe_eligible(
                            input_text, goal
                        )
                    )
                    if committed or probe:
                        continued = self._prior_continuation_attempt(
                            input_text,
                            prior_turns,
                            correlation,
                            deadline,
                            business_subject=goal.business_subject,
                            comparison_requested=(
                                goal.comparison_requested
                                or goal.goal_class
                                in {"compare", "analyze"}
                            ),
                        )
                        if continued is not None:
                            if committed:
                                return continued
                            if (
                                LIMITATION_INSUFFICIENT_EVIDENCE
                                not in continued.limitations
                            ):
                                _logger.info(
                                    "orchestration stage="
                                    "prior_continuation "
                                    "decision=probe_accepted "
                                    "correlation_id=%s",
                                    correlation,
                                )
                                return continued
                            typed_continuity = (
                                goal.comparison_requested
                                or goal.goal_class in {
                                    "compare",
                                    "analyze",
                                }
                            )
                            # Compare/analyze already spent a synthesis
                            # stage on prior evidence — do not burn the
                            # remaining 30s budget on owner reselection
                            # (L5 timeout class). Methodology cue probes
                            # may still fall through when headroom remains.
                            if (
                                typed_continuity
                                or not self._budget_allows_resolver(
                                    deadline
                                )
                            ):
                                _logger.info(
                                    "orchestration stage="
                                    "prior_continuation "
                                    "decision=probe_insufficient_stop "
                                    "remaining_ms=%d correlation_id=%s",
                                    int(
                                        deadline.remaining_seconds() * 1000
                                    ),
                                    correlation,
                                )
                                return continued
                            _logger.info(
                                "orchestration stage="
                                "prior_continuation "
                                "decision=probe_insufficient "
                                "fallthrough correlation_id=%s",
                                correlation,
                            )

        # Selection must not receive full prior transcript (Stage 05
        # latency). A bounded untrusted prior_observation may be embedded in the
        # capability catalog payload; InvokeModel prior_turns stay empty.
        # I02-R3B: when goal is still unknown (cold start), capability
        # selection may also carry a typed turn-goal in one proposal.
        selection = self._select_target(
            input_text,
            groups,
            workspace_context,
            prior_turns,
            deadline,
            correlation=correlation,
            interpret_goal=(goal is None),
        )
        if selection is None or selection[0] == "not_applicable":
            # Group applicable=false / no model: conversational path.
            _logger.info(
                "orchestration stage=target_selection "
                "decision=not_applicable correlation_id=%s",
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
            )
        if selection[0] == "not_applicable_capability":
            # A group path was attempted but the capability stage bound
            # none — marked so the interaction layer answers with
            # deterministic insufficiency, never free-form prose.
            _logger.info(
                "orchestration stage=target_selection "
                "decision=capability_unbound correlation_id=%s",
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome,
            )
        if selection[0] == "inconclusive":
            # Group was chosen (or invented) but capability could not be
            # bound — bounded ask-back, never a second free-form burn.
            _logger.info(
                "orchestration stage=target_selection decision=none "
                "correlation_id=%s",
                correlation,
            )
            if self._invoke_model is not None and self._model_ref is not None:
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
                    correlation_id=correlation,
                    content=_SELECTION_INCONCLUSIVE_CONTENT,
                )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome,
            )
        _, group_key, descriptor, selected_goal = selection
        group = groups[group_key]
        remote_name = descriptor.remote_name
        _logger.info(
            "orchestration stage=target_selection decision=selected "
            "group=%s capability=%s class=%s correlation_id=%s",
            group_key,
            remote_name,
            descriptor.operation_class.value,
            correlation,
        )
        _emit_activity(
            phase=ActivityPhase.CAPABILITY_SELECTED,
            correlation=correlation,
            capability_ref=_activity_capability_ref(
                remote_name=remote_name,
                operation_class=descriptor.operation_class.value,
            ),
            **_group_activity_refs(group),
        )

        # Bounded turn-goal interpretation (C3-INTELLIGENCE-LOOP-03R1):
        # reuse multiturn goal, else typed fields from capability
        # selection (I02-R3B), else a dedicated turn_goal proposal.
        if goal is None:
            if selected_goal is not None:
                goal = selected_goal
                _logger.info(
                    "orchestration stage=goal_understanding "
                    "decision=typed_with_capability class=%s "
                    "correlation_id=%s",
                    goal.goal_class,
                    correlation,
                )
            else:
                goal = self._understand_goal(
                    input_text,
                    correlation,
                    workspace_context,
                    prior_turns,
                    deadline,
                )

        # Semantic finality gate (C3-CONVERSATIONAL-INTELLIGENCE-02,
        # R1 §6.174): the validated turn goal is the only semantic
        # statement of what the user wants. A write-class target is
        # only compatible with a DECLARED action goal — reconcile
        # deterministically BEFORE any governed-write stage runs.
        # An UNINTERPRETED goal (absent/invalid proposal) is never
        # proof of a change request: it becomes a proportional
        # ask-back, like a declared ambiguity. A declared non-action
        # goal demotes the selection to the owner's non-mutating
        # surface (one bounded reselection reusing the same
        # selection stage), failing closed when nothing applies.
        if descriptor.operation_class in _WRITE_OPERATION_CLASSES:
            if not goal.declared or goal.goal_class == "clarify":
                _logger.info(
                    "orchestration stage=intent_reconciliation "
                    "decision=%s class=%s correlation_id=%s",
                    "clarify" if goal.declared else "uninterpreted",
                    descriptor.operation_class.value,
                    correlation,
                )
                return GovernedCapabilityAttempt(
                    status=(
                        GovernedCapabilityStatus.CLARIFICATION_REQUIRED
                    ),
                    correlation_id=correlation,
                    content=_INTENT_CLARIFICATION_CONTENT,
                )
            if goal.goal_class != "create_or_modify":
                _logger.info(
                    "orchestration stage=intent_reconciliation "
                    "decision=demote class=%s goal=%s correlation_id=%s",
                    descriptor.operation_class.value,
                    goal.goal_class,
                    correlation,
                )
                _demote_status, demoted = self._select_capability(
                    input_text,
                    dataclasses.replace(
                        group,
                        capabilities=tuple(
                            cap
                            for cap in group.capabilities
                            if cap.operation_class
                            not in _WRITE_OPERATION_CLASSES
                        ),
                    ),
                    workspace_context,
                    prior_turns,
                    correlation=correlation,
                    deadline=deadline,
                )
                if demoted is None:
                    return GovernedCapabilityAttempt(
                        status=GovernedCapabilityStatus.NOT_APPLICABLE,
                        correlation_id=correlation,
                        error_code="intent_target_incompatible",
                        admission_outcome=unbound_outcome,
                    )
                descriptor = demoted
                remote_name = demoted.remote_name
                _logger.info(
                    "orchestration stage=intent_reconciliation "
                    "decision=reselected capability=%s class=%s "
                    "correlation_id=%s",
                    remote_name,
                    descriptor.operation_class.value,
                    correlation,
                )

        # User-declared execution bound (C3-CI-02R1): an explicit
        # "prepare, do not apply" restriction stated in the request
        # text reduces the effective turn ceiling — it can never
        # raise it, and it composes with the request-scoped
        # max_execution_stage (most restrictive wins).
        prepare_only = prepare_only or (
            goal.execution_bound == "prepare_only"
        )

        # Staged semantic path selection (C3-INTELLIGENCE-LOOP-02R1):
        # native sufficiency is assessed BEFORE any foreign surface is
        # exposed — the assessment sees only the target group. Foreign
        # capability selection runs only when the assessment justifies
        # it (required evidence or explicit corroboration).
        # Adaptive skip (not READ⇒skip): when the validated goal already
        # declares comparison_requested, corroborate is forced for
        # non-write targets — the native-assessment model call is
        # redundant. Write targets still assess because enrichment
        # (foreign_evidence_required) remains a valid path.
        path_mode = "native"
        foreign_cap: ProviderCapability | None = None
        foreign_group: CapabilityGroup | None = None
        foreign_key: str | None = None
        if len(groups) > 1:
            non_write_target = descriptor.operation_class not in (
                SpecialistOperationClass.PREPARE,
                SpecialistOperationClass.ACT,
            )
            if non_write_target and goal.comparison_requested:
                assessment = "corroboration_requested"
                _logger.info(
                    "orchestration stage=native_assessment "
                    "decision=skip_comparison_declared correlation_id=%s",
                    correlation,
                )
            else:
                assessment = self._assess_native_path(
                    input_text,
                    group,
                    descriptor,
                    correlation,
                    workspace_context,
                    prior_turns,
                    goal=goal,
                    deadline=deadline,
                )
            if (
                assessment == "corroboration_requested"
                or goal.comparison_requested
            ) and non_write_target:
                path_mode = "corroborate"
            elif assessment == "foreign_evidence_required":
                path_mode = "enrichment"
            if path_mode != "native":
                found = self._select_foreign_capability(
                    input_text,
                    groups,
                    group_key,
                    path_mode,
                    correlation,
                    workspace_context,
                    prior_turns,
                    deadline,
                )
                if found is None:
                    if path_mode == "enrichment":
                        # Required foreign evidence has no valid source
                        # — never run the target as if native sufficed.
                        _logger.info(
                            "orchestration stage=semantic_path "
                            "decision=foreign_required_invalid "
                            "correlation_id=%s",
                            correlation,
                        )
                        return GovernedCapabilityAttempt(
                            status=GovernedCapabilityStatus.NOT_APPLICABLE,
                            correlation_id=correlation,
                            error_code="invalid_foreign_selection",
                            admission_outcome=unbound_outcome,
                        )
                    # corroborate: the second source could not be
                    # selected — the primary result still runs and the
                    # comparison terminal marks it truthfully.
                else:
                    foreign_key, foreign_cap = found
                    foreign_group = groups[foreign_key]

        # Bounded operational plan (§6.131 R1): when the selected
        # capability is an opaque envelope, the owner's DISCOVERY
        # capability must supply the real operation vocabulary before
        # arguments are projected — otherwise the model would invent
        # owner-specific terms and the owner would reject the call.
        # RW-S03-01: required free strings alone never open this path.
        discovery = (
            _discovery_capability(group)
            if _requires_owner_vocabulary(descriptor)
            and not _is_candidate_bound(descriptor)
            else None
        )
        # Governed self-index probe: same READ/ANALYSIS capability may
        # be invoked empty first when schema allows and the model
        # proposes probe_index after reading the owner contract.
        # Never competes with opaque-envelope DISCOVERY; never ACT.
        self_index = (
            discovery is None
            and not _is_candidate_bound(descriptor)
            and _eligible_self_index_probe(descriptor)
        )
        _logger.info(
            "orchestration stage=plan decision=%s envelope=%s "
            "discovery=%s self_index_eligible=%s correlation_id=%s",
            (
                "with_discovery"
                if discovery is not None
                else ("self_index_candidate" if self_index else "direct")
            ),
            _requires_owner_vocabulary(descriptor),
            discovery.remote_name if discovery is not None else "",
            self_index,
            correlation,
        )
        plan = self._build_plan(
            input_text,
            descriptor,
            group,
            discovery,
            correlation,
            foreign=foreign_cap,
            foreign_group=foreign_group,
        )
        if plan is None:
            # The deterministic plan failed validation — fail closed.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                correlation_id=correlation,
                error_code="plan_validation_failed",
            )
        # Decision-path telemetry (C3-T7 reuse): classify the accepted
        # plan as FAST / OPERATIONAL / REASONING from proven routing
        # facts only. Never authority; never invents sufficiency.
        invocable_count = sum(
            1
            for cap in group.capabilities
            if invocable_in_interactive_phase(cap.operation_class)
        )
        arg_keys, arg_required = _schema_keys(descriptor)
        no_model_args = not (arg_keys - ORCHESTRATED_FIELDS) and not (
            arg_required - ORCHESTRATED_FIELDS
        )
        complex_investigation = path_mode != "native" or (
            goal is not None and goal.comparison_requested
        )
        fast_surface = (
            len(groups) == 1
            and invocable_count == 1
            and discovery is None
            and no_model_args
            and path_mode == "native"
            and not complex_investigation
        )
        routing = select_decision_path(
            DecisionPathInput(
                request_class="capability_orchestration",
                authoritative_deterministic_rule_available=fast_surface,
                authoritative_context_sufficient=fast_surface,
                structured_context_sufficient=True,
                complex_investigation_required=complex_investigation,
                required_evidence_missing=False,
                evidence_conflict_present=False,
            )
        )
        _logger.info(
            "orchestration stage=decision_path decision=%s path=%s "
            "correlation_id=%s",
            routing.status.value,
            (
                routing.selected_path.value
                if routing.selected_path is not None
                else ""
            ),
            correlation,
        )

        owner_evidence: str | None = None
        discovery_structured: Mapping[str, Any] | None = None
        discovery_ran = False
        self_index_ran = False
        optional_index_probe_skipped_budget = False
        index_structured: Mapping[str, Any] | None = None
        index_declared_ids: frozenset[str] | None = None
        if discovery is not None:
            discovery_arguments, _ = self._build_arguments(
                input_text,
                discovery,
                workspace_context,
                prior_turns,
                deadline,
            )
            if discovery_arguments is not None:
                try:
                    discovery_outcome = self._invoke(
                        group,
                        discovery.remote_name,
                        discovery_arguments,
                        correlation,
                        deadline,
                    )
                except CapabilityProviderError as exc:
                    _logger.info(
                        "orchestration stage=discovery decision=error "
                        "error_code=%s correlation_id=%s",
                        exc.code,
                        correlation,
                    )
                    return _error_attempt(correlation, exc)
                owner_evidence = _bound_owner_evidence(discovery_outcome)
                if isinstance(discovery_outcome.structured, Mapping):
                    discovery_structured = discovery_outcome.structured
                discovery_ran = True
                self._log_plan(plan, correlation, discovery_ran=True)
            else:
                self._log_plan(plan, correlation, discovery_ran=False)
        elif self_index:
            # Owner-declared omit→index authorizes empty INDEX READ
            # without a model probe. Optional model probe runs only when
            # TurnDeadline still has headroom for probe + index_select +
            # presentation floor (I02-R2). Never catch an exhausted
            # global deadline to continue.
            contract_index = _contract_declares_omit_returns_index(
                descriptor
            )
            run_index = False
            if contract_index:
                run_index = True
            elif self._budget_allows_optional_index_probe(deadline):
                run_index = self._propose_index_probe(
                    input_text,
                    descriptor,
                    workspace_context,
                    prior_turns,
                    correlation,
                    deadline,
                )
            else:
                optional_index_probe_skipped_budget = True
                _logger.info(
                    "orchestration stage=index_probe "
                    "decision=skip_budget remaining_ms=%d "
                    "correlation_id=%s",
                    int(deadline.remaining_seconds() * 1000),
                    correlation,
                )
            if run_index:
                # INDEX READ → later GUIDANCE READ (same capability).
                # Empty arguments are schema-valid only when eligibility
                # already proved no required fields.
                empty_args = _validate_instance(
                    {}, descriptor.input_schema
                )
                if empty_args is None:
                    _logger.info(
                        "orchestration stage=index_probe "
                        "decision=empty_args_invalid correlation_id=%s",
                        correlation,
                    )
                else:
                    try:
                        index_outcome = self._invoke(
                            group,
                            descriptor.remote_name,
                            empty_args,
                            correlation,
                            deadline,
                        )
                    except CapabilityProviderError as exc:
                        _logger.info(
                            "orchestration stage=index_probe "
                            "decision=error error_code=%s "
                            "correlation_id=%s",
                            exc.code,
                            correlation,
                        )
                        return _error_attempt(correlation, exc)
                    owner_evidence = _bound_owner_evidence(index_outcome)
                    discovery_ran = True
                    self_index_ran = True
                    if isinstance(index_outcome.structured, Mapping):
                        index_structured = index_outcome.structured
                        field_keys = _optional_unconstrained_string_keys(
                            descriptor
                        )
                        index_declared_ids = _index_declared_identifiers(
                            index_structured,
                            field_keys,
                        )
                    _logger.info(
                        "orchestration stage=index_probe "
                        "decision=ok capability=%s identifiers=%d "
                        "correlation_id=%s",
                        descriptor.remote_name,
                        len(index_declared_ids or ()),
                        correlation,
                    )
                    self._log_plan(
                        plan, correlation, discovery_ran=True
                    )

        # Missing-input preflight (LOOP-03R1, D08): when a foreign step
        # is planned, the target's preliminary arguments and the
        # same-owner resolver run BEFORE any foreign provider call. A
        # business subject the user must supply — an identifier a
        # foreign source can never prove, or a field the foreign
        # capability itself requires — is clarified first and foreign
        # calls stay 0. Fields legitimately filled by foreign evidence
        # do not block fan-out.
        preliminary_arguments: dict[str, Any] | None = None
        if foreign_cap is not None:
            pre_args, pre_missing = self._build_arguments(
                input_text,
                descriptor,
                workspace_context,
                owner_evidence=owner_evidence,
                business_subject=goal.business_subject,
                prior_turns=prior_turns,
                deadline=deadline,
            )
            if pre_args is not None:
                # Same canonical rule as the post-foreign check: an
                # identifier with no provenance is invented — demote
                # it BEFORE any foreign call (never fan out to
                # discover a subject the user has not identified).
                pre_unproven = _unproven_identifier_inputs(
                    pre_args,
                    descriptor,
                    input_text,
                    workspace_context,
                    owner_evidence,
                )
                if pre_unproven:
                    pre_args = None
                    pre_missing = tuple(
                        dict.fromkeys(pre_missing + pre_unproven)
                    )[:MAX_MISSING_INPUTS]
            if pre_args is None and pre_missing:
                if self._budget_allows_resolver(deadline):
                    preflight = self._resolve_missing_inputs(
                        input_text,
                        descriptor,
                        pre_missing,
                        group,
                        discovery,
                        correlation,
                        workspace_context,
                        prior_turns,
                        deadline,
                    )
                else:
                    _logger.info(
                        "orchestration stage=preflight "
                        "decision=resolver_skipped_budget "
                        "remaining_ms=%d correlation_id=%s",
                        int(deadline.remaining_seconds() * 1000),
                        correlation,
                    )
                    preflight = self._Resolution()
                if preflight.attempt is not None:
                    # Resolver ambiguity/error clarifies BEFORE the
                    # foreign fan-out — never invoke a second owner to
                    # discover a subject the user has not identified.
                    return preflight.attempt
                if preflight.arguments is not None:
                    pre_args = preflight.arguments
                    if preflight.owner_evidence:
                        owner_evidence = preflight.owner_evidence
                if pre_args is None:
                    foreign_required = _schema_keys(foreign_cap)[1]
                    canon_foreign = {
                        _canonical_key(field)
                        for field in foreign_required
                    }
                    user_required = [
                        name
                        for name in pre_missing
                        if _canonical_key(name).endswith("id")
                        or _canonical_key(name) in canon_foreign
                    ]
                    if user_required:
                        _logger.info(
                            "orchestration stage=preflight "
                            "decision=clarify_before_foreign "
                            "missing=%d correlation_id=%s",
                            len(user_required),
                            correlation,
                        )
                        return GovernedCapabilityAttempt(
                            status=(
                                GovernedCapabilityStatus
                                .CLARIFICATION_REQUIRED
                            ),
                            correlation_id=correlation,
                            content=self._clarification_question(
                                input_text,
                                tuple(user_required),
                                descriptor,
                                correlation,
                                deadline,
                            ),
                        )
            preliminary_arguments = pre_args

        # Bounded foreign evidence step (LOOP-02R1): one non-mutating
        # capability of a different group runs through the SAME owner
        # workflow mechanics as a selected target (`_invoke_selected`
        # — candidate-bound discovery flows included). Enrichment is
        # REQUIRED evidence: failure or unbuildable input fails closed
        # (clarification or source-unavailable), never a silent native
        # success. Corroboration failure degrades to a truthful
        # comparison-source-unavailable marker on the primary result.
        foreign_outcome: SpecialistOutcome | None = None
        foreign_evidence: str | None = None
        if foreign_cap is not None and foreign_group is not None:
            foreign_result = self._invoke_foreign_evidence(
                input_text,
                foreign_key or "",
                foreign_cap,
                foreign_group,
                correlation,
                workspace_context,
                prior_turns,
                deadline,
                goal=goal,
            )
            if foreign_result.outcome is None and (
                path_mode == "enrichment"
            ):
                if foreign_result.missing_inputs:
                    return GovernedCapabilityAttempt(
                        status=(
                            GovernedCapabilityStatus.CLARIFICATION_REQUIRED
                        ),
                        correlation_id=correlation,
                        content=self._clarification_question(
                            input_text,
                            foreign_result.missing_inputs,
                            foreign_cap,
                            correlation,
                            deadline,
                        ),
                    )
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                    correlation_id=correlation,
                    error_code="foreign_source_unavailable",
                )
            foreign_outcome = foreign_result.outcome
            foreign_evidence = foreign_result.evidence

        if (
            self_index_ran
            and index_structured is not None
            and index_declared_ids
            and preliminary_arguments is None
        ):
            # INDEX → exact identifier selection → guidance READ.
            # Structured owner ids are authoritative; substring matches
            # in descriptive text never prove provenance.
            bound = self._bind_arguments_from_index(
                input_text,
                descriptor,
                index_structured,
                index_declared_ids,
                workspace_context,
                prior_turns,
                correlation,
                deadline,
            )
            if bound is not None:
                arguments, missing_inputs = bound, ()
            else:
                arguments, missing_inputs = None, tuple(
                    _optional_unconstrained_string_keys(descriptor)[
                        :MAX_MISSING_INPUTS
                    ]
                )
        elif preliminary_arguments is not None and foreign_evidence is None:
            # Preflight already produced validated target arguments and
            # no foreign evidence arrived to enrich them — reuse the
            # validated result instead of a duplicate proposal (§42).
            arguments, missing_inputs = preliminary_arguments, ()
        else:
            arguments, missing_inputs = self._build_arguments(
                input_text,
                descriptor,
                workspace_context,
                owner_evidence=owner_evidence,
                foreign_evidence=foreign_evidence,
                business_subject=goal.business_subject,
                prior_turns=prior_turns,
                deadline=deadline,
            )
        _logger.info(
            "orchestration stage=arguments decision=%s "
            "missing=%d correlation_id=%s",
            "built" if arguments is not None else (
                "missing_inputs" if missing_inputs else "none"
            ),
            len(missing_inputs),
            correlation,
        )
        if arguments is not None:
            unproven = _unproven_identifier_inputs(
                arguments,
                descriptor,
                input_text,
                workspace_context,
                owner_evidence,
            )
            if unproven:
                # An identifier the model produced with no provenance
                # is an invented id — demote it to a missing input so
                # the generic resolver (or clarification) handles it.
                _logger.info(
                    "orchestration stage=arguments "
                    "decision=unproven_identifier fields=%d "
                    "correlation_id=%s",
                    len(unproven),
                    correlation,
                )
                arguments = None
                missing_inputs = tuple(
                    dict.fromkeys(missing_inputs + unproven)
                )[:MAX_MISSING_INPUTS]
        if arguments is not None and self_index_ran:
            post_index_gaps = _post_self_index_argument_gaps(
                arguments,
                descriptor,
                index_declared_ids,
            )
            if post_index_gaps:
                _logger.info(
                    "orchestration stage=arguments "
                    "decision=post_index_identifier_required "
                    "fields=%d correlation_id=%s",
                    len(post_index_gaps),
                    correlation,
                )
                arguments = None
                missing_inputs = tuple(
                    dict.fromkeys(missing_inputs + post_index_gaps)
                )[:MAX_MISSING_INPUTS]
        if (
            optional_index_probe_skipped_budget
            and not self_index_ran
        ):
            # Optional model index probe skipped for turn headroom.
            # Empty free-string invoke would be an ungoverned index READ
            # → SOURCE_UNAVAILABLE. A filled exploratory proposal proceeds
            # as the typed model argument. Identifier provenance stays on
            # _unproven_identifier_inputs, not on stem overlap.
            # Pagination-only material args are a legitimate list READ.
            id_keys = _optional_unconstrained_string_keys(descriptor)
            if id_keys:
                filled_count = 0
                if arguments is not None:
                    for key in id_keys:
                        raw = arguments.get(key)
                        if isinstance(raw, str) and raw.strip():
                            filled_count += 1
                if filled_count == 0 and not arguments:
                    _logger.info(
                        "orchestration stage=arguments "
                        "decision=skip_budget_identifier_unavailable "
                        "fields=%d correlation_id=%s",
                        len(id_keys),
                        correlation,
                    )
                    return GovernedCapabilityAttempt(
                        status=(
                            GovernedCapabilityStatus.PROCESSING_TIMEOUT
                        ),
                        correlation_id=correlation,
                        error_code="turn_budget_exhausted",
                    )
                _logger.info(
                    "orchestration stage=arguments "
                    "decision=skip_budget_proceed_with_args "
                    "fields=%d filled=%d correlation_id=%s",
                    len(id_keys),
                    filled_count,
                    correlation,
                )
        if arguments is not None and not self_index_ran:
            # Stage 04: apply owner-declared defaults, then require
            # nested/entity completeness before PREPARE/READ invoke.
            arguments = _apply_entity_defaults_to_arguments(
                dict(arguments),
                discovery_structured,
            )
            completeness_gaps = _argument_completeness_gaps(
                arguments,
                descriptor,
                discovery_structured,
            )
            if completeness_gaps:
                _logger.info(
                    "orchestration stage=arguments "
                    "decision=completeness_not_ready fields=%d "
                    "correlation_id=%s",
                    len(completeness_gaps),
                    correlation,
                )
                arguments = None
                missing_inputs = tuple(
                    dict.fromkeys(missing_inputs + completeness_gaps)
                )[:MAX_MISSING_INPUTS]
        if arguments is None and missing_inputs:
            # Generic resolver step (§6.140): before asking the user
            # for an identifier the owner itself can resolve, run one
            # bounded same-owner non-mutating capability and rebuild
            # the target arguments from its evidence.
            # After a self-index probe, skip foreign/same-owner resolver
            # fan-out that could invent ids — index options already
            # exhausted the legitimate vocabulary for this capability.
            if self_index_ran and index_declared_ids is not None:
                resolved = self._Resolution()
            elif not self._budget_allows_resolver(deadline):
                # Stage 05 latency: resolver fan-out is optional
                # enrichment. Without headroom for select+invoke+
                # rebuild+clarify, ask the user immediately.
                _logger.info(
                    "orchestration stage=resolver "
                    "decision=skipped_budget remaining_ms=%d "
                    "correlation_id=%s",
                    int(deadline.remaining_seconds() * 1000),
                    correlation,
                )
                resolved = self._Resolution()
            else:
                resolved = self._resolve_missing_inputs(
                    input_text,
                    descriptor,
                    missing_inputs,
                    group,
                    discovery,
                    correlation,
                    workspace_context,
                    prior_turns,
                    deadline,
                    foreign=foreign_cap,
                    foreign_group=foreign_group,
                    foreign_evidence=foreign_evidence,
                )
            if resolved.attempt is not None:
                return resolved.attempt
            if resolved.arguments is not None:
                arguments = resolved.arguments
                missing_inputs = ()
                if resolved.owner_evidence:
                    owner_evidence = resolved.owner_evidence
                if self_index_ran:
                    post_index_gaps = _post_self_index_argument_gaps(
                        arguments,
                        descriptor,
                        index_declared_ids,
                    )
                    if post_index_gaps:
                        _logger.info(
                            "orchestration stage=arguments "
                            "decision=post_resolver_index_reject "
                            "fields=%d correlation_id=%s",
                            len(post_index_gaps),
                            correlation,
                        )
                        arguments = None
                        missing_inputs = post_index_gaps
                elif arguments is not None:
                    arguments = _apply_entity_defaults_to_arguments(
                        dict(arguments),
                        discovery_structured,
                    )
                    completeness_gaps = _argument_completeness_gaps(
                        arguments,
                        descriptor,
                        discovery_structured,
                    )
                    if completeness_gaps:
                        _logger.info(
                            "orchestration stage=arguments "
                            "decision=post_resolver_completeness_reject "
                            "fields=%d correlation_id=%s",
                            len(completeness_gaps),
                            correlation,
                        )
                        arguments = None
                        missing_inputs = completeness_gaps
                if arguments is not None:
                    _logger.info(
                        "orchestration stage=arguments "
                        "decision=resolved_by_owner evidence=1 "
                        "correlation_id=%s",
                        correlation,
                    )
        if arguments is None:
            if missing_inputs:
                # The capability path exists but owner-required input
                # is absent from the turn — truthful ask-back, never a
                # fabricated value nor a generic refusal.
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
                    correlation_id=correlation,
                    content=self._clarification_question(
                        input_text,
                        missing_inputs,
                        descriptor,
                        correlation,
                        deadline,
                    ),
                )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome,
            )

        if descriptor.operation_class is SpecialistOperationClass.PREPARE:
            attempt = self._attempt_prepare(
                group_key,
                remote_name,
                arguments,
                group,
                actor_user_id,
                session_id,
                correlation,
                prepare_only=prepare_only,
                deadline=deadline,
            )
            _logger.info(
                "orchestration stage=execute decision=%s "
                "error_code=%s correlation_id=%s",
                attempt.status.value,
                attempt.error_code or "",
                correlation,
            )
            return attempt
        if descriptor.operation_class is SpecialistOperationClass.ACT:
            return self._attempt_direct_act(
                group_key,
                descriptor,
                arguments,
                group,
                actor_user_id,
                session_id,
                correlation,
                prepare_only=prepare_only,
                deadline=deadline,
            )

        try:
            invoked = self._invoke_selected(
                group_key,
                remote_name,
                arguments,
                group,
                input_text,
                correlation,
                prior_turns,
                deadline,
                goal,
            )
        except CapabilityProviderError as exc:
            if exc.code in _REPAIRABLE_SURFACE_CODES:
                # Bounded pre-execution repair (C3-LOOP-01): the live
                # surface changed under the selection — re-read the
                # group, reselect and rebuild arguments at most once.
                # Only reachable for non-write targets: PREPARE/ACT
                # returned through their governed branches above, so a
                # material ACT can never be retried here.
                repaired = self._repair_once(
                    input_text,
                    group_key,
                    arguments,
                    correlation,
                    workspace_context,
                    prior_turns,
                    deadline,
                )
                if repaired is not None:
                    invoked = repaired
                else:
                    return _error_attempt(correlation, exc)
            elif (
                exc.code in _OWNER_REMOTE_ERROR_CODES
                and not discovery_ran
                and not self_index_ran
            ):
                # C3 contextual recovery: the owner rejected the
                # arguments under a constraint the flat schema cannot
                # express — one bounded round: same-group DISCOVERY
                # vocabulary -> same argument stage -> one retry.
                recovered = self._recover_owner_contract(
                    input_text,
                    descriptor,
                    group_key,
                    remote_name,
                    group,
                    correlation,
                    workspace_context,
                    prior_turns,
                    deadline,
                )
                if recovered is not None:
                    invoked = recovered
                else:
                    return _error_attempt(correlation, exc)
            else:
                _logger.info(
                    "orchestration stage=execute decision=error "
                    "error_code=%s detail=%s correlation_id=%s",
                    exc.code,
                    exc.message[:240],
                    correlation,
                )
                return _error_attempt(correlation, exc)
        if invoked is None:
            # Post-consultation miss: the owner produced no eligible
            # candidate or the owner candidate schema rejected the
            # proposal. C3 pre-R4: the same single governed recovery
            # round granted to irrelevant evidence applies to an
            # inadequate query — the planner may reformulate the
            # discovery arguments or reselect an eligible
            # READ/DISCOVERY under the shared one-round flag,
            # identical-argument dedup, budget and live-surface
            # revalidation. Any failure keeps the truthful miss.
            if not _RELEVANCE_RECOVERY_USED.get():
                recovered = self._recover_relevance(
                    input_text,
                    descriptor,
                    group_key,
                    remote_name,
                    group,
                    groups,
                    None,
                    arguments,
                    GoalEvidenceJudgment(
                        correspondence=GOAL_EVIDENCE_IRRELEVANT,
                        mismatch_hint=(
                            "owner consultation produced no usable "
                            "candidate or records"
                        ),
                    ),
                    goal,
                    owner_evidence=owner_evidence,
                    workspace_context=workspace_context,
                    prior_turns=prior_turns,
                    correlation=correlation,
                    deadline=deadline,
                )
                if recovered is not None:
                    invoked = recovered
        if invoked is None:
            # Truthful NOT_APPLICABLE after the bounded recovery —
            # never a fabrication.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="owner_query_miss",
                admission_outcome=unbound_outcome,
            )
        outcome, action_id, remote_used = invoked
        if path_mode == "corroborate":
            # Bounded comparison terminal (LOOP-02): two independent
            # owner evidence sets are confronted deterministically —
            # the model only selects comparable records/fields. Both
            # sources stay in provenance and limitations merge.
            return self._corroborate_attempt(
                input_text,
                outcome,
                foreign_outcome,
                group_key,
                remote_used,
                action_id,
                group,
                correlation,
                foreign_group=foreign_group,
                foreign_key=foreign_key,
                deadline=deadline,
            )
        if (
            descriptor.operation_class
            is SpecialistOperationClass.ANALYSIS
        ):
            # Bounded ANALYSIS -> PREPARE continuation (§6.140): when
            # the user goal requires preparing a change informed by
            # the analysis, one applicable live PREPARE capability of
            # the same owner is selected semantically and routed
            # through the normal governed-write chain. The analysis
            # result is owner evidence — never authority, never a
            # direct ACT.
            continued = self._analysis_continuation(
                input_text,
                descriptor,
                outcome,
                group_key,
                group,
                discovery,
                owner_evidence,
                actor_user_id,
                session_id,
                correlation,
                workspace_context,
                prior_turns,
                deadline,
                foreign=foreign_cap,
                foreign_group=foreign_group,
                foreign_evidence=foreign_evidence,
            )
            if continued is not None:
                return continued
        outcome = self._maybe_aggregate_paginated_count(
            input_text,
            outcome,
            arguments,
            group_key,
            remote_used,
            group,
            correlation,
            prior_turns,
            deadline,
        )
        # CRI E2/E3: one verdict feeds both the insufficiency marker
        # and the grounded conversational composition — same edge,
        # same facts, never a second assessment.
        cri_facts = (
            outcome_facts(
                outcome,
                descriptor.operation_class,
                record_resolver=lambda structured: _synthesis_records(
                    structured, field_labels=self._field_labels
                ),
            )
            if self._cri_active
            else None
        )
        cri_verdict = (
            assess_outcome(
                cri_facts,
                goal.answer_requirements,
                contract_subject=goal.contract_subject,
            )
            if cri_facts is not None
            else None
        )
        # D5 evidence-intent correspondence (doc 124): a non-answer
        # verdict must never replace a governed deterministic
        # projection already produced for this outcome — the zero-
        # candidate discovery terminal content and the guidance
        # projection ARE the honest answer/miss; a generic
        # insufficiency composition over them is a downgrade, not a
        # correction. The same defer applies to ANSWERED verdicts
        # when the outcome is guidance-shaped: the deterministic
        # section projection is the governed presentation of the
        # same evidence, not the record scaffold.
        _guided = (
            _deterministic_guidance_content(
                outcome.structured,
                owner_truncated=(
                    LIMITATION_RESULT_TRUNCATED in outcome.limitations
                ),
            )
            if cri_verdict is not None
            else None
        )
        projected_answer = cri_verdict is not None and (
            (
                cri_verdict.decision
                in (OUTCOME_ENVELOPE_ONLY, OUTCOME_INSUFFICIENT)
                and not cri_facts.has_business_evidence
                and (
                    bool(outcome.contract_facts)
                    or _guided is not None
                )
            )
            or (
                cri_verdict.decision == OUTCOME_ANSWERED
                and _guided is not None
            )
        )
        if not projected_answer:
            # Semantic relevance edge (plan 125 adendum /
            # DELIA-C3-SEMANTIC-RELEVANCE): an ``answered`` verdict on
            # business evidence is conclusive only after the bounded
            # goal/evidence correspondence judgment — irrelevant
            # evidence earns ONE governed READ recovery round (same
            # capability, revalidated gates, budget-gated); unproven
            # or persisting mismatch degrades to honest
            # insufficiency. Deterministic guidance/contract
            # projections skip the judgment — they already ARE the
            # governed answer.
            (
                outcome,
                remote_used,
                action_id,
                cri_facts,
                cri_verdict,
            ) = self._apply_semantic_relevance(
                input_text,
                outcome,
                cri_facts,
                cri_verdict,
                descriptor,
                group_key,
                remote_used,
                action_id,
                group,
                groups,
                arguments,
                goal,
                owner_evidence,
                workspace_context,
                prior_turns,
                correlation,
                deadline,
            )
            _guided = (
                _deterministic_guidance_content(
                    outcome.structured,
                    owner_truncated=(
                        LIMITATION_RESULT_TRUNCATED
                        in outcome.limitations
                    ),
                )
                if cri_verdict is not None
                else None
            )
            projected_answer = cri_verdict is not None and (
                (
                    cri_verdict.decision
                    in (OUTCOME_ENVELOPE_ONLY, OUTCOME_INSUFFICIENT)
                    and not cri_facts.has_business_evidence
                    and (
                        bool(outcome.contract_facts)
                        or _guided is not None
                    )
                )
                or (
                    cri_verdict.decision == OUTCOME_ANSWERED
                    and _guided is not None
                )
            )
        cri = (
            None
            if projected_answer
            else self._compose_cri_response(
                cri_facts,
                cri_verdict,
                goal,
                correlation,
                contract_text=descriptor.description,
                projected_content=outcome.projected_content,
            )
            if cri_verdict is not None
            else None
        )
        _synth_content, _synth_extra = self._synthesize_content(
            input_text,
            outcome,
            correlation,
            deadline,
            prior_turns=prior_turns,
            business_subject=goal.business_subject,
            invocation_arguments=arguments,
            allow_model_stage=cri is None,
        )
        outcome = self._apply_outcome_assessment(
            outcome,
            None if projected_answer else cri_verdict,
            correlation,
        )
        _extra = _synth_extra + (
            cri.limitations if cri is not None else ()
        )
        _synth_limitations: tuple[str, ...] | None = None
        if _extra:
            _synth_limitations = tuple(
                dict.fromkeys(outcome.limitations + _extra)
            )
        return self._outcome_attempt(
            group_key,
            remote_used,
            action_id,
            group,
            outcome,
            correlation,
            content=(
                cri.content if cri is not None else _synth_content
            ),
            limitations=_synth_limitations,
            input_text=input_text,
            # Prompt 5: the ONLY seam where the runtime knows whether
            # the CRI composer actually produced this response — a
            # startup flag is never proof of participation.
            composition_mode="cri" if cri is not None else None,
        )

    # ---------------- bounded multi-step helpers ----------------

    @dataclasses.dataclass(frozen=True, slots=True)
    class _Resolution:
        """Result of the bounded resolver step."""

        arguments: dict[str, Any] | None = None
        attempt: GovernedCapabilityAttempt | None = None
        owner_evidence: str | None = None

    def _resolve_missing_inputs(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        missing_inputs: tuple[str, ...],
        group: CapabilityGroup,
        discovery: ProviderCapability | None,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline,
        foreign: ProviderCapability | None = None,
        foreign_group: CapabilityGroup | None = None,
        foreign_evidence: str | None = None,
    ) -> "OperationalCapabilityOrchestrator._Resolution":
        """RESOLVER step: same-owner non-mutating evidence for a
        missing target input (§6.140, G1).

        Selection is a bounded model proposal revalidated against the
        live surface; the resolver result feeds one bounded rebuild of
        the target arguments. Ambiguous owner answers produce a
        candidate clarification — never a silent pick; an invented id
        that cannot be proven in the owner result fails closed.
        """
        resolver = self._select_resolver(
            input_text,
            descriptor,
            missing_inputs,
            group,
            workspace_context,
            prior_turns,
            correlation,
            deadline,
        )
        if resolver is None:
            return self._Resolution()
        # Rebuild the bounded plan with the resolver step and
        # revalidate every step against the live surface.
        plan = self._build_plan(
            input_text,
            descriptor,
            group,
            discovery,
            correlation,
            resolver=resolver,
            foreign=foreign,
            foreign_group=foreign_group,
        )
        if plan is None:
            return self._Resolution()
        _logger.info(
            "orchestration stage=resolver decision=selected "
            "capability=%s class=%s missing=%d correlation_id=%s",
            resolver.remote_name,
            resolver.operation_class.value,
            len(missing_inputs),
            correlation,
        )
        resolver_arguments, resolver_missing = self._build_arguments(
            input_text,
            resolver,
            workspace_context,
            correlation=correlation,
            prior_turns=prior_turns,
            deadline=deadline,
        )
        if resolver_arguments is None:
            _logger.info(
                "orchestration stage=resolver decision=args_failed "
                "missing=%d correlation_id=%s",
                len(resolver_missing),
                correlation,
            )
            return self._Resolution()
        if _unproven_identifier_inputs(
            resolver_arguments,
            resolver,
            input_text,
            workspace_context,
            None,
        ):
            # A resolver invoked with an invented identifier cannot
            # produce trustworthy evidence — fail closed.
            _logger.info(
                "orchestration stage=resolver "
                "decision=unproven_identifier correlation_id=%s",
                correlation,
            )
            return self._Resolution()
        try:
            outcome = self._invoke(
                group, resolver.remote_name, resolver_arguments,
                correlation, deadline,
            )
        except CapabilityProviderError as exc:
            _logger.info(
                "orchestration stage=resolver decision=error "
                "error_code=%s correlation_id=%s",
                exc.code,
                correlation,
            )
            return self._Resolution(
                attempt=_error_attempt(correlation, exc)
            )
        self._log_plan(plan, correlation, discovery_ran=discovery is not None)
        entities = _resolver_entities(outcome.structured)
        evidence = _bound_owner_evidence(outcome)
        if _resolver_ambiguous(entities, missing_inputs):
            # Position words are not a selector. Reuse the arguments
            # proposal against owner evidence; only a proven identifier
            # binds. Ambiguity without that proof clarifies.
            rebuilt, _still_missing = self._build_arguments(
                input_text,
                descriptor,
                workspace_context,
                owner_evidence=evidence,
                foreign_evidence=foreign_evidence,
                correlation=correlation,
                prior_turns=prior_turns,
                deadline=deadline,
            )
            if (
                rebuilt is not None
                and _missing_inputs_bound(rebuilt, missing_inputs)
                and not _unproven_identifier_inputs(
                    rebuilt,
                    descriptor,
                    input_text,
                    workspace_context,
                    evidence,
                )
                and _resolved_values_proven(
                    rebuilt, missing_inputs, outcome.structured
                )
            ):
                _logger.info(
                    "orchestration stage=resolver "
                    "decision=ambiguous_proven_selection "
                    "correlation_id=%s",
                    correlation,
                )
                return self._Resolution(
                    arguments=rebuilt, owner_evidence=evidence
                )
            _logger.info(
                "orchestration stage=resolver decision=ambiguous "
                "candidates=%d correlation_id=%s",
                len(entities),
                correlation,
            )
            return self._Resolution(
                attempt=GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
                    correlation_id=correlation,
                    content=_candidate_clarification_content(
                        entities, missing_inputs
                    ),
                )
            )
        rebuilt, still_missing = self._build_arguments(
            input_text,
            descriptor,
            workspace_context,
            owner_evidence=evidence,
            foreign_evidence=foreign_evidence,
            correlation=correlation,
            prior_turns=prior_turns,
            deadline=deadline,
        )
        if rebuilt is None and entities:
            # Deterministic fill when the model cannot project but the
            # owner list supplies exactly one proven entity (or an
            # ordinal-selected entity already handled above).
            if len(entities) == 1:
                filled = _fill_missing_from_entity(
                    descriptor, missing_inputs, entities[0]
                )
                if filled is not None and _resolved_values_proven(
                    filled, missing_inputs, outcome.structured
                ):
                    rebuilt, still_missing = filled, ()
        if (
            rebuilt is None
            or still_missing
            or not _missing_inputs_bound(rebuilt, missing_inputs)
        ):
            # The rebuild did not satisfy the inputs the target
            # semantically required — resolving here would invoke the
            # owner under-filtered (F1 semantics at the resolver
            # boundary). Fail closed to the original clarification.
            return self._Resolution(owner_evidence=evidence)
        if not _resolved_values_proven(
            rebuilt, missing_inputs, outcome.structured
        ):
            # A resolved value that cannot be found in the owner
            # evidence is an invented id — fail closed to the original
            # clarification, never invoke with it.
            _logger.info(
                "orchestration stage=resolver "
                "decision=unproven_value correlation_id=%s",
                correlation,
            )
            return self._Resolution(owner_evidence=evidence)
        _logger.info(
            "orchestration stage=resolver decision=resolved "
            "still_missing=%d correlation_id=%s",
            len(still_missing),
            correlation,
        )
        return self._Resolution(
            arguments=rebuilt, owner_evidence=evidence
        )

    def _select_resolver(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        missing_inputs: tuple[str, ...],
        group: CapabilityGroup,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> ProviderCapability | None:
        """One bounded proposal for a same-owner non-mutating resolver.

        Eligible classes: DISCOVERY | READ | ANALYSIS. The target
        itself, candidate-bound executors and write classes are never
        eligible. The proposal is revalidated deterministically.
        """
        eligible = [
            cap
            for cap in group.capabilities
            if cap.remote_name != descriptor.remote_name
            and cap.operation_class
            in (
                SpecialistOperationClass.DISCOVERY,
                SpecialistOperationClass.READ,
                SpecialistOperationClass.ANALYSIS,
            )
            and not _is_candidate_bound(cap)
            and not _is_proposal_bound(cap)
        ]
        if not eligible:
            return None
        block = {
            "target": {
                "remote_name": descriptor.remote_name,
                "description": (descriptor.description or "")[
                    :MAX_DESCRIPTION_CHARS
                ],
                "missing_inputs": list(missing_inputs),
            },
            "resolver_candidates": [
                {
                    "remote_name": cap.remote_name,
                    "operation_class": cap.operation_class.value,
                    "description": (cap.description or "")[
                        :MAX_DESCRIPTION_CHARS
                    ],
                    "required": sorted(_schema_keys(cap)[1]),
                }
                for cap in eligible[:MAX_SURFACE_ENTRIES]
            ],
        }
        proposal = self._propose(
            input_text,
            block_tag="resolver",
            block_payload=json.dumps(
                block, ensure_ascii=False, default=str
            )[:MAX_SURFACE_CHARS],
            instruction_id=RESOLVER_SELECTION_INSTRUCTION_ID,
            instruction=self._instruction(RESOLVER_SELECTION_INSTRUCTION_ID),
            expected_fields=("applicable", "remote_name"),
            input_kind="resolver_selection",
            allowed_keys=frozenset(
                {"applicable", "remote_name", "limitations"}
            ),
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return None
        applicable = proposal.get("applicable")
        if isinstance(applicable, str):
            applicable = applicable.strip().lower() == "true"
        if applicable is not True:
            return None
        remote_name = proposal.get("remote_name")
        if not isinstance(remote_name, str):
            return None
        remote_name = remote_name.strip()
        return next(
            (cap for cap in eligible if cap.remote_name == remote_name),
            None,
        )

    def _analysis_continuation(
        self,
        input_text: str,
        analysis_descriptor: ProviderCapability,
        analysis_outcome: SpecialistOutcome,
        group_key: str,
        group: CapabilityGroup,
        discovery: ProviderCapability | None,
        owner_evidence: str | None,
        actor_user_id: str | None,
        session_id: str | None,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline,
        foreign: ProviderCapability | None = None,
        foreign_group: CapabilityGroup | None = None,
        foreign_evidence: str | None = None,
    ) -> GovernedCapabilityAttempt | None:
        """Bounded ANALYSIS -> PREPARE continuation (§6.140).

        One semantic decision: does the user goal require preparing a
        change informed by this analysis? The only eligible next class
        is PREPARE — never direct ACT. When no PREPARE applies the
        analysis renders terminally (``None``).
        """
        prepare_cap = self._select_prepare_continuation(
            input_text,
            analysis_outcome,
            group,
            workspace_context,
            prior_turns,
            correlation,
            deadline,
        )
        if prepare_cap is None:
            return None
        plan = self._build_plan(
            input_text,
            prepare_cap,
            group,
            discovery,
            correlation,
            resolver=analysis_descriptor,
            foreign=foreign,
            foreign_group=foreign_group,
        )
        if plan is None:
            _logger.info(
                "orchestration stage=continuation "
                "decision=plan_rejected correlation_id=%s",
                correlation,
            )
            return None
        self._log_plan(
            plan, correlation, discovery_ran=discovery is not None
        )
        evidence_parts = [
            part
            for part in (
                _bound_owner_evidence(analysis_outcome), owner_evidence
            )
            if part
        ]
        combined_evidence = "\n".join(evidence_parts)[
            :MAX_OWNER_EVIDENCE_CHARS
        ] or None
        arguments, missing_inputs = self._build_arguments(
            input_text,
            prepare_cap,
            workspace_context,
            owner_evidence=combined_evidence,
            foreign_evidence=foreign_evidence,
            correlation=correlation,
            prior_turns=prior_turns,
            deadline=deadline,
        )
        _logger.info(
            "orchestration stage=continuation decision=%s "
            "capability=%s missing=%d correlation_id=%s",
            "prepare" if arguments is not None else "terminal",
            prepare_cap.remote_name,
            len(missing_inputs),
            correlation,
        )
        if arguments is None:
            if missing_inputs:
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
                    correlation_id=correlation,
                    content=self._clarification_question(
                        input_text,
                        missing_inputs,
                        prepare_cap,
                        correlation,
                        deadline,
                    ),
                )
            return None
        return self._attempt_prepare(
            group_key,
            prepare_cap.remote_name,
            arguments,
            group,
            actor_user_id,
            session_id,
            correlation,
            deadline=deadline,
        )

    @dataclasses.dataclass(frozen=True, slots=True)
    class _TurnGoal:
        """Bounded semantic interpretation of the user turn (LOOP-03R1).

        A proposal, never authority: it classifies intent, carries the
        business subject and user-stated scope constraints. Downstream
        stages consume it as untrusted-but-validated structure — a
        comparison goal can never silently collapse to single-source
        native success.
        """

        goal_class: str = "read"
        comparison_requested: bool = False
        output_mode: str = "unspecified"
        business_subject: str | None = None
        scope_constraints: tuple[tuple[str, str], ...] = ()
        # True only when a validated model proposal declared the class
        # — the neutral default is never treated as declared intent,
        # so an absent interpretation is unproven intent and cannot
        # carry a write-class selection (C3-CI-02R1 §6.174).
        declared: bool = False
        # User-stated execution restriction (C3-CI-02R1): "prepare_only"
        # when the user explicitly forbids applying the change; the
        # bound can only reduce the effective execution ceiling.
        execution_bound: str = "unrestricted"
        # True only when a validated proposal declares that prior
        # DELIA_RESULT content already answers without a new owner call.
        prior_evidence_sufficient: bool = False
        # CRI E2: typed sufficiency requirements proposed by the SAME
        # goal stage — a hypothesis validated against typed outcome
        # evidence, never a fact. None when undeclared.
        answer_requirements: AnswerRequirements | None = None
        # D5 evidence-intent correspondence (doc 124): True only when a
        # validated proposal declares the user asked about the published
        # contract/schema itself. Owner contract metadata composes an
        # answer only for declared contract subjects — absent means
        # unproven intent, never schema-dump-by-default.
        contract_subject: bool = False

    _GOAL_CLASSES = frozenset(
        {"read", "analyze", "compare", "create_or_modify", "clarify"}
    )
    _OUTPUT_MODES = frozenset({"dynamic", "snapshot", "unspecified"})
    _EXECUTION_BOUNDS = frozenset({"unrestricted", "prepare_only"})

    _GOAL_ALLOWED_KEYS = frozenset(
        {
            "goal_class",
            "comparison_requested",
            "output_mode",
            "execution_bound",
            "business_subject",
            "scope_constraints",
            "prior_evidence_sufficient",
            "limitations",
            "answer_requirements",
            "contract_subject",
        }
    )

    def _turn_goal_from_proposal(
        self,
        proposal: Mapping[str, Any] | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        *,
        correlation: str,
        require_goal_class: bool,
    ) -> "OperationalCapabilityOrchestrator._TurnGoal | None":
        """Validate a goal payload into ``_TurnGoal``.

        When ``require_goal_class`` is True (dedicated turn_goal stage),
        missing/invalid class degrades to the neutral undeclared default.
        When False (typed capability+goal), absence of ``goal_class``
        returns None so the caller may fall back to a separate propose;
        an explicit invalid class still fails closed to undeclared.
        """
        if not isinstance(proposal, Mapping):
            if require_goal_class:
                _logger.info(
                    "orchestration stage=goal_understanding "
                    "decision=default correlation_id=%s",
                    correlation,
                )
                return self._TurnGoal()
            return None
        if "goal_class" not in proposal:
            if require_goal_class:
                _logger.info(
                    "orchestration stage=goal_understanding "
                    "decision=default correlation_id=%s",
                    correlation,
                )
                return self._TurnGoal()
            return None
        goal_class = proposal.get("goal_class")
        if not (
            isinstance(goal_class, str)
            and goal_class in self._GOAL_CLASSES
        ):
            # An interpretation whose class is not a valid goal is
            # itself uninterpretable — degrade to the neutral default
            # rather than coercing it into a declared read intent
            # (C3-CI-02R1 §6.174).
            _logger.info(
                "orchestration stage=goal_understanding "
                "decision=invalid_class correlation_id=%s",
                correlation,
            )
            return self._TurnGoal()
        comparison = proposal.get("comparison_requested")
        output_mode = proposal.get("output_mode")
        execution_bound = proposal.get("execution_bound")
        subject = proposal.get("business_subject")
        scope = proposal.get("scope_constraints")
        scope_pairs: list[tuple[str, str]] = []
        if isinstance(scope, Mapping):
            for key, value in list(scope.items())[:MAX_ARGUMENT_KEYS]:
                if isinstance(key, str) and isinstance(
                    value, (str, int, float)
                ):
                    scope_pairs.append(
                        (key.strip()[:80], str(value).strip()[:200])
                    )
        prior_sufficient = (
            proposal.get("prior_evidence_sufficient") is True
            and bool(prior_turns)
        )
        goal = self._TurnGoal(
            goal_class=goal_class,
            comparison_requested=comparison is True,
            output_mode=(
                output_mode
                if isinstance(output_mode, str)
                and output_mode in self._OUTPUT_MODES
                else "unspecified"
            ),
            business_subject=(
                subject.strip()[:MAX_DESCRIPTION_CHARS]
                if isinstance(subject, str) and subject.strip()
                else None
            ),
            scope_constraints=tuple(scope_pairs),
            declared=True,
            execution_bound=(
                execution_bound
                if isinstance(execution_bound, str)
                and execution_bound in self._EXECUTION_BOUNDS
                else "unrestricted"
            ),
            prior_evidence_sufficient=prior_sufficient,
            answer_requirements=parse_answer_requirements(
                proposal.get("answer_requirements")
            ),
            contract_subject=(
                proposal.get("contract_subject") is True
            ),
        )
        _logger.info(
            "orchestration stage=goal_understanding "
            "decision=interpreted class=%s comparison=%s "
            "output_mode=%s bound=%s subject=%s prior_sufficient=%s "
            "contract_subject=%s correlation_id=%s",
            goal.goal_class,
            goal.comparison_requested,
            goal.output_mode,
            goal.execution_bound,
            "yes" if goal.business_subject else "no",
            "yes" if goal.prior_evidence_sufficient else "no",
            "yes" if goal.contract_subject else "no",
            correlation,
        )
        return goal

    def _understand_goal(
        self,
        input_text: str,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline,
    ) -> "OperationalCapabilityOrchestrator._TurnGoal":
        """One bounded goal-interpretation proposal (LOOP-03R1).

        When prior turns exist this may run before target selection so a
        prior-evidence-sufficient follow-up can skip reselection. The
        same validated result feeds native assessment, argument
        projection and the comparability gate. Any invalid or absent
        proposal degrades to a neutral default goal — never a
        fabricated interpretation.
        """
        proposal = self._propose(
            input_text,
            block_tag="turn_context",
            block_payload="{}",
            instruction_id=GOAL_INSTRUCTION_ID,
            instruction=self._goal_instruction,
            instruction_version=self._cri_instruction_version,
            expected_fields=("goal_class",),
            input_kind="turn_goal",
            allowed_keys=self._GOAL_ALLOWED_KEYS,
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        parsed = self._turn_goal_from_proposal(
            proposal,
            prior_turns,
            correlation=correlation,
            require_goal_class=True,
        )
        return parsed if parsed is not None else self._TurnGoal()

    @staticmethod
    def _prior_result_turn(
        prior_turns: tuple[ConversationContextTurn, ...],
    ) -> ConversationContextTurn | None:
        """Latest non-empty DELIA_RESULT turn from prior context."""
        for turn in reversed(prior_turns):
            if turn.kind is not TurnKind.DELIA_RESULT:
                continue
            if (turn.content or "").strip():
                return turn
        return None

    @staticmethod
    def _prior_result_content(
        prior_turns: tuple[ConversationContextTurn, ...],
    ) -> str | None:
        """Latest non-empty DELIA_RESULT content from prior turns.

        Untrusted conversational data — never authority, never AuthZ,
        never fresh grounding. Used only for bounded continuity when
        the validated goal declares prior evidence sufficient.
        """
        turn = OperationalCapabilityOrchestrator._prior_result_turn(
            prior_turns
        )
        if turn is None:
            return None
        return (turn.content or "").strip()[:MAX_RENDER_CONTENT_CHARS]

    def _budget_allows_resolver(self, deadline: TurnDeadline) -> bool:
        """Resolver fan-out needs headroom beyond a bare clarify.

        Requires remaining budget for a bounded model stage slice plus
        a viable minimum so clarify can still finish. The floor is
        intentionally below half a full stage timeout: follow-up turns
        that already spent budget on goal/selection must still be able
        to resolve a missing identifier via one same-owner READ
        (e.g. ordinal bind after an unproven id) inside the global
        30s turn budget — raising the global ceiling is forbidden.
        """
        remaining = deadline.remaining_seconds()
        floor = max(
            self._model_stage_timeout_seconds * 0.25,
            MIN_VIABLE_MODEL_STAGE_SECONDS * 3,
        )
        return remaining >= floor

    def _budget_allows_optional_index_probe(
        self, deadline: TurnDeadline
    ) -> bool:
        """Optional model index probe needs recoverable follow-on room.

        Derived only from existing caps (never widens the global 30s
        turn budget):

        - one full model-stage timeout for the probe proposal itself;
        - one full model-stage timeout for a subsequent index_select;
        - the same ``MIN_VIABLE_MODEL_STAGE_SECONDS * 3`` floor used by
          synthesis/resolver so a grounded READ presentation can still
          finish after the owner returns.

        When remaining is below this floor the optional model probe is
        not started; owner-declared omit→index remains a separate path
        that does not require this model call.
        """
        remaining = deadline.remaining_seconds()
        required = (
            self._model_stage_timeout_seconds
            + self._model_stage_timeout_seconds
            + MIN_VIABLE_MODEL_STAGE_SECONDS * 3
        )
        return remaining >= required

    def _prior_continuation_attempt(
        self,
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
        *,
        business_subject: str | None,
        comparison_requested: bool = False,
    ) -> GovernedCapabilityAttempt | None:
        """Transform prior DELIA_RESULT via selection-only synthesis.

        Returns None when prior content is absent or cannot be
        transformed — caller falls through to live selection. Never
        returns a literal full copy when multiple excerpts exist.

        Compare/analyze asks must not succeed by replaying a bullet
        list (G0 / F33): either emit a deterministic segment
        comparison from prior evidenced units, or declare insufficiency.
        """
        prior_content = self._prior_result_content(prior_turns)
        if not prior_content:
            _logger.info(
                "orchestration stage=prior_continuation "
                "decision=insufficient_prior_content "
                "correlation_id=%s",
                correlation,
            )
            return None
        records = _prior_excerpt_records(prior_content)
        if not records:
            return None
        # G0 bounded rework: compare/analyze over free-text prior
        # excerpts is never a typed attribute comparison. Fail closed
        # before spending a synthesis stage on positional heuristics.
        if (
            comparison_requested
            and not _prior_supports_typed_attribute_compare(records)
        ):
            return _compare_insufficiency_attempt(
                correlation,
                decision="compare_insufficient_untyped_prior",
            )
        block: dict[str, Any] = {"records": [dict(r) for r in records]}
        if business_subject is not None:
            block["business_subject"] = business_subject
        try:
            proposal = self._propose(
                input_text,
                block_tag="records",
                block_payload=json.dumps(
                    block,
                    ensure_ascii=False,
                    default=str,
                )[:MAX_SURFACE_CHARS],
                instruction_id=SYNTHESIS_INSTRUCTION_ID,
                instruction=self._instruction(SYNTHESIS_INSTRUCTION_ID),
                expected_fields=("items",),
                input_kind="prior_continuity_synthesis",
                allowed_keys=frozenset({"items", "presentation"}),
                prior_turns=(),
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded:
            _logger.info(
                "orchestration stage=prior_continuation "
                "decision=budget_exhausted correlation_id=%s",
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.PROCESSING_TIMEOUT,
                correlation_id=correlation,
                error_code="turn_budget_exhausted",
            )
        explicit_empty = (
            isinstance(proposal, Mapping)
            and isinstance(proposal.get("items"), (list, tuple))
            and len(proposal.get("items")) == 0
        )
        selected_items = (
            proposal.get("items")
            if isinstance(proposal, Mapping)
            else None
        )
        if (
            isinstance(selected_items, (list, tuple))
            and len(records) > 2
            and len(selected_items) >= len(records)
        ):
            # Selecting every excerpt replays the prior result —
            # not a proportional transform of the new ask.
            _logger.info(
                "orchestration stage=prior_continuation "
                "decision=reject_full_replay excerpts=%d "
                "correlation_id=%s",
                len(records),
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SUCCESS,
                correlation_id=correlation,
                content=_insufficiency_content(),
                limitations=(
                    LIMITATION_PRIOR_TURN_CONTINUATION,
                    LIMITATION_INSUFFICIENT_EVIDENCE,
                ),
            )
        rendered, reason = (
            _render_synthesis(
                proposal, records, field_labels=self._field_labels
            )
            if isinstance(proposal, Mapping)
            else (None, "proposal_absent")
        )
        if rendered is None:
            if reason == "invalid_record_index" and comparison_requested:
                return _compare_insufficiency_attempt(
                    correlation,
                    decision="compare_reject_invalid_index",
                )
            if rendered is None and reason == "empty_selection":
                if comparison_requested:
                    return _compare_insufficiency_attempt(
                        correlation,
                        decision="compare_reject_empty_selection",
                    )
                # Q02-A: empty synthesis is insufficiency — do not
                # invent a full prior bullet dump without a lexical
                # extraction detector (removed) or typed selection.
            if rendered is None:
                # Already on the prior-continuation path: do not fall
                # through to live reselection — that burns the remaining
                # global budget after a failed transform (Stage 05 live).
                _logger.info(
                    "orchestration stage=prior_continuation "
                    "decision=insufficient_evidence reason=%s "
                    "correlation_id=%s",
                    reason,
                    correlation,
                )
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.SUCCESS,
                    correlation_id=correlation,
                    content=_insufficiency_content(),
                    limitations=(
                        LIMITATION_PRIOR_TURN_CONTINUATION,
                        LIMITATION_INSUFFICIENT_EVIDENCE,
                    ),
                )
        proven_differences = (
            _selected_proven_differences(
                proposal, records, field_labels=self._field_labels
            )
            if isinstance(proposal, Mapping)
            else []
        )
        if comparison_requested and not proven_differences:
            return _compare_insufficiency_attempt(
                correlation,
                decision="compare_reject_without_typed_diff",
            )
        normalized_prior = " ".join(prior_content.split())
        normalized_rendered = " ".join(rendered.split())
        if (
            len(records) > 1
            and normalized_rendered == normalized_prior
        ):
            _logger.info(
                "orchestration stage=prior_continuation "
                "decision=reject_literal_copy excerpts=%d "
                "correlation_id=%s",
                len(records),
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SUCCESS,
                correlation_id=correlation,
                content=_insufficiency_content(),
                limitations=(
                    LIMITATION_PRIOR_TURN_CONTINUATION,
                    LIMITATION_INSUFFICIENT_EVIDENCE,
                ),
            )
        # Q02-A: do not expand validated synthesis selections via
        # coverage/thinness heuristics — that path previously depended
        # on lexical extraction/limitation detectors and would overwrite
        # intentional narrow continuity answers.
        _logger.info(
            "orchestration stage=prior_continuation "
            "decision=transformed excerpts=%d correlation_id=%s",
            len(records),
            correlation,
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            content=rendered,
            limitations=(LIMITATION_PRIOR_TURN_CONTINUATION,),
        )

    def _assess_native_path(
        self,
        input_text: str,
        group: CapabilityGroup,
        descriptor: ProviderCapability,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        goal: "OperationalCapabilityOrchestrator._TurnGoal" | None = None,
        deadline: TurnDeadline | None = None,
        relevance_feedback: str | None = None,
    ) -> str:
        """Stage B/C: native sufficiency assessment (LOOP-02R1).

        Runtime invariant: this proposal sees ONLY the target group's
        live surface — no foreign group name, capability or owner
        description is exposed before the assessment decides that a
        foreign path is justified. Returns ``sufficient`` (native),
        ``foreign_evidence_required``, ``corroboration_requested`` or
        ``inconclusive``; anything unparseable or absent is native —
        foreign fan-out is never the default.
        """
        proposal = self._propose(
            input_text,
            block_tag="target_capability_group",
            block_payload=json.dumps(
                {
                    "target_capability_id": descriptor.capability_id,
                    "target_operation_class": (
                        descriptor.operation_class.value
                    ),
                    "capabilities": json.loads(
                        _capability_payload(group)
                    ),
                    "turn_goal": (
                        {
                            "goal_class": goal.goal_class,
                            "comparison_requested": (
                                goal.comparison_requested
                            ),
                            "output_mode": goal.output_mode,
                            "business_subject": goal.business_subject,
                        }
                        if goal is not None
                        else None
                    ),
                    # Bounded mismatch signal from a validated
                    # goal/evidence judgment — present only during
                    # the single governed recovery round; untrusted
                    # data, never an instruction.
                    "relevance_feedback": (
                        json.loads(relevance_feedback)
                        if relevance_feedback
                        else None
                    ),
                },
                ensure_ascii=False,
                default=str,
            )[:MAX_SURFACE_CHARS],
            instruction_id=NATIVE_ASSESSMENT_INSTRUCTION_ID,
            instruction=self._instruction(NATIVE_ASSESSMENT_INSTRUCTION_ID),
            expected_fields=("status",),
            input_kind="native_assessment",
            allowed_keys=frozenset({"status", "limitations"}),
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        status = (
            proposal.get("status") if isinstance(proposal, Mapping)
            else None
        )
        if status not in (
            "sufficient",
            "foreign_evidence_required",
            "corroboration_requested",
            "inconclusive",
        ):
            status = "sufficient"
        _logger.info(
            "orchestration stage=native_assessment decision=%s "
            "correlation_id=%s",
            status,
            correlation,
        )
        return status

    def _select_foreign_capability(
        self,
        input_text: str,
        groups: Mapping[str, CapabilityGroup],
        target_group_key: str,
        mode: str,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline,
    ) -> tuple[str, ProviderCapability] | None:
        """Stage: pick ONE foreign non-mutating capability — only runs
        after the native assessment justified a foreign path. The
        proposal sees foreign groups only; deterministic runtime
        revalidates the id against the live surface (exists,
        unambiguous, non-mutating). Returns ``(group_key, cap)`` or
        None — the caller decides the bounded failure per mode.
        """
        foreign_groups = {
            key: group
            for key, group in groups.items()
            if key != target_group_key
        }
        proposal = self._propose(
            input_text,
            block_tag="foreign_capability_groups",
            block_payload=_group_summaries(
                foreign_groups,
                prior_observation=_prior_observation_context(
                    prior_turns
                ),
            )[:MAX_SURFACE_CHARS],
            instruction_id=FOREIGN_SELECTION_INSTRUCTION_ID,
            instruction=self._instruction(FOREIGN_SELECTION_INSTRUCTION_ID),
            expected_fields=("foreign_capability_id",),
            input_kind="foreign_selection",
            allowed_keys=frozenset(
                {"foreign_capability_id", "limitations"}
            ),
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        foreign_id = (
            proposal.get("foreign_capability_id")
            if isinstance(proposal, Mapping)
            else None
        )
        if not isinstance(foreign_id, str) or not foreign_id.strip():
            _logger.info(
                "orchestration stage=foreign_selection "
                "decision=none mode=%s correlation_id=%s",
                mode,
                correlation,
            )
            return None
        found = _find_capability(foreign_groups, foreign_id.strip())
        if found is None or (
            found[1].operation_class not in _PATH_FOREIGN_CLASSES
        ):
            _logger.info(
                "orchestration stage=foreign_selection "
                "decision=invalid mode=%s correlation_id=%s",
                mode,
                correlation,
            )
            return None
        _logger.info(
            "orchestration stage=foreign_selection "
            "decision=selected mode=%s capability=%s "
            "correlation_id=%s",
            mode,
            found[1].capability_id,
            correlation,
        )
        return found

    @dataclasses.dataclass(frozen=True, slots=True)
    class _ForeignResult:
        """Outcome of the bounded foreign non-mutating step."""

        outcome: SpecialistOutcome | None = None
        evidence: str | None = None
        missing_inputs: tuple[str, ...] = ()
        failed: bool = False

    def _invoke_foreign_evidence(
        self,
        input_text: str,
        foreign_key: str,
        foreign_cap: ProviderCapability,
        foreign_group: CapabilityGroup,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline,
        relevance_feedback: str | None = None,
        goal: _TurnGoal | None = None,
    ) -> "OperationalCapabilityOrchestrator._ForeignResult":
        """Execute the bounded foreign non-mutating step through the
        SAME owner-defined invocation mechanics as a selected target
        (LOOP-02R1): candidate-bound capabilities run their owner
        discovery→candidate→read flow via ``_invoke_selected`` — the
        foreign leg never creates a simplified execution path and the
        candidate token never leaves the owner workflow.
        """
        foreign_arguments, foreign_missing = self._build_arguments(
            input_text,
            foreign_cap,
            workspace_context,
            correlation=correlation,
            relevance_feedback=relevance_feedback,
            business_subject=(
                goal.business_subject if goal is not None else None
            ),
            prior_turns=prior_turns,
            deadline=deadline,
        )
        if foreign_arguments is None:
            _logger.info(
                "orchestration stage=foreign_invocation "
                "decision=args_failed missing=%d correlation_id=%s",
                len(foreign_missing),
                correlation,
            )
            return self._ForeignResult(
                missing_inputs=foreign_missing,
                failed=not foreign_missing,
            )
        if _unproven_identifier_inputs(
            foreign_arguments,
            foreign_cap,
            input_text,
            workspace_context,
            None,
        ):
            _logger.info(
                "orchestration stage=foreign_invocation "
                "decision=unproven_identifier correlation_id=%s",
                correlation,
            )
            return self._ForeignResult(failed=True)
        try:
            invoked = self._invoke_selected(
                foreign_key,
                foreign_cap.remote_name,
                foreign_arguments,
                foreign_group,
                input_text,
                correlation,
                prior_turns,
                deadline,
                goal=goal,
            )
        except CapabilityProviderError as exc:
            _logger.info(
                "orchestration stage=foreign_invocation "
                "decision=error error_code=%s correlation_id=%s",
                exc.code,
                correlation,
            )
            return self._ForeignResult(failed=True)
        if invoked is None:
            # Owner workflow produced no resolvable result — truthful
            # failure, never fabricated evidence.
            _logger.info(
                "orchestration stage=foreign_invocation "
                "decision=no_result correlation_id=%s",
                correlation,
            )
            return self._ForeignResult(failed=True)
        outcome = invoked[0]
        _logger.info(
            "orchestration stage=foreign_invocation "
            "decision=ok correlation_id=%s",
            correlation,
        )
        return self._ForeignResult(
            outcome=outcome,
            evidence=_bound_owner_evidence(outcome),
        )

    def _corroborate_attempt(
        self,
        input_text: str,
        outcome: SpecialistOutcome,
        foreign_outcome: SpecialistOutcome | None,
        group_key: str,
        remote_used: str,
        action_id: str,
        group: CapabilityGroup,
        correlation: str,
        deadline: TurnDeadline,
        foreign_group: CapabilityGroup | None = None,
        foreign_key: str | None = None,
    ) -> GovernedCapabilityAttempt:
        """Bounded cross-source comparison terminal (LOOP-02R1).

        Two independent owner evidence sets are confronted: the model
        may only select which records/fields are compared; the runtime
        computes the verdict deterministically — agreement, conflict
        or inconclusive — and renders values verbatim. Both sources
        stay in provenance and both limitation sets merge; evidence
        is never merged and the model never decides the verdict.
        """
        if foreign_outcome is None:
            _logger.info(
                "orchestration stage=comparison "
                "decision=source_unavailable correlation_id=%s",
                correlation,
            )
            rendered = render_specialist_outcome_rich(
                outcome, field_labels=self._field_labels
            )
            return self._outcome_attempt(
                group_key,
                remote_used,
                action_id,
                group,
                outcome,
                correlation,
                content=rendered.content,
                markdown_content=rendered.markdown,
                limitations=tuple(rendered.limitations)
                + ("comparison_source_unavailable",),
            )
        left_records = _comparison_records(outcome)
        right_records = _comparison_records(foreign_outcome)
        verdict: str | None = None
        content: str | None = None
        if left_records and right_records:
            proposal = self._propose(
                input_text,
                block_tag="records",
                block_payload=json.dumps(
                    {
                        "left": [dict(r) for r in left_records],
                        "right": [dict(r) for r in right_records],
                    },
                    ensure_ascii=False,
                    default=str,
                )[:MAX_SURFACE_CHARS],
                instruction_id=COMPARISON_INSTRUCTION_ID,
                instruction=self._instruction(COMPARISON_INSTRUCTION_ID),
                expected_fields=("left", "right"),
                input_kind="evidence_comparison",
                allowed_keys=frozenset(
                    {"left", "right", "limitations"}
                ),
                correlation=correlation,
                deadline=deadline,
            )
            compared = _compare_records(
                left_records, right_records, proposal
            )
            if compared is not None:
                verdict, content = compared
        _logger.info(
            "orchestration stage=comparison_verdict decision=%s "
            "correlation_id=%s",
            verdict or "inconclusive",
            correlation,
        )
        # Multi-source provenance (LOOP-02R1): the foreign comparison
        # source joins source_refs when it produced real evidence —
        # never fabricated when the source was unavailable. Both
        # owners' limitations merge additively, deterministic order.
        extra_refs: tuple[SourceRef, ...] = ()
        foreign_limitations: tuple[str, ...] = ()
        if foreign_outcome is not None and foreign_group is not None:
            foreign_source = foreign_group.source or SourceRef(
                source_id=foreign_group.owner_ref,
                source_system=foreign_group.owner_ref,
                provider_name=foreign_group.display_name,
            )
            extra_refs = (
                SourceRef(
                    source_id=foreign_source.source_id,
                    source_system=foreign_source.source_system,
                    provider_name=foreign_source.provider_name,
                    observed_at=foreign_outcome.provenance.observed_at,
                ),
            )
            foreign_limitations = tuple(foreign_outcome.limitations)
        merged_limitations = tuple(
            dict.fromkeys(tuple(outcome.limitations) + foreign_limitations)
        )
        if verdict == "agreement":
            limitations = merged_limitations
        elif verdict == "conflict":
            limitations = merged_limitations + ("evidence_conflict",)
        else:
            limitations = merged_limitations + (
                "comparison_inconclusive",
            )
            content = content or "Comparação inconclusiva."
        return self._outcome_attempt(
            group_key,
            remote_used,
            action_id,
            group,
            outcome,
            correlation,
            content=content,
            limitations=limitations,
            extra_source_refs=extra_refs,
        )

    def _select_prepare_continuation(
        self,
        input_text: str,
        analysis_outcome: SpecialistOutcome,
        group: CapabilityGroup,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> ProviderCapability | None:
        """Semantic bounded choice of an applicable same-owner PREPARE.

        Eligible: live PREPARE-class capabilities of the selected
        group only. The proposal carries a bounded analysis evidence
        summary — never tool-name pairing, never a direct ACT.
        """
        eligible = [
            cap
            for cap in group.capabilities
            if cap.operation_class is SpecialistOperationClass.PREPARE
        ]
        if not eligible:
            return None
        block = {
            "analysis": _bound_owner_evidence(analysis_outcome)[
                :MAX_SURFACE_CHARS
            ],
            "prepare_candidates": [
                {
                    "remote_name": cap.remote_name,
                    "description": (cap.description or "")[
                        :MAX_DESCRIPTION_CHARS
                    ],
                    "required": sorted(_schema_keys(cap)[1]),
                }
                for cap in eligible[:MAX_SURFACE_ENTRIES]
            ],
        }
        proposal = self._propose(
            input_text,
            block_tag="analysis_continuation",
            block_payload=json.dumps(
                block, ensure_ascii=False, default=str
            )[:MAX_SURFACE_CHARS],
            instruction_id=CONTINUATION_INSTRUCTION_ID,
            instruction=self._instruction(CONTINUATION_INSTRUCTION_ID),
            expected_fields=("applicable", "remote_name"),
            input_kind="analysis_continuation",
            allowed_keys=frozenset(
                {"applicable", "remote_name", "limitations"}
            ),
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return None
        applicable = proposal.get("applicable")
        if isinstance(applicable, str):
            applicable = applicable.strip().lower() == "true"
        if applicable is not True:
            return None
        remote_name = proposal.get("remote_name")
        if not isinstance(remote_name, str):
            return None
        remote_name = remote_name.strip()
        return next(
            (cap for cap in eligible if cap.remote_name == remote_name),
            None,
        )

    # ---------------- write orchestration ----------------

    def _attempt_prepare(
        self,
        group_key: str,
        remote_name: str,
        arguments: Mapping[str, Any],
        group: CapabilityGroup,
        actor_user_id: str | None,
        session_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Invoke an owner PREPARE capability and project the proposal.

        A READY proposal is held as backend-only pending orchestration
        state and surfaced as CONFIRMATION_REQUIRED — the raw
        proposal_ref never leaves this boundary. Anything else is
        rendered truthfully (NOT_READY/INVALID/EXPIRED/denials are
        owner answers, not DÉLIA failures).
        """
        capability_ref = f"{group_key}.{remote_name}"
        _logger.info(
            "orchestration stage=prepare_invoke decision=call "
            "capability=%s arg_keys=%s correlation_id=%s",
            capability_ref,
            ",".join(sorted(str(k) for k in arguments))[:200],
            correlation,
        )
        try:
            outcome = self._invoke(
                group, remote_name, dict(arguments), correlation,
                deadline,
            )
        except CapabilityProviderError as exc:
            _logger.info(
                "orchestration stage=prepare_invoke decision=error "
                "error_code=%s detail=%s correlation_id=%s",
                exc.code,
                exc.message[:240],
                correlation,
            )
            return _error_attempt(correlation, exc)

        payload = outcome.structured or {}
        preview = project_proposal_preview(
            capability_ref=capability_ref,
            remote_capability=remote_name,
            owner_payload=payload,
            specialist_id=group_key,
            correlation_id=correlation,
            observed_at=outcome.provenance.observed_at,
            now_epoch=time.time(),
            limitations=outcome.limitations,
        )
        self._audit(
            stage="PREPARE_PROJECTED",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=preview.readiness.value,
            proposal_digest=(
                proposal_digest(preview.proposal_ref)
                if preview.proposal_ref
                else None
            ),
            preview_fingerprint=(
                preview_fingerprint(preview) if preview.proposal_ref else None
            ),
        )

        if preview.readiness is not ProposalReadiness.READY:
            # Truthful owner projection — the specialist answered the
            # prepare call but produced no confirmable proposal
            # (denial/invalid/expired/not-ready). Render what the owner
            # actually returned; never fabricate a preview.
            rendered = render_specialist_outcome_rich(
                outcome, field_labels=self._field_labels
            )
            note = _READINESS_NOTE.get(preview.readiness)
            limitations = tuple(rendered.limitations) + (
                (note,) if note else ()
            )
            return self._outcome_attempt(
                group_key,
                remote_name,
                remote_name,
                group,
                outcome,
                correlation,
                content=rendered.content,
                markdown_content=rendered.markdown,
                limitations=limitations,
            )

        act_capability = _find_act_capability(
            group, require_proposal_handle=True
        )
        digest = proposal_digest(preview.proposal_ref)
        fingerprint = preview_fingerprint(preview)

        # Deterministic provider-neutral confirmation decision
        # (§6.140): the structural confirmation requirement on the
        # owner PREPARE proposal is the sole authority — the model
        # never decides destructiveness, no owner-vocabulary op policy
        # is consulted, and malformed/absent policy fails closed as an
        # owner-contract defect rather than degrading into auto-ACT or
        # a lazy confirmation prompt.
        confirmation_policy = _effective_confirmation_policy(preview)
        self._audit(
            stage="CONFIRMATION_POLICY",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=confirmation_policy,
            proposal_digest=digest,
            preview_fingerprint=fingerprint,
        )
        if confirmation_policy == CONFIRMATION_POLICY_INVALID:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="owner_policy_invalid",
                content=(
                    "O proprietário não declarou uma política de "
                    "confirmação consistente para esta operação — "
                    "nenhuma escrita foi executada."
                ),
            )
        if act_capability is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                content=(
                    "A proposta foi preparada pelo especialista, mas "
                    "nenhuma capacidade de confirmação (ACT) está "
                    "anunciada pelo proprietário — a escrita não pode "
                    "prosseguir."
                ),
            )
        # Post-PREPARE operation-bound scope choice (B2 closure,
        # §6.184): a free-text MESSAGE is never ACT-eligible — a READY
        # proposal is ALWAYS held as a backend pending write awaiting a
        # typed decision (APPLY_PREPARED/REJECT_PREPARED) bound to the
        # exact proposal on a later turn. The owner confirmation policy
        # keeps its own meaning: `explicit_user_confirmation=false`
        # does NOT skip the user's execution-scope choice — it only
        # declares that the bound APPLY needs no ADDITIONAL owner
        # confirmation; `true` makes the same bound decision satisfy
        # the owner confirmation too. Either way, zero ACT this turn.
        pending_purpose = (
            PENDING_PURPOSE_SCOPE_PLUS_CONFIRMATION
            if confirmation_policy == CONFIRMATION_POLICY_CONFIRM
            else PENDING_PURPOSE_SCOPE_CHOICE
        )
        decision = evaluate_write_continuation(
            capability_live=act_capability is not None,
            confirmation_required=True,
            preview=preview,
            confirmation=None,
            now_epoch=time.time(),
        )
        self._audit(
            stage="DECISION_GATE",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=decision.status.value,
            proposal_digest=digest,
            preview_fingerprint=fingerprint,
            execution_mode=pending_purpose,
        )

        now = time.time()
        expires = preview.expires_at_epoch
        if expires is None:
            expires = now + DEFAULT_PENDING_TTL_SECONDS
        pending = PendingWrite(
            digest=digest,
            capability_ref=capability_ref,
            group_key=group_key,
            actor_user_id=str(actor_user_id or ""),
            session_id=str(session_id or ""),
            expires_at_epoch=expires,
            created_at_epoch=now,
            preview=preview,
            act_remote_capability=act_capability.remote_name,
            correlation_id=correlation,
            pending_purpose=pending_purpose,
        )
        self._pending_writes.put(pending)
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
            correlation_id=correlation,
            outcome=outcome,
            provenance=self._provenance(
                group_key, remote_name, remote_name, group, outcome
            ),
            content=_preview_render(preview),
            confirmation_context={
                "session_id": pending.session_id,
                "capability_ref": capability_ref,
                "proposal_digest": digest,
                "preview_fingerprint": fingerprint,
                "expires_at_epoch": expires,
                "pending_purpose": pending_purpose,
            },
            limitations=outcome.limitations,
        )

    def _attempt_direct_act(
        self,
        group_key: str,
        descriptor: ProviderCapability,
        arguments: Mapping[str, Any],
        group: CapabilityGroup,
        actor_user_id: str | None,
        session_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Gate a model-selected ACT capability — always fail closed.

        A cold ACT selection on a free-text MESSAGE can never execute
        (B2 closure, §6.184 §5): an ACT whose owner schema requires
        ``proposal_handle`` lacks the live PREPARE proposal it needs,
        and an ACT-only capability has no owner-verified preview to
        which a typed APPLY_PREPARED decision could bind — the runtime
        must not fabricate one. Both are refused truthfully.
        """
        if prepare_only:
            # Execution ceiling: an ACT capability can never run while
            # the turn is capped at PREPARE.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="execution_ceiling",
                content=(
                    "Esta sessão está limitada a preparação — a "
                    "operação não foi executada."
                ),
            )
        capability_ref = f"{group_key}.{descriptor.remote_name}"
        keys, required = _schema_keys(descriptor)
        if PROPOSAL_HANDLE_FIELD in keys or PROPOSAL_HANDLE_FIELD in required:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                content=(
                    "Essa operação exige uma proposta preparada pelo "
                    "especialista. Peça a alteração primeiro para gerar "
                    "uma prévia confirmável."
                ),
            )
        # ACT-only without a verifiable owner PREPARE proposal (B2
        # closure §5): there is no owner-verified preview/digest to
        # which a typed APPLY_PREPARED decision could bind — the
        # runtime cannot fabricate a preview, so the cold ACT
        # selection is refused truthfully instead of executing or
        # staging an unverifiable pending intent.
        self._audit(
            stage="DECISION_GATE",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=descriptor.remote_name,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision="PRECONDITION_REQUIRED",
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.WRITE_REJECTED,
            correlation_id=correlation,
            error_code="precondition_required",
            content=(
                "Essa operação é uma escrita sem prévia verificável "
                "do especialista — a execução não pode prosseguir a "
                "partir de texto livre."
            ),
        )

    def _attempt_confirmation(
        self,
        confirmation_payload: Mapping[str, Any],
        *,
        actor_user_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Bind a structured confirmation to a pending write.

        Fail closed on every dimension: unknown/expired digest,
        actor/session/fingerprint mismatch, reclassified or removed
        owner capability. The raw proposal handle stays backend-only —
        the wire carries digests only.
        """
        if prepare_only:
            # Execution ceiling (LOOP-03R1): no confirmation can reach
            # ACT while the turn is capped at PREPARE.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="execution_ceiling",
                content=(
                    "Esta sessão está limitada a preparação — a "
                    "operação não foi executada."
                ),
            )
        digest = str(confirmation_payload.get("proposal_digest") or "")
        record = self._pending_writes.get(digest)
        if record is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_unknown",
                content=(
                    "Nenhuma operação pendente corresponde a esta "
                    "confirmação — ela pode ter expirado ou já ter sido "
                    "respondida."
                ),
            )
        if str(actor_user_id or "") != record.actor_user_id:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.AUTHZ_DENIED,
                correlation_id=correlation,
                error_code="actor_mismatch",
                content="A confirmação não pertence a este usuário.",
            )
        session_id = str(confirmation_payload.get("session_id") or "")
        if not session_id or not record.session_id or (
            session_id != record.session_id
        ):
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="session_mismatch",
                content="A confirmação não pertence a esta sessão.",
            )
        fingerprint = str(
            confirmation_payload.get("preview_fingerprint") or ""
        )
        raw_decision = str(confirmation_payload.get("decision") or "")
        try:
            decision = ConfirmationDecision(raw_decision.upper())
        except ValueError:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_invalid",
                content="Decisão de confirmação inválida.",
            )

        if record.preview is None:
            # Pending intents without an owner-verified preview are no
            # longer created (§6.184 §5) — a bound decision has no
            # verified proposal to bind to, so it fails closed.
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_unknown",
                content=(
                    "Nenhuma proposta preparada corresponde a esta "
                    "confirmação."
                ),
            )
        return self._confirm_proposal(
            record, decision, fingerprint, actor_user_id, session_id,
            correlation, deadline,
        )

    def _confirm_proposal(
        self,
        record: PendingWrite,
        decision: ConfirmationDecision,
        fingerprint: str,
        actor_user_id: str | None,
        session_id: str,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        preview = record.preview
        assert preview is not None
        bound = bind_confirmation(
            preview=preview,
            confirmation=StructuredConfirmation(
                actor_user_id=str(actor_user_id or ""),
                session_id=session_id,
                capability_ref=record.capability_ref,
                proposal_digest=record.digest,
                preview_fingerprint=fingerprint,
                decision=decision,
                occurred_at_epoch=time.time(),
            ),
            expected_actor_id=record.actor_user_id,
            expected_session_id=record.session_id,
            now_epoch=time.time(),
        )
        # Validate before claiming: an invalid fingerprint, actor or
        # session may NEVER consume another caller's legitimate pending
        # proposal. A validated CONFIRM/REJECT still needs to win the
        # exclusive claim below before any ACT can proceed.
        if bound.state not in (
            ConfirmationState.CONFIRMED,
            ConfirmationState.REJECTED,
        ):
            reasons = ",".join(r.value for r in bound.reason_codes)
            self._audit(
                stage="CONFIRMATION_INVALID",
                capability_ref=record.capability_ref,
                group_id=record.group_key,
                owner_capability=preview.owner_capability,
                correlation_id=correlation,
                actor_user_id=actor_user_id,
                decision=bound.state.value,
                proposal_digest=record.digest,
                preview_fingerprint=fingerprint,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_mismatch",
                content=(
                    "A confirmação não corresponde à proposta exata "
                    f"({reasons}). Nenhuma escrita foi executada."
                ),
            )
        # RW-01: validated binding alone is NOT a winning claim.
        # Two requests can read the same pending record concurrently;
        # only the atomic, identity-checked consumer may proceed to ACT.
        # Do not hold the store lock across owner/network calls.
        claimed = self._pending_writes.take_if_current(
            record.digest, record
        )
        if claimed is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="confirmation_unknown",
                content=(
                    "Esta operação já foi respondida ou expirou. "
                    "Nenhuma escrita foi executada por esta decisão."
                ),
            )
        self._audit(
            stage="CONFIRMATION_BOUND",
            capability_ref=record.capability_ref,
            group_id=record.group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=bound.state.value,
            proposal_digest=record.digest,
            preview_fingerprint=fingerprint,
        )
        if bound.state is ConfirmationState.REJECTED:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                content="Operação cancelada — nenhuma escrita foi executada.",
            )
        # CONFIRMED still authorizes nothing: fresh live revalidation of
        # the owner surface precedes the ACT call, and live Core/Domain
        # AuthZ is enforced by the owner.
        #
        # Pending purpose (§6.184): `execution_scope_choice` — the owner
        # declared explicit_user_confirmation=false, so the bound APPLY
        # is the user's scope choice ONLY; it is NOT an owner
        # confirmation and must not reach the owner as one (confirmed=
        # False argument, reduction-only gate). `execution_scope_plus_
        # owner_confirmation` (and any legacy/unknown purpose — the
        # fail-safe direction) — the same bound decision additionally
        # satisfies the owner-required confirmation.
        requires_owner_confirmation = (
            record.pending_purpose != PENDING_PURPOSE_SCOPE_CHOICE
        )
        return self._execute_prepared_act(
            group_key=record.group_key,
            capability_ref=record.capability_ref,
            act_remote_capability=record.act_remote_capability,
            preview=preview,
            digest=record.digest,
            fingerprint=fingerprint,
            confirmation=bound if requires_owner_confirmation else None,
            execution_mode=(
                "explicit_user_confirmation"
                if requires_owner_confirmation
                else "execution_scope_choice"
            ),
            actor_user_id=actor_user_id,
            correlation=correlation,
            deadline=deadline,
        )

    def _execute_prepared_act(
        self,
        *,
        group_key: str,
        capability_ref: str,
        act_remote_capability: str | None,
        preview: WriteProposalPreview,
        digest: str,
        fingerprint: str,
        confirmation: ConfirmationRecord | None,
        execution_mode: str,
        actor_user_id: str | None,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """The single governed ACT execution path.

        A bound explicit user confirmation and an owner-declared
        direct policy converge here — fresh surface revalidation,
        capability-liveness check, decision gate, owner-invoked ACT
        and postcondition verification are identical for both; only
        the confirmation input differs. No path past this point can
        skip a gate.
        """
        try:
            group = self._fresh_group(group_key, correlation, deadline)
        except CapabilityProviderError as exc:
            return _error_attempt(correlation, exc)
        if group is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code="capability_group_offline",
                content=(
                    "O grupo de capacidades não está mais disponível. "
                    "Nenhuma escrita foi executada."
                ),
            )
        act_capability = (
            next(
                (
                    cap
                    for cap in group.capabilities
                    if cap.remote_name == act_remote_capability
                ),
                None,
            )
            if act_remote_capability
            else _find_act_capability(group, require_proposal_handle=True)
        )
        decision_gate = evaluate_write_continuation(
            capability_live=(
                act_capability is not None
                and invocable_in_interactive_phase(
                    act_capability.operation_class
                )
            ),
            confirmation_required=(
                execution_mode == "explicit_user_confirmation"
            ),
            preview=preview,
            confirmation=confirmation,
            now_epoch=time.time(),
        )
        self._audit(
            stage="DECISION_GATE",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=preview.owner_capability,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=decision_gate.status.value,
            proposal_digest=digest,
            preview_fingerprint=fingerprint,
            execution_mode=execution_mode,
        )
        if decision_gate.status.value != "READY_FOR_LIVE_REVALIDATION":
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.WRITE_REJECTED,
                correlation_id=correlation,
                error_code=",".join(
                    r.value for r in decision_gate.reason_codes
                ),
                content=(
                    "A capacidade de confirmação não está mais "
                    "disponível na superfície viva do especialista. "
                    "Nenhuma escrita foi executada."
                ),
            )
        assert act_capability is not None
        act_arguments = _act_arguments(
            act_capability,
            preview.proposal_ref,
            confirmed=confirmation is not None,
        )
        return self._invoke_act(
            group,
            act_capability.remote_name,
            act_arguments,
            correlation,
            deadline,
            actor_user_id=actor_user_id,
            capability_ref=(
                f"{group_key}.{act_capability.remote_name}"
            ),
            execution_mode=execution_mode,
        )

    def _invoke_act(
        self,
        group: CapabilityGroup,
        remote_name: str,
        arguments: Mapping[str, Any],
        correlation: str,
        deadline: TurnDeadline | None = None,
        *,
        actor_user_id: str | None,
        capability_ref: str,
        execution_mode: str | None = None,
    ) -> GovernedCapabilityAttempt:
        """Invoke the owner ACT capability and project the outcome.

        A technical success is never projected as a verified business
        outcome — only the owner's explicit ``verified`` postcondition
        evidence produces VERIFIED.
        """
        group_key = f"{group.provider_id}:{group.group_id}"
        self._audit(
            stage="ACT_ATTEMPT",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=remote_name,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision="INVOKED",
            execution_mode=execution_mode,
        )
        try:
            outcome = self._invoke(
                group, remote_name, dict(arguments), correlation,
                deadline,
            )
        except CapabilityProviderError as exc:
            _logger.info(
                "orchestration stage=act_invoke decision=error "
                "error_code=%s detail=%s correlation_id=%s",
                exc.code,
                exc.message[:240],
                correlation,
            )
            return _error_attempt(correlation, exc)
        projection = project_write_outcome(
            capability_ref=capability_ref,
            remote_capability=remote_name,
            owner_payload=outcome.structured or {},
            specialist_id=group_key,
            correlation_id=correlation,
            occurred_at=outcome.provenance.observed_at,
            limitations=outcome.limitations,
        )
        self._audit(
            stage="OUTCOME_VERIFIED",
            capability_ref=capability_ref,
            group_id=group_key,
            owner_capability=remote_name,
            correlation_id=correlation,
            actor_user_id=actor_user_id,
            decision=projection.status.value,
            execution_mode=execution_mode,
        )
        rendered = render_specialist_outcome_rich(
            outcome, field_labels=self._field_labels
        )
        content = rendered.content
        limitations = rendered.limitations
        markdown_content = rendered.markdown
        note = _OUTCOME_NOTE.get(projection.status)
        if note is not None:
            content = f"{content}\n\n{note}" if content else note
            if markdown_content is not None:
                markdown_content = f"{markdown_content}\n\n{note}"
        return self._outcome_attempt(
            group_key,
            remote_name,
            remote_name,
            group,
            outcome,
            correlation,
            content=content,
            markdown_content=markdown_content,
            limitations=limitations,
        )

    def _provenance(
        self,
        group_key: str,
        remote_used: str,
        action_id: str,
        group: CapabilityGroup,
        outcome: SpecialistOutcome,
    ):
        """Bounded user-facing provenance of one owner invocation."""
        source = group.source or SourceRef(
            source_id=group.owner_ref,
            source_system=group.owner_ref,
            provider_name=group.display_name,
        )
        return GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id=source.source_id,
                    source_system=source.source_system,
                    provider_name=source.provider_name,
                    observed_at=outcome.provenance.observed_at,
                ),
            ),
            specialist_id=outcome.provenance.specialist_id,
            remote_capability=outcome.provenance.remote_name,
            action_id=action_id,
            protocol=outcome.provenance.protocol.value,
            observed_at=outcome.provenance.observed_at,
            correlation_id=outcome.provenance.correlation_id,
            is_complete=outcome.is_complete,
            provider_id=group.provider_id,
            capability_group_id=group.group_id,
        )

    def _apply_outcome_assessment(
        self,
        outcome: SpecialistOutcome,
        verdict: OutcomeVerdict | None,
        correlation: str,
    ) -> SpecialistOutcome:
        """CRI E2 — governed sufficiency assessment at the binding edge.

        Response-intelligence ON only: the caller computes one verdict
        (typed facts x goal-stage ``answer_requirements`` hypothesis)
        and shares it with the E3 presentation composer — the wire
        keeps SUCCESS, insufficiency is marked on the outcome's own
        limitations so every render path carries it; status is never
        rewritten and no confident answer is fabricated. OFF (or no
        verdict) returns the outcome untouched (byte-identical
        baseline).
        """
        if not self._cri_active or verdict is None:
            return outcome
        _logger.info(
            "orchestration stage=outcome_assessment "
            "decision=%s reasons=%s correlation_id=%s",
            verdict.decision,
            ",".join(verdict.reasons),
            correlation,
        )
        # R3/M04: the sufficiency->limitation rule lives in the
        # assessment owner; the coordinator keeps activation gating
        # and observability as minimal glue.
        return apply_verdict_limitation(outcome, verdict)

    # ---- CRI E3 — grounded conversational composition ------------

    _CRI_RECORD_SCAN = 32

    def _compose_cri_response(
        self,
        facts: EvidenceFacts | None,
        verdict: OutcomeVerdict | None,
        goal: _TurnGoal,
        correlation: str,
        *,
        contract_text: str | None = None,
        projected_content: str | None = None,
    ) -> CriComposition | None:
        """CRI E3 — one grounded conversational composition.

        Active only when CRI is on AND the governed vocabulary
        resource was injected; prior-turn excerpt records keep the
        existing render (their content is already phrased). The
        composed content carries the count actually presented — a
        projection shortfall re-marks insufficiency instead of
        claiming success (E3-G2). Any failure degrades to the
        synthesized render — composition is an enhancement, never a
        correctness dependency.
        """
        if (
            not self._cri_present_active
            or facts is None
            or verdict is None
        ):
            return None
        if records_are_prior_excerpts(facts.records):
            return None
        # R3/M05: record presentation and ordering preparation live
        # in the composition owner; the coordinator keeps activation
        # gating, call ledger and observability as minimal glue.
        prepared = tuple(
            presented_record(record, self._field_labels)
            for record in facts.records[: self._CRI_RECORD_SCAN]
        )
        req = goal.answer_requirements
        ordering_date, ordering_event = ordering_presentation(
            facts.records, verdict, req, contract_text
        )
        comp_started = time.monotonic()
        cri = compose_cri_response(
            verdict=verdict,
            requirements=req,
            records=prepared,
            delivered_count=distinct_delivered_count(facts.records),
            total_count=facts.total_count,
            coverage_complete=facts.coverage_complete,
            ordering_date=ordering_date,
            ordering_event=ordering_event,
            vocabulary=self._cri_vocabulary,
            contract_facts=facts.contract_facts,
            projected_content=projected_content,
        )
        comp_ledger = current_call_ledger()
        if comp_ledger is not None:
            comp_ledger.record_composition(
                int((time.monotonic() - comp_started) * 1000)
            )
        _logger.info(
            "orchestration stage=cri_response decision=%s "
            "presented=%s delivered=%s semantic_proposed=%s "
            "ordering_event=%s correlation_id=%s",
            "composed" if cri is not None else "fallback",
            cri.presented_records if cri is not None else 0,
            len(facts.records),
            (
                req is not None and req.ordering_semantic is not None
            ),
            ordering_event or "none",
            correlation,
        )
        return cri

    def _outcome_attempt(
        self,
        group_key: str,
        remote_used: str,
        action_id: str,
        group: CapabilityGroup,
        outcome: SpecialistOutcome,
        correlation: str,
        *,
        content: str | None = None,
        limitations: tuple[str, ...] | None = None,
        markdown_content: str | None = None,
        extra_source_refs: tuple[SourceRef, ...] = (),
        input_text: str | None = None,
        composition_mode: str | None = None,
    ) -> GovernedCapabilityAttempt:
        """Assemble a SUCCESS attempt from an owner outcome.

        ``extra_source_refs`` appends additional bounded business
        sources (multi-source corroboration) after the primary ref —
        deduplicated, deterministic order. ``input_text`` enables
        goal-aligned deterministic rendering when synthesis demotes.
        ``composition_mode`` carries the effective answer composition
        observed at this seam (e.g. ``"cri"``) — presentation-only,
        never authority. ``markdown_content`` carries the deterministic
        markdown projection of the same admitted structured payload —
        callers that synthesize prose pass ``content`` without it, so
        model text never becomes ``markdown_safe`` (Category C).
        """
        binding = GovernedCapabilityBinding(
            binding_id=f"{group_key}.{remote_used}",
            group_key=group_key,
            remote_capability=remote_used,
            action_id=action_id,
            source=(
                group.source
                or SourceRef(
                    source_id=group.owner_ref,
                    source_system=group.owner_ref,
                    provider_name=group.display_name,
                )
            ),
            provider_id=group.provider_id,
            capability_group_id=group.group_id,
        )

        def _render(out: SpecialistOutcome) -> RenderedSpecialistOutcome:
            return render_specialist_outcome_rich(
                out,
                input_text=input_text,
                field_labels=self._field_labels,
            )

        if content is None and not extra_source_refs:
            attempt = _success_attempt(
                correlation_id=correlation,
                binding=binding,
                outcome=outcome,
                render=_render,
            )
            if composition_mode is not None:
                attempt = dataclasses.replace(
                    attempt, composition_mode=composition_mode
                )
            return attempt
        provenance = self._provenance(
            group_key, remote_used, action_id, group, outcome
        )
        if extra_source_refs:
            seen = {
                (ref.source_id, ref.source_system)
                for ref in provenance.source_refs
            }
            provenance = dataclasses.replace(
                provenance,
                source_refs=provenance.source_refs
                + tuple(
                    ref
                    for ref in extra_source_refs
                    if (ref.source_id, ref.source_system) not in seen
                ),
            )
        if content is None:
            rendered = render_specialist_outcome_rich(
                outcome,
                input_text=input_text,
                field_labels=self._field_labels,
            )
            content = rendered.content
            markdown_content = rendered.markdown
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            outcome=outcome,
            provenance=provenance,
            content=content,
            markdown_content=markdown_content,
            # Synthesized/alternate content never drops owner-reported
            # limitations — they stay attached to the attempt.
            limitations=(
                limitations
                if limitations is not None
                else outcome.limitations
            ),
            composition_mode=composition_mode,
        )

    def _audit(
        self,
        *,
        stage: str,
        capability_ref: str,
        group_id: str,
        owner_capability: str,
        correlation_id: str,
        actor_user_id: str | None,
        decision: str,
        proposal_digest: str | None = None,
        preview_fingerprint: str | None = None,
        execution_mode: str | None = None,
    ) -> None:
        """Bounded audit event — digest refs only, never raw handles."""
        _logger.info(
            "governed_write stage=%s decision=%s group_id=%s "
            "capability_ref=%s owner_capability=%s correlation_id=%s "
            "actor_user_id=%s proposal_digest=%s preview_fingerprint=%s "
            "execution_mode=%s",
            stage,
            decision,
            group_id,
            capability_ref,
            owner_capability,
            correlation_id,
            actor_user_id or "",
            proposal_digest or "",
            preview_fingerprint or "",
            execution_mode or "",
        )

    # ---------------- internals ----------------

    def _groups(
        self,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> tuple[dict[str, CapabilityGroup], list[str]]:
        """Live provider capability groups keyed by group key."""
        groups: dict[str, CapabilityGroup] = {}
        failures: list[str] = []
        for provider_id, provider in self._providers.items():
            # LOOP-03R2A-R1: each provider consultation is bounded by
            # the remaining turn budget — never starts exhausted and
            # never widens the provider's own stage max.
            if deadline is not None:
                deadline.check("surface_list")
            if _cancel_observed():
                raise _TurnCancelled()
            try:
                surface = provider.list_groups(
                    correlation_id=correlation,
                    timeout_seconds=(
                        deadline.remaining_seconds()
                        if deadline is not None
                        else None
                    ),
                )
            except CapabilityProviderError as exc:
                failures.append(exc.code)
                continue
            # A provider that overran the remaining budget may not
            # contribute results to this turn — fail truthfully.
            if deadline is not None:
                deadline.check("surface_list")
            failures.extend(surface.failures)
            for group in surface.groups:
                groups[f"{provider_id}:{group.group_id}"] = group
        return groups, failures

    def _fresh_group(
        self,
        group_key: str,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> CapabilityGroup | None:
        """Re-resolve one group live — provider-side revalidation."""
        provider_id, _, group_id = group_key.partition(":")
        provider = self._providers.get(provider_id)
        if provider is None or not group_id:
            return None
        if deadline is not None:
            deadline.check("surface_relist")
        if _cancel_observed():
            raise _TurnCancelled()
        surface = provider.list_groups(
            correlation_id=correlation,
            timeout_seconds=(
                deadline.remaining_seconds()
                if deadline is not None
                else None
            ),
        )
        if deadline is not None:
            deadline.check("surface_relist")
        return next(
            (g for g in surface.groups if g.group_id == group_id), None
        )

    def _select_target(
        self,
        input_text: str,
        groups: Mapping[str, CapabilityGroup],
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        deadline: TurnDeadline | None = None,
        correlation: str = "",
        *,
        interpret_goal: bool = False,
    ) -> (
        tuple[str, str, ProviderCapability, "_TurnGoal | None"]
        | tuple[str]
        | None
    ):
        """Hierarchical bounded selection, never authority.

        SELECT GROUP -> SELECT CAPABILITY. Argument projection is a
        separate stage because an opaque envelope capability requires
        owner DISCOVERY evidence first (§6.131 R1). Each stage is
        revalidated deterministically against the fresh live groups;
        workspace context is an untrusted hint only. Without a model
        the turn falls back to the ordinary interaction path.

        Returns:
        - ``("selected", group_key, descriptor, goal)``
        - ``("not_applicable",)`` when no group is required / applicable
        - ``("inconclusive",)`` when a group path was attempted but no
          capability could be bound (clarify, do not free-form invent)
        - ``None`` when no model is configured

        When ``interpret_goal`` is True (cold start), capability
        selection may return a validated ``_TurnGoal`` from the same
        typed proposal (I02-R3B). Otherwise the third element is None.
        """
        if self._invoke_model is None or self._model_ref is None:
            return None
        group_status, group_key = self._select_group(
            input_text,
            groups,
            workspace_context,
            prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if group_status == "not_applicable":
            _logger.info(
                "orchestration stage=select_group decision=none "
                "groups=%d",
                len(groups),
            )
            return ("not_applicable",)
        if group_status == "invalid" or group_key is None or (
            group_key not in groups
        ):
            _logger.info(
                "orchestration stage=select_group decision=invalid "
                "groups=%d",
                len(groups),
            )
            return ("inconclusive",)
        group = groups[group_key]
        if interpret_goal:
            cap_status, descriptor, selected_goal = (
                self._select_capability_with_goal(
                    input_text,
                    group,
                    workspace_context,
                    prior_turns,
                    correlation=correlation,
                    deadline=deadline,
                )
            )
        else:
            cap_status, descriptor = self._select_capability(
                input_text,
                group,
                workspace_context,
                prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
            selected_goal = None
        if descriptor is None:
            # Q02-A: no lexical coverage-inquiry override. Capability
            # applicability remains a validated model proposal only.
            if cap_status == "not_applicable":
                # The group path WAS attempted and bound nothing — a
                # distinct signal from group-level not_applicable so
                # the caller can mark the deterministic insufficiency
                # terminal instead of free-form conversational prose.
                _logger.info(
                    "orchestration stage=select_capability "
                    "decision=not_applicable group=%s",
                    group_key,
                )
                return ("not_applicable_capability",)
            else:
                _logger.info(
                    "orchestration stage=select_capability decision=none "
                    "group=%s",
                    group_key,
                )
                return ("inconclusive",)
        return ("selected", group_key, descriptor, selected_goal)

    def _build_plan(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        group: CapabilityGroup,
        discovery: ProviderCapability | None,
        correlation: str,
        resolver: ProviderCapability | None = None,
        foreign: ProviderCapability | None = None,
        foreign_group: CapabilityGroup | None = None,
    ) -> PlanCandidate | None:
        """Assemble and validate the bounded operational plan.

        Steps are generated deterministically by the orchestrator —
        never by the model. Supported shapes (max
        ``MAX_OPERATIONAL_PLAN_STEPS``): DISCOVERY -> target;
        RESOLVER -> target; DISCOVERY -> RESOLVER -> target;
        ANALYSIS -> PREPARE (the analysis step is a non-mutating
        evidence role, structurally identical to a resolver);
        DISCOVERY -> ANALYSIS -> PREPARE; plus one optional
        cross-group evidence step (LOOP-02) between DISCOVERY and the
        target. The shared ``validate_plan_candidate`` rules revalidate
        every step against the live capability view of ALL
        participating groups, the step bound, and backward-only
        dependencies; any failure fails closed.
        """
        ordered = [
            ("owner capability vocabulary discovery", discovery),
            ("cross-group semantic evidence", foreign),
            (
                "owner analysis evidence"
                if resolver is not None
                and resolver.operation_class
                is SpecialistOperationClass.ANALYSIS
                else "same-owner non-mutating evidence resolution",
                resolver,
            ),
            (input_text[:MAX_DESCRIPTION_CHARS], descriptor),
        ]
        steps: list[PlanStep] = []
        for intent, capability in ordered:
            if capability is None:
                continue
            character = _PLAN_OPERATION_CHARACTER.get(
                capability.operation_class
            )
            if character is None:
                return None
            steps.append(
                PlanStep(
                    step_id=f"step-{len(steps) + 1}",
                    intent=intent[:MAX_DESCRIPTION_CHARS],
                    capability_id=capability.capability_id,
                    operation_character=character,
                    depends_on_step_ids=tuple(
                        step.step_id for step in steps
                    ),
                )
            )
        plan = PlanCandidate(
            plan_id=f"plan-{correlation}",
            goal=input_text[:MAX_DESCRIPTION_CHARS],
            steps=tuple(steps),
        )
        plan_views = _plan_views(group)
        if foreign_group is not None:
            plan_views = plan_views + _plan_views(foreign_group)
        validation = validate_plan_candidate(
            plan,
            plan_views,
            max_steps=MAX_OPERATIONAL_PLAN_STEPS,
        )
        if not validation.valid:
            _logger.info(
                "operational_plan decision=rejected codes=%s "
                "correlation_id=%s",
                ",".join(code.value for code in validation.error_codes),
                correlation,
            )
            return None
        return plan

    @staticmethod
    def _log_plan(
        plan: PlanCandidate, correlation: str, *, discovery_ran: bool
    ) -> None:
        """Bounded plan audit — step ids and capability refs only."""
        _logger.info(
            "operational_plan decision=accepted steps=%s "
            "discovery_ran=%s correlation_id=%s",
            ";".join(
                f"{step.step_id}:{step.capability_id}"
                for step in plan.steps
            ),
            discovery_ran,
            correlation,
        )

    def _model_stage_proposal(
        self,
        input_text: str,
        *,
        block_tag: str,
        block_payload: str,
        instruction_id: str,
        instruction: str,
        instruction_lineage: tuple[str, ...],
        expected_fields: tuple[str, ...],
        input_kind: str,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str | None = None,
        deadline: TurnDeadline | None = None,
    ) -> Mapping[str, Any] | None:
        """One bounded model stage — raw structured proposal or None.

        Shared invocation mechanics for every orchestrator-owned model
        call: deadline check, stage-timeout resolution with cold-start
        headroom, minimum-viable-budget fail-fast, request assembly,
        error/timeout taxonomy and bounded stage logging. Per-purpose
        proposal validation stays with each caller.
        """
        if self._invoke_model is None or self._model_ref is None:
            return None
        if deadline is not None:
            try:
                deadline.check("model_propose")
            except TurnBudgetExhausted as exc:
                raise _StageDeadlineExceeded(
                    "turn_budget_exhausted"
                ) from exc
        # CP5/R3: cancellation observed mid-attempt stops the next real
        # operation — no new model call (and no replay) after a
        # disconnect; the attempt unwinds to the honest terminal.
        if _cancel_observed():
            raise _TurnCancelled()
        # CP4 governed resume: a recorded proposal replays only for a
        # byte-identical stage input — completed typed work survives a
        # downstream timeout without re-spending the model, and every
        # deterministic gate downstream still re-validates it against
        # the fresh live surface.
        resume_state = _RESUME_STATE.get()
        stage_key = _resume_stage_key(
            instruction_id, input_text, block_tag, block_payload
        )
        if resume_state is not None and stage_key in resume_state.proposals:
            _logger.info(
                "orchestration stage=model_propose decision=resumed "
                "purpose=%s correlation_id=%s",
                instruction_id,
                correlation or "",
            )
            return resume_state.proposals[stage_key]
        stage_timeout = (
            deadline.stage_timeout(self._model_stage_timeout_seconds)
            if deadline is not None
            else self._model_stage_timeout_seconds
        )
        # Cold-start headroom: when remaining budget is still large and
        # the stage env cap could consume it whole (doc 47), leave room
        # for conversational synthesis after a selection miss. Do NOT
        # apply this reserve mid-turn when remaining is already tight —
        # that would abort legitimate late stages as budget_exhausted.
        # Doc 103: the former 15s admission sub-cap is removed — every
        # logical LLM call shares the same 60s ceiling; no stage-local
        # artificial cut.
        if deadline is not None:
            remaining = deadline.remaining_seconds()
            if (
                instruction_id == GROUP_SELECTION_INSTRUCTION_ID
                and remaining
                >= (
                    CONVERSATIONAL_FALLBACK_RESERVE_SECONDS
                    + MIN_VIABLE_MODEL_STAGE_SECONDS * 2
                )
            ):
                stage_timeout = min(
                    stage_timeout,
                    max(
                        0.0,
                        remaining
                        - CONVERSATIONAL_FALLBACK_RESERVE_SECONDS,
                    ),
                )
        # Honest stop: do not start a model stage that cannot finish
        # usefully within the remaining turn budget.
        if stage_timeout < MIN_VIABLE_MODEL_STAGE_SECONDS:
            _logger.info(
                "orchestration stage=model_propose "
                "decision=budget_too_small purpose=%s "
                "remaining_ms=%d correlation_id=%s",
                instruction_id,
                int(stage_timeout * 1000),
                correlation or "",
            )
            raise _StageDeadlineExceeded("turn_budget_exhausted")
        workspace_block = (
            "\n<workspace_context>\n"
            + workspace_context.to_prompt_block()
            + "\n</workspace_context>"
            if workspace_context is not None
            else ""
        )
        # Doc 103: governed retry INSIDE one logical model call — the
        # same bounded request may be invoked at most
        # LLM_CALL_MAX_ATTEMPTS times for recoverable classes (call
        # timeout, transient provider failure, invalid structured
        # output), only while budget remains and no cancellation was
        # observed. Never a retry of the turn, the MCP invoke or any
        # material operation.
        call_attempt = 0
        while True:
            call_attempt += 1
            # Per-call ceiling: min(60s stage cap, remaining budget).
            call_timeout = (
                min(stage_timeout, deadline.remaining_seconds())
                if deadline is not None
                else stage_timeout
            )
            if deadline is not None:
                remaining = deadline.remaining_seconds()
                if (
                    instruction_id == GROUP_SELECTION_INSTRUCTION_ID
                    and remaining
                    >= (
                        CONVERSATIONAL_FALLBACK_RESERVE_SECONDS
                        + MIN_VIABLE_MODEL_STAGE_SECONDS * 2
                    )
                ):
                    # Retries of a selection call re-honor the fallback
                    # reserve — a retried call may never consume the
                    # budget reserved for conversational synthesis.
                    call_timeout = min(
                        call_timeout,
                        max(
                            0.0,
                            remaining
                            - CONVERSATIONAL_FALLBACK_RESERVE_SECONDS,
                        ),
                    )
            if call_timeout < MIN_VIABLE_MODEL_STAGE_SECONDS:
                raise _StageDeadlineExceeded("turn_budget_exhausted")
            # Stage 6 budget attribution: budget still available when
            # this invocation was granted its timeout.
            call_remaining_ms = (
                int(deadline.remaining_seconds() * 1000)
                if deadline is not None
                else None
            )
            started = time.monotonic()
            try:
                result = self._invoke_model.execute(
                    ModelInvocationRequest(
                        invocation_id=ModelInvocationId(str(uuid.uuid4())),
                        model_ref=self._model_ref,
                        prior_context=prior_turns,
                        input_text=(
                            "<user_message>\n"
                            + input_text
                            + "\n</user_message>"
                            + workspace_block
                            + "\n<"
                            + block_tag
                            + ">\n"
                            + block_payload
                            + "\n</"
                            + block_tag
                            + ">"
                        ),
                        task_purpose_id=instruction_id,
                        output_schema_id=instruction_id,
                        output_schema_version=SELECTION_INSTRUCTION_VERSION,
                        expected_fields=expected_fields,
                        instruction_lineage=instruction_lineage,
                        instruction_content=instruction,
                        timeout_seconds=call_timeout,
                        declared_epistemic_class=EpistemicClass.HYPOTHESIS,
                        untrusted_external_metadata={
                            "interaction_surface": "delia-mfe",
                            "input_kind": input_kind,
                        },
                    )
                )
                break
            except ModelInvocationError as exc:
                # Prompt 5: a REAL model call that failed or timed out —
                # counted as a call; usage stays absent (never
                # fabricated).
                ledger = current_call_ledger()
                if ledger is not None:
                    ledger.record_error(
                        stage=instruction_id,
                        finish_status=(
                            "timeout" if exc.code == TIMEOUT else "error"
                        ),
                        attempt=_ATTEMPT_INDEX.get(),
                        duration_ms=int(
                            (time.monotonic() - started) * 1000
                        ),
                        budget_remaining_ms=call_remaining_ms,
                        error_code=exc.code,
                        context_budget=getattr(
                            exc, "context_budget", None
                        ),
                    )
                _logger.info(
                    "orchestration stage=model_propose decision=error "
                    "purpose=%s error_code=%s call_attempt=%d "
                    "timing_ms=%d correlation_id=%s",
                    instruction_id,
                    exc.code,
                    call_attempt,
                    int((time.monotonic() - started) * 1000),
                    correlation or "",
                )
                if not call_retry_eligible(
                    exc.code, call_attempt, self._llm_call_max_attempts
                ):
                    # LOOP-03R2A: a model-stage TIMEOUT is a governed
                    # orchestration failure — it terminates at the
                    # attempt boundary, never as a NOT_APPLICABLE that
                    # degrades into a general-model answer.
                    if exc.code == TIMEOUT:
                        raise _StageDeadlineExceeded(
                            "model_timeout"
                        ) from exc
                    return None
                # Cancellation between retries must not start a new
                # real call — unwind to the honest terminal.
                if _cancel_observed():
                    raise _TurnCancelled()
                _emit_activity(
                    phase=ActivityPhase.CONTINUING,
                    correlation=correlation,
                )
                _logger.info(
                    "orchestration stage=model_propose decision=retry "
                    "purpose=%s call_attempt=%d correlation_id=%s",
                    instruction_id,
                    call_attempt + 1,
                    correlation or "",
                )
                continue
        # LOOP-03R1 (latency): bounded stage timing per proposal
        # purpose — no payload, no user text, no values.
        _logger.info(
            "orchestration stage=model_propose decision=ok "
            "purpose=%s timing_ms=%d correlation_id=%s",
            instruction_id,
            int((time.monotonic() - started) * 1000),
            correlation or "",
        )
        # Prompt 5: a REAL model call completed — provider usage and
        # measured duration were already carried by
        # ModelInvocationResult; record them verbatim for the
        # presentation-only observability projection.
        ledger = current_call_ledger()
        if ledger is not None:
            ledger.record_result(
                stage=instruction_id,
                result=result,
                attempt=_ATTEMPT_INDEX.get(),
                budget_remaining_ms=call_remaining_ms,
            )
        proposal = result.structured_output
        if not isinstance(proposal, Mapping):
            return None
        if resume_state is not None:
            resume_state.proposals[stage_key] = proposal
        return proposal

    def _propose(
        self,
        input_text: str,
        *,
        block_tag: str,
        block_payload: str,
        instruction_id: str,
        instruction: str,
        expected_fields: tuple[str, ...],
        input_kind: str,
        allowed_keys: frozenset[str],
        instruction_version: str | None = None,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str | None = None,
        deadline: TurnDeadline | None = None,
    ) -> Mapping[str, Any] | None:
        """One bounded model proposal — structured output only."""
        proposal = self._model_stage_proposal(
            input_text,
            block_tag=block_tag,
            block_payload=block_payload,
            instruction_id=instruction_id,
            instruction=instruction,
            instruction_lineage=_lineage(
                instruction_id,
                instruction,
                instruction_version or SELECTION_INSTRUCTION_VERSION,
            ),
            expected_fields=expected_fields,
            input_kind=input_kind,
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return None
        # Surplus keys (e.g. adapter-suggested "limitations" on a
        # selection-only schema) must not discard a valid proposal —
        # Stage 05 live: grounded_synthesis returned ok then prior
        # continuity saw proposal_absent after a hard allowed_keys
        # reject. Project to the declared contract instead.
        extra = set(proposal) - allowed_keys
        if extra:
            _logger.info(
                "orchestration stage=model_propose "
                "decision=strip_extra purpose=%s extra_keys=%s "
                "correlation_id=%s",
                instruction_id,
                ",".join(sorted(str(k) for k in extra)[:8]),
                correlation or "",
            )
            proposal = {
                key: value
                for key, value in proposal.items()
                if key in allowed_keys
            }
        # Selection proposals may declare applicable=false with null
        # companion ids — do not reject solely for a missing
        # capability_group_id / remote_name in that case.
        applicable = proposal.get("applicable")
        if isinstance(applicable, str):
            applicable = applicable.strip().lower() == "true"
        if applicable is False and "applicable" in expected_fields:
            return proposal
        if any(field not in proposal for field in expected_fields):
            return None
        return proposal

    # -------- C3-INTELLIGENCE-LOOP-01: bounded user-facing stages --------

    MAX_REPLAN_ROUNDS = 1

    def _clarification_question(
        self,
        input_text: str,
        missing_inputs: tuple[str, ...],
        descriptor: ProviderCapability,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> str:
        """Missing inputs become a business question, never field names.

        The model may propose wording; deterministic gates keep
        technical internals (snake_case fields, handles, routes,
        provider mechanics, authority claims) off the user surface.
        Any proposal failure falls back to the generic deterministic
        ask-back — it never derives wording from missing input names.
        """
        block_payload = json.dumps(
            {
                "missing_inputs": list(missing_inputs),
                "capability_description": (descriptor.description or "")[
                    :MAX_DESCRIPTION_CHARS
                ],
            },
            ensure_ascii=False,
            default=str,
        )[:MAX_SURFACE_CHARS]
        try:
            proposal = self._propose(
                input_text,
                block_tag="missing_inputs",
                block_payload=block_payload,
                instruction_id=CLARIFICATION_INSTRUCTION_ID,
                instruction=self._instruction(CLARIFICATION_INSTRUCTION_ID),
                expected_fields=("question",),
                input_kind="clarification_wording",
                allowed_keys=frozenset({"question", "limitations"}),
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded:
            # Prefer a deterministic ask-back over a timed-out wording
            # stage that would collapse the turn to PROCESSING_TIMEOUT.
            _logger.info(
                "orchestration stage=clarification "
                "decision=budget_fallback correlation_id=%s",
                correlation,
            )
            return _clarification_content(
                missing_inputs, user_message=input_text
            )
        question = (
            proposal.get("question") if isinstance(proposal, Mapping) else None
        )
        if isinstance(question, str):
            wording = _redact_text(question.strip())[
                :MAX_RENDER_CONTENT_CHARS
            ]
            # The proposed wording must not echo the internal names it
            # was asked to translate, nor any other technical surface.
            leaks_internal_name = any(
                name in wording for name in missing_inputs
            )
            if wording and not leaks_internal_name and not (
                _wording_leaks_technical(wording)
            ):
                _logger.info(
                    "orchestration stage=clarification "
                    "decision=model_wording correlation_id=%s",
                    correlation,
                )
                return wording
        _logger.info(
            "orchestration stage=clarification decision=fallback "
            "correlation_id=%s",
            correlation,
        )
        return _clarification_content(
            missing_inputs, user_message=input_text
        )

    def _maybe_aggregate_paginated_count(
        self,
        input_text: str,
        outcome: SpecialistOutcome,
        arguments: Mapping[str, Any],
        group_key: str,
        remote_name: str,
        group: CapabilityGroup,
        correlation: str,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline | None,
    ) -> SpecialistOutcome:
        """Bounded same-capability page walk for COUNT intents (R5).

        Only for non-personal / all-visible scopes. Personal assigned /
        requested / ambiguous paths never aggregate visible pages into
        a fabricated personal total. Stops on ``has_more=False``,
        authoritative total, page failure, duplicate storm, max pages,
        or turn-budget headroom exhaustion — never invents a total.
        """
        intent = classify_result_intent(input_text)
        scope = classify_personal_ticket_scope(input_text)
        if intent is not ResultIntent.COUNT:
            return outcome
        if scope in {
            PersonalTicketScope.MY_TICKETS_AMBIGUOUS,
            PersonalTicketScope.ASSIGNED_TO_ME,
            PersonalTicketScope.REQUESTED_BY_ME,
        }:
            return outcome
        envelope = extract_pagination_envelope(outcome.structured)
        if envelope is None:
            return outcome
        if envelope.total_count is not None:
            return outcome
        if envelope.has_more is not True:
            return outcome
        if not isinstance(arguments, Mapping):
            return outcome
        # Owner must expose a page cursor we can advance.
        page_key = next(
            (
                key
                for key in arguments
                if str(key).strip().lower().replace("-", "_") == "page"
            ),
            None,
        )
        if page_key is None:
            return outcome

        pages: list[object] = [outcome.structured]
        try:
            current_page = int(arguments.get(page_key) or envelope.page or 1)
        except (TypeError, ValueError):
            current_page = envelope.page or 1
        max_pages = DEFAULT_MAX_PAGES
        while len(pages) < max_pages:
            if deadline is not None and (
                deadline.remaining_seconds()
                < MIN_VIABLE_MODEL_STAGE_SECONDS * 3
            ):
                _logger.info(
                    "orchestration stage=pagination "
                    "decision=budget_exhausted pages=%d "
                    "correlation_id=%s",
                    len(pages),
                    correlation,
                )
                break
            current_page += 1
            next_arguments = dict(arguments)
            next_arguments[page_key] = current_page
            try:
                invoked = self._invoke_selected(
                    group_key,
                    remote_name,
                    next_arguments,
                    group,
                    input_text,
                    correlation,
                    prior_turns,
                    deadline,
                )
            except CapabilityProviderError:
                pages.append(None)
                break
            if invoked is None:
                pages.append(None)
                break
            next_outcome, _, _ = invoked
            next_envelope = extract_pagination_envelope(
                next_outcome.structured
            )
            if next_envelope is None:
                pages.append(None)
                break
            pages.append(next_outcome.structured)
            if next_envelope.total_count is not None:
                break
            if next_envelope.has_more is not True:
                break

        aggregation = aggregate_paginated_pages(pages, max_pages=max_pages)
        _logger.info(
            "orchestration stage=pagination decision=%s pages=%d "
            "unique=%d duplicates=%d correlation_id=%s",
            "complete" if aggregation.complete else "partial",
            aggregation.pages_fetched,
            aggregation.unique_count,
            len(aggregation.duplicate_ids),
            correlation,
        )
        base = (
            dict(outcome.structured)
            if isinstance(outcome.structured, Mapping)
            else {}
        )
        merged: dict[str, Any] = {
            **base,
            "items": [dict(item) for item in aggregation.items],
            "page": 1,
            "page_size": aggregation.unique_count,
            "has_more": not aggregation.complete,
        }
        if aggregation.authoritative_total is not None:
            merged["total_count"] = aggregation.authoritative_total
        elif aggregation.complete and not aggregation.duplicate_ids:
            merged["has_more"] = False
        return dataclasses.replace(outcome, structured=merged)

    def _synthesize_content(
        self,
        input_text: str,
        outcome: SpecialistOutcome,
        correlation: str,
        deadline: TurnDeadline | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        business_subject: str | None = None,
        invocation_arguments: Mapping[str, Any] | None = None,
        allow_model_stage: bool = True,
    ) -> tuple[str | None, tuple[str, ...]]:
        """Bounded evidence-bound synthesis for a non-mutating outcome.

        The model may only SELECT and ORGANIZE owner evidence — it
        proposes which records/fields matter (plus an optional closed
        presentation hint); there is no model-authored prose channel,
        so no model text can introduce a factual leaf value
        (§6.144/§6.145). Deterministic runtime copies values verbatim
        from the sanitized records and composes the natural answer.
        Empty selection is Stage 05 insufficiency (honest limitation),
        not a raw dump. Other failures demote to the deterministic
        renderer. Bounded transient context is forwarded to the
        selection proposal only — prior data is never replayed as
        current evidence. The outcome and its epistemic class are
        never altered.

        R4/R5: personal ticket scope and paginated count semantics are
        projected deterministically before any model synthesis so a
        page of N items is never framed as a personal or global total.
        """
        _emit_activity(
            phase=ActivityPhase.OUTCOME_PREPARING, correlation=correlation
        )
        paginated_projection = _project_paginated_personal_or_count(
            input_text,
            outcome.structured,
            invocation_arguments=invocation_arguments,
        )
        if paginated_projection is not None:
            _logger.info(
                "orchestration stage=synthesis "
                "decision=paginated_or_personal_scope "
                "correlation_id=%s",
                correlation,
            )
            return paginated_projection
        # I02: when owner evidence is guidance-shaped, prefer a
        # deterministic goal-aligned projection before spending model
        # budget — preserves prerequisites/steps/criteria under the
        # global 30s ceiling without inventing prose.
        owner_truncated = (
            LIMITATION_RESULT_TRUNCATED in outcome.limitations
        )
        guided = _deterministic_guidance_content(
            outcome.structured,
            owner_truncated=owner_truncated,
            field_labels=self._field_labels,
        )
        if guided is not None:
            body, guided_limitations = guided
            _logger.info(
                "orchestration stage=synthesis "
                "decision=deterministic_guidance "
                "correlation_id=%s",
                correlation,
            )
            return body, guided_limitations
        records = tuple(
            _sanitize_renderable(entity)
            for entity in _synthesis_records(
                outcome.structured, field_labels=self._field_labels
            )
        )
        if not records:
            return None, ()
        if len(records) == 1:
            # Token efficiency: a single record carrying exactly one
            # renderable leaf needs no selection proposal — the
            # deterministic composer answers directly.
            single = records[0]
            renderable = [
                (str(field), _redact_text(str(value).strip()))
                for field, value in single.items()
                if not isinstance(value, (Mapping, list, tuple))
                and value is not None
                and _redact_text(str(value).strip())
            ]
            if len(renderable) == 1:
                return (
                    _compose_answer(
                        single, renderable,
                        field_labels=self._field_labels,
                    )[
                        :MAX_RENDER_CONTENT_CHARS
                    ],
                    (),
                )
        block: dict[str, Any] = {"records": [dict(r) for r in records]}
        if business_subject is not None:
            # Bounded semantic subject from the validated turn goal —
            # untrusted selection context, never a factual value.
            block["business_subject"] = business_subject
        # Owner evidence already exists: if the remaining budget cannot
        # finish a synthesis stage, demote to deterministic render
        # instead of timing out the whole turn (Stage 05 30s ceiling).
        if deadline is not None and (
            deadline.remaining_seconds() < MIN_VIABLE_MODEL_STAGE_SECONDS * 3
        ):
            guided_budget = _deterministic_guidance_content(
                outcome.structured,
                owner_truncated=owner_truncated,
                field_labels=self._field_labels,
            )
            if guided_budget is not None:
                _logger.info(
                    "orchestration stage=synthesis "
                    "decision=skip_budget_deterministic "
                    "remaining_ms=%d correlation_id=%s",
                    int(deadline.remaining_seconds() * 1000),
                    correlation,
                )
                return guided_budget
            _logger.info(
                "orchestration stage=synthesis "
                "decision=skip_budget remaining_ms=%d "
                "correlation_id=%s",
                int(deadline.remaining_seconds() * 1000),
                correlation,
            )
            return None, ()
        if not allow_model_stage:
            # CRI composition already owns this response — the
            # deterministic projections above still contributed their
            # limitations, but no model stage may burn the frozen 30s
            # budget on a draft that would be discarded.
            _logger.info(
                "orchestration stage=synthesis "
                "decision=skip_cri_composed correlation_id=%s",
                correlation,
            )
            return None, ()
        try:
            proposal = self._propose(
                input_text,
                block_tag="records",
                block_payload=json.dumps(
                    block,
                    ensure_ascii=False,
                    default=str,
                )[:MAX_SURFACE_CHARS],
                instruction_id=SYNTHESIS_INSTRUCTION_ID,
                instruction=self._instruction(SYNTHESIS_INSTRUCTION_ID),
                expected_fields=("items",),
                input_kind="grounded_synthesis",
                allowed_keys=frozenset({"items", "presentation"}),
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded:
            _logger.info(
                "orchestration stage=synthesis "
                "decision=budget_fallback correlation_id=%s",
                correlation,
            )
            # Prefer goal-aligned guidance projection over a blind dump.
            guided_fallback = _deterministic_guidance_content(
                outcome.structured,
                owner_truncated=owner_truncated,
                field_labels=self._field_labels,
            )
            if guided_fallback is not None:
                return guided_fallback
            return None, ()
        # LOOP-03R2A (observability): the fallback carries one bounded
        # deterministic reason code — never proposal content.
        page_envelope = extract_pagination_envelope(outcome.structured)
        rendered, reason = (
            _render_synthesis(
                proposal,
                records,
                has_more=(
                    page_envelope.has_more
                    if page_envelope is not None
                    else None
                ),
                field_labels=self._field_labels,
            )
            if isinstance(proposal, Mapping)
            else (None, "proposal_absent")
        )
        if rendered is None:
            # Stage 05: only an explicit empty ``items`` array means
            # "cannot answer" — invalid indices/fields/unrenderable
            # leaves still demote to the deterministic owner render.
            explicit_empty = (
                isinstance(proposal, Mapping)
                and isinstance(proposal.get("items"), (list, tuple))
                and len(proposal.get("items")) == 0
            )
            if reason == "empty_selection" and explicit_empty:
                _logger.info(
                    "orchestration stage=synthesis "
                    "decision=insufficient_evidence "
                    "correlation_id=%s",
                    correlation,
                )
                return (
                    _insufficiency_content(),
                    (LIMITATION_INSUFFICIENT_EVIDENCE,),
                )
            _logger.info(
                "orchestration stage=synthesis decision=fallback "
                "reason=%s correlation_id=%s",
                reason,
                correlation,
            )
            return None, ()
        _logger.info(
            "orchestration stage=synthesis decision=synthesized "
            "correlation_id=%s",
            correlation,
        )
        return rendered, ()

    def _repair_once(
        self,
        input_text: str,
        group_key: str,
        arguments: Mapping[str, Any],
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline | None = None,
    ) -> tuple[SpecialistOutcome, str, str] | None:
        """One bounded pre-execution repair round (MAX_REPLAN_ROUNDS=1).

        Live surface changed under the initial selection: re-resolve the
        group fresh, reselect one capability semantically and rebuild
        its arguments once. Non-mutating targets only — PREPARE/ACT
        never reach this path, so no material write is ever retried.
        Any failure returns None and the original error stands.
        """
        try:
            fresh = self._fresh_group(group_key, correlation, deadline)
        except CapabilityProviderError:
            # The live re-list itself failed — fail closed on the
            # original error; exactly one repair attempt, no loop.
            _logger.info(
                "orchestration stage=repair decision=fail_closed "
                "reason=relist_failed correlation_id=%s",
                correlation,
            )
            return None
        if fresh is None:
            return None
        _repick_status, repick = self._select_capability(
            input_text,
            fresh,
            workspace_context,
            prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if repick is None or not invocable_in_interactive_phase(
            repick.operation_class
        ) or repick.operation_class in (
            SpecialistOperationClass.PREPARE,
            SpecialistOperationClass.ACT,
        ):
            return None
        new_args, missing = self._build_arguments(
            input_text,
            repick,
            workspace_context,
            correlation=correlation,
            prior_turns=prior_turns,
            deadline=deadline,
        )
        if new_args is None or missing:
            return None
        _logger.info(
            "orchestration stage=repair decision=reselected "
            "capability=%s correlation_id=%s",
            repick.remote_name,
            correlation,
        )
        try:
            return self._invoke_selected(
                group_key,
                repick.remote_name,
                new_args,
                fresh,
                input_text,
                correlation,
                prior_turns,
                deadline,
            )
        except CapabilityProviderError:
            return None

    def _recover_owner_contract(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        group_key: str,
        remote_name: str,
        group: CapabilityGroup,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        deadline: TurnDeadline | None = None,
    ) -> tuple[SpecialistOutcome, str, str] | None:
        """One bounded contextual-recovery round (C3).

        The owner rejected the proposed arguments as a remote
        contract/admissibility error — the flat ``inputSchema`` cannot
        express entity-conditional constraints, but the group's
        DISCOVERY capability already publishes the real owner
        vocabulary. Consult it once, re-propose arguments through the
        SAME argument stage under the bounded owner evidence, apply
        the SAME deterministic gates, and retry the invocation once.
        Non-mutating targets only by construction — PREPARE/ACT never
        reach this path. Any failure returns ``None`` and the original
        owner error stands: no loops, no second planner, no invented
        contract.
        """
        discovery_cap = _discovery_capability(group)
        if discovery_cap is None or (
            discovery_cap.remote_name == remote_name
        ):
            # No owner-vocabulary peer, or the rejected capability is
            # the discovery source itself — never self-recover.
            return None
        if deadline is not None and not self._budget_allows_resolver(
            deadline
        ):
            _logger.info(
                "orchestration stage=recovery "
                "decision=skipped_budget correlation_id=%s",
                correlation,
            )
            return None
        try:
            discovery_arguments, _ = self._build_arguments(
                input_text,
                discovery_cap,
                workspace_context,
                prior_turns=prior_turns,
                deadline=deadline,
            )
            if discovery_arguments is None:
                return None
            discovery_outcome = self._invoke(
                group,
                discovery_cap.remote_name,
                discovery_arguments,
                correlation,
                deadline,
            )
        except CapabilityProviderError:
            return None
        owner_evidence = _bound_owner_evidence(discovery_outcome)
        discovery_structured = (
            discovery_outcome.structured
            if isinstance(discovery_outcome.structured, Mapping)
            else None
        )
        new_args, missing = self._build_arguments(
            input_text,
            descriptor,
            workspace_context,
            owner_evidence=owner_evidence,
            prior_turns=prior_turns,
            deadline=deadline,
        )
        if new_args is None or missing:
            return None
        if _unproven_identifier_inputs(
            new_args,
            descriptor,
            input_text,
            workspace_context,
            owner_evidence,
        ):
            # The informed proposal still invents an identifier —
            # fail closed on the original owner error.
            return None
        new_args = _apply_entity_defaults_to_arguments(
            dict(new_args), discovery_structured
        )
        if _argument_completeness_gaps(
            new_args, descriptor, discovery_structured
        ):
            return None
        _logger.info(
            "orchestration stage=recovery decision=owner_contract "
            "capability=%s correlation_id=%s",
            remote_name,
            correlation,
        )
        try:
            return self._invoke_selected(
                group_key,
                remote_name,
                new_args,
                group,
                input_text,
                correlation,
                prior_turns,
                deadline,
            )
        except CapabilityProviderError:
            return None

    def _judge_goal_evidence(
        self,
        input_text: str,
        facts: EvidenceFacts,
        goal: _TurnGoal,
        *,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline | None,
    ) -> GoalEvidenceJudgment | None:
        """One bounded semantic-correspondence proposal.

        The model sees the stated goal subject/requirements and the
        sanitized owner records — it classifies correspondence; the
        deterministic parse decides. ``None`` means the proposal was
        absent or invalid: the caller must degrade honestly, never
        assume pertinence.
        """
        requirements = goal.answer_requirements
        block: dict[str, Any] = {
            "business_subject": goal.business_subject,
            "scope_constraints": dict(goal.scope_constraints),
            "records": list(facts.records)[:MAX_RELEVANCE_RECORDS],
        }
        if requirements is not None:
            declared = {
                "min_items": requirements.min_items,
                "ordering": requirements.ordering,
                "complete_coverage": requirements.complete_coverage,
            }
            block["declared_requirements"] = {
                key: value
                for key, value in declared.items()
                if value not in (None, False)
            }
        proposal = self._propose(
            input_text,
            block_tag="evidence",
            block_payload=json.dumps(
                block,
                ensure_ascii=False,
                default=str,
            )[:MAX_RELEVANCE_EVIDENCE_CHARS],
            instruction_id=GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
            instruction=self._instruction(
                GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID
            ),
            expected_fields=("correspondence",),
            input_kind="goal_evidence_relevance",
            allowed_keys=frozenset(
                {"correspondence", "mismatch_hint"}
            ),
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            _logger.info(
                "orchestration stage=goal_evidence_relevance "
                "decision=unavailable correlation_id=%s",
                correlation,
            )
            return None
        judgment = parse_goal_evidence_judgment(proposal)
        _logger.info(
            "orchestration stage=goal_evidence_relevance "
            "decision=%s correlation_id=%s",
            (
                judgment.correspondence
                if judgment is not None
                else "invalid"
            ),
            correlation,
        )
        return judgment

    def _recover_relevance(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        group_key: str,
        remote_name: str,
        group: CapabilityGroup,
        groups: Mapping[str, CapabilityGroup],
        facts: EvidenceFacts | None,
        prior_arguments: dict[str, Any] | None,
        judgment: GoalEvidenceJudgment,
        goal: _TurnGoal,
        *,
        owner_evidence: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline | None,
    ) -> tuple[SpecialistOutcome, str, str] | None:
        """One bounded semantic-recovery round (plan 125 adendum /
        doc 143 Trilha B).

        The judgment declared the returned evidence irrelevant to the
        stated goal. Within this single guarded round the planner may
        reconsider the READ strategy: re-propose arguments on the same
        capability, or — through the same governed selection stages —
        reselect a different live READ capability/group. Every gate
        re-validates: live surface membership, resumable class,
        argument validation, identifier provenance, budget. An
        identical query on the same capability is never re-executed;
        any failure returns ``None`` and the original outcome stands
        as insufficient — no loops, no amplification, no PREPARE/ACT.
        """
        if descriptor.operation_class not in (
            _RESUMABLE_OPERATION_CLASSES
        ):
            return None
        if deadline is not None and not self._budget_allows_resolver(
            deadline
        ):
            _logger.info(
                "orchestration stage=relevance_recovery "
                "decision=skipped_budget correlation_id=%s",
                correlation,
            )
            return None
        feedback = json.dumps(
            {
                "prior_correspondence": judgment.correspondence,
                "mismatch_hint": (judgment.mismatch_hint or "")[
                    :MAX_MISMATCH_HINT_CHARS
                ],
                "business_subject": goal.business_subject,
                "scope_constraints": dict(goal.scope_constraints),
                # Bounded preview of what the source actually
                # returned — untrusted owner data, never
                # instructions; lets the reformulation pivot on the
                # observed mismatch (e.g. nomenclature, qualifiers).
                "prior_result_preview": json.dumps(
                    list(facts.records)[:MAX_RELEVANCE_RECORDS]
                    if facts is not None
                    else [],
                    ensure_ascii=False,
                    default=str,
                )[:MAX_EVIDENCE_RECORD_CHARS],
            },
            ensure_ascii=False,
        )
        _RELEVANCE_RECOVERY_USED.set(True)
        # Governed reselection inside the one allowed round: the
        # planner may reconsider group and capability over the same
        # live surface; falling back to the original descriptor keeps
        # the same-capability reformulation path.
        sel_group_key, sel_group, sel_descriptor = (
            group_key,
            group,
            descriptor,
        )
        if len(groups) > 1 or len(group.capabilities) > 1:
            status, maybe_key = self._select_group(
                input_text,
                groups,
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
                relevance_feedback=feedback,
            )
            if status == "selected" and maybe_key in groups:
                sel_group_key = maybe_key
                sel_group = groups[maybe_key]
            status, candidate = self._select_capability(
                input_text,
                sel_group,
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
                relevance_feedback=feedback,
            )
            if status == "selected" and candidate is not None:
                sel_descriptor = candidate
        if sel_descriptor.operation_class not in (
            _RESUMABLE_OPERATION_CLASSES
        ):
            _logger.info(
                "orchestration stage=relevance_recovery "
                "decision=rejected_class capability=%s "
                "correlation_id=%s",
                sel_descriptor.remote_name,
                correlation,
            )
            return None
        # Bounded foreign composition inside the SAME recovery
        # round (LOOP-02R1 mechanics reused verbatim): the
        # correspondence judgment already proved the mismatch, so
        # the native-sufficiency assessment now decides on
        # confirmed divergence — never on speculation. A required
        # foreign consult resolves evidence (e.g. the owner
        # canonical designation) that is injected into the
        # reformulated arguments of the single re-invocation.
        # Selection/invocation failure degrades to plain
        # reformulation — recovery is best-effort, still bounded.
        foreign_evidence: str | None = None
        if len(groups) > 1:
            assessment = self._assess_native_path(
                input_text,
                sel_group,
                sel_descriptor,
                correlation,
                workspace_context,
                prior_turns,
                goal=goal,
                deadline=deadline,
                relevance_feedback=feedback,
            )
            if assessment == "foreign_evidence_required":
                found = self._select_foreign_capability(
                    input_text,
                    groups,
                    sel_group_key,
                    "enrichment",
                    correlation,
                    workspace_context,
                    prior_turns,
                    deadline,
                )
                if found is not None:
                    foreign_key, foreign_cap = found
                    foreign_result = self._invoke_foreign_evidence(
                        input_text,
                        foreign_key,
                        foreign_cap,
                        groups[foreign_key],
                        correlation,
                        workspace_context=workspace_context,
                        prior_turns=prior_turns,
                        deadline=deadline,
                        relevance_feedback=feedback,
                        goal=goal,
                    )
                    if foreign_result.evidence is not None:
                        foreign_evidence = foreign_result.evidence
        new_args, missing = self._build_arguments(
            input_text,
            sel_descriptor,
            workspace_context,
            owner_evidence=owner_evidence,
            foreign_evidence=foreign_evidence,
            relevance_feedback=feedback,
            business_subject=goal.business_subject,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if new_args is None or missing:
            return None
        if _unproven_identifier_inputs(
            new_args,
            sel_descriptor,
            input_text,
            workspace_context,
            owner_evidence,
        ):
            # The informed proposal still invents an identifier —
            # fail closed on the original insufficiency.
            return None
        same_capability = (
            sel_group_key == group_key
            and sel_descriptor.remote_name == remote_name
        )
        if same_capability and dict(prior_arguments or {}) == dict(
            new_args
        ):
            _logger.info(
                "orchestration stage=relevance_recovery "
                "decision=identical_arguments correlation_id=%s",
                correlation,
            )
            return None
        _logger.info(
            "orchestration stage=relevance_recovery "
            "decision=reinvoke capability=%s correlation_id=%s",
            sel_descriptor.remote_name,
            correlation,
        )
        try:
            return self._invoke_selected(
                sel_group_key,
                sel_descriptor.remote_name,
                new_args,
                sel_group,
                input_text,
                correlation,
                prior_turns,
                deadline,
            )
        except CapabilityProviderError:
            return None
        except (_TurnCancelled, _StageDeadlineExceeded):
            raise
        except Exception:
            # The recovery leg is best-effort: any provider-layer
            # failure inside the single bounded re-invocation leaves
            # the original insufficiency standing — never an
            # unhandled error at the turn boundary (plan 148 WP3).
            _logger.info(
                "orchestration stage=relevance_recovery "
                "decision=reinvoke_failed correlation_id=%s",
                correlation,
            )
            return None

    def _apply_semantic_relevance(
        self,
        input_text: str,
        outcome: SpecialistOutcome,
        cri_facts: EvidenceFacts | None,
        cri_verdict: OutcomeVerdict | None,
        descriptor: ProviderCapability,
        group_key: str,
        remote_used: str,
        action_id: str,
        group: CapabilityGroup,
        groups: Mapping[str, CapabilityGroup],
        arguments: dict[str, Any] | None,
        goal: _TurnGoal,
        owner_evidence: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline | None,
    ) -> tuple[
        SpecialistOutcome,
        str,
        str,
        EvidenceFacts | None,
        OutcomeVerdict | None,
    ]:
        """Semantic-relevance edge (plan 125 adendum).

        An ``answered`` verdict on business evidence is conclusive
        only after the bounded correspondence judgment:
        - ``corresponds`` -> the verdict stands;
        - ``irrelevant``  -> ONE governed READ recovery round (when
          not already used this interaction); a still-mismatched or
          absent recovery degrades to honest ``goal_mismatch``
          insufficiency;
        - ``uncertain``/absent/invalid proposal -> ``relevance_
          unproven`` insufficiency, never a confident fabrication.
        """
        unchanged = (
            outcome,
            remote_used,
            action_id,
            cri_facts,
            cri_verdict,
        )
        if (
            cri_verdict is None
            or cri_facts is None
            or cri_verdict.decision != OUTCOME_ANSWERED
            or not cri_facts.has_business_evidence
        ):
            return unchanged
        judgment = self._judge_goal_evidence(
            input_text,
            cri_facts,
            goal,
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if (
            judgment is not None
            and judgment.correspondence == GOAL_EVIDENCE_IRRELEVANT
            and not _RELEVANCE_RECOVERY_USED.get()
        ):
            recovered = self._recover_relevance(
                input_text,
                descriptor,
                group_key,
                remote_used,
                group,
                groups,
                cri_facts,
                arguments,
                judgment,
                goal,
                owner_evidence=owner_evidence,
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
            if recovered is not None:
                outcome, action_id, remote_used = recovered
                cri_facts = outcome_facts(
                    outcome,
                    descriptor.operation_class,
                    record_resolver=(
                        lambda structured: _synthesis_records(
                            structured,
                            field_labels=self._field_labels,
                        )
                    ),
                )
                cri_verdict = assess_outcome(
                    cri_facts,
                    goal.answer_requirements,
                    contract_subject=goal.contract_subject,
                )
                if (
                    cri_verdict.decision == OUTCOME_ANSWERED
                    and cri_facts.has_business_evidence
                ):
                    judgment = self._judge_goal_evidence(
                        input_text,
                        cri_facts,
                        goal,
                        workspace_context=workspace_context,
                        prior_turns=prior_turns,
                        correlation=correlation,
                        deadline=deadline,
                    )
                else:
                    judgment = None
        if cri_verdict is None or cri_facts is None:
            return (
                outcome,
                remote_used,
                action_id,
                cri_facts,
                cri_verdict,
            )
        if cri_verdict.decision != OUTCOME_ANSWERED:
            return (
                outcome,
                remote_used,
                action_id,
                cri_facts,
                cri_verdict,
            )
        if judgment is None or (
            judgment.correspondence != GOAL_EVIDENCE_CORRESPONDS
        ):
            cri_verdict = OutcomeVerdict(
                OUTCOME_INSUFFICIENT,
                (
                    (REASON_GOAL_MISMATCH,)
                    if (
                        judgment is not None
                        and judgment.correspondence
                        == GOAL_EVIDENCE_IRRELEVANT
                    )
                    else (REASON_RELEVANCE_UNPROVEN,)
                ),
            )
        return (
            outcome,
            remote_used,
            action_id,
            cri_facts,
            cri_verdict,
        )

    def _admit_conversational_turn(
        self,
        input_text: str,
        *,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> tuple[str | None, bool]:
        """Cheap typed admission: non-operational turns skip selection.

        Returns ``(interaction_class, owner_required)``: the admitted
        class ("conversation", "explanation", "hypothetical" or
        "surface_inquiry") only when the model declares
        requires_owner_surface=false. ``owner_required`` is True when
        the proposal proceeded to the governed owner path (requires
        true, or operational/ambiguous class); False when admission
        never ran (budget skip, timeout, invalid proposal) or admitted
        a conversational class. Ambiguous/failed admission returns
        ``(None, False)`` and falls through to selection with the
        conversational fallback preserved (never invents business
        facts by skipping owners). "surface_inquiry" answers from the
        deterministic live-surface projection — still no owner
        invocation, but the live listing IS consulted.
        """
        # Q02-A: prior turns no longer skip admission — the model must
        # classify topic change vs operational continuity explicitly.
        remaining = deadline.remaining_seconds()
        if remaining < (
            MIN_VIABLE_MODEL_STAGE_SECONDS
            + CONVERSATIONAL_FALLBACK_RESERVE_SECONDS
        ):
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=budget_skip remaining_ms=%d "
                "correlation_id=%s",
                int(remaining * 1000),
                correlation,
            )
            return None, False
        try:
            proposal = self._propose(
                input_text,
                block_tag="admission",
                block_payload=(
                    '{"owner_surfaces":"live governed owner '
                    'surfaces exist; their catalog is listed '
                    'only after admission - decide whether '
                    'the request requires governed owner '
                    'data or can be answered '
                    'conversationally"}'
                ),
                instruction_id=INTERACTION_ADMISSION_INSTRUCTION_ID,
                instruction=self._instruction(INTERACTION_ADMISSION_INSTRUCTION_ID),
                expected_fields=(
                    "requires_owner_surface",
                    "interaction_class",
                ),
                input_kind="interaction_admission",
                allowed_keys=frozenset(
                    {
                        "requires_owner_surface",
                        "interaction_class",
                        "limitations",
                    }
                ),
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded:
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=budget_exhausted correlation_id=%s",
                correlation,
            )
            return None, False
        if proposal is None:
            return None, False
        raw_req = proposal.get("requires_owner_surface")
        if isinstance(raw_req, str):
            requires = raw_req.strip().lower() == "true"
        elif raw_req is True:
            requires = True
        elif raw_req is False:
            requires = False
        else:
            return None, False
        raw_class = proposal.get("interaction_class")
        if not isinstance(raw_class, str):
            return None, False
        interaction_class = raw_class.strip().lower()
        if interaction_class not in {
            "conversation",
            "explanation",
            "hypothetical",
            "operational",
            "surface_inquiry",
            "ambiguous",
        }:
            return None, False
        if interaction_class == "surface_inquiry":
            # The typed class is the semantic statement: a surface
            # inquiry is answered by the deterministic live-surface
            # projection — bounded, read-only, never an invocation. A
            # contradictory requires_owner_surface flag in the same
            # proposal is output noise and never vetoes the listing;
            # it only vetoes free-form classes (below), where skipping
            # the owner path could suppress real data.
            return interaction_class, True
        if requires or interaction_class in {"operational", "ambiguous"}:
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=owner_surface class=%s correlation_id=%s",
                interaction_class,
                correlation,
            )
            return None, True
        return interaction_class, False

    def _surface_inquiry_attempt(
        self,
        groups: Mapping[str, CapabilityGroup],
        failures: list[str],
        correlation: str,
    ) -> GovernedCapabilityAttempt:
        """Deterministic surface answer: the live listing projected
        verbatim — surface metadata observed this turn, never an
        invocation result and never an authorization claim."""
        content = _surface_inquiry_content(groups, failures)
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id=correlation,
            admission_outcome=SURFACE_INQUIRY_ADMISSION,
            content=content,
            limitations=(LIMITATION_CAPABILITY_SURFACE_LISTING,),
            markdown_content=content,
        )

    def _select_group(
        self,
        input_text: str,
        groups: Mapping[str, CapabilityGroup],
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
        relevance_feedback: str | None = None,
    ) -> tuple[str, str | None]:
        """Stage 1: pick the capability group whose surface matches.

        Returns ``(status, group_key)`` where status is:
        - ``selected`` — live group key
        - ``not_applicable`` — no owner surface required (conversational)
        - ``invalid`` — model claimed applicable with a non-live group
        """
        eligible = sorted(groups)
        if not eligible:
            return ("not_applicable", None)
        # Q02-A S20 / one-rework RQ-03: singleton membership is never
        # semantic relevance. Always require a validated model proposal.
        # Missing/timeout proposals fail closed to not_applicable —
        # including when only one live group exists — so unproven
        # relevance cannot start an operational owner invoke.
        observation = _prior_observation_context(prior_turns)
        group_payload = _group_summaries(
            groups, prior_observation=observation
        )
        if relevance_feedback is not None:
            # Bounded semantic-mismatch signal from a validated
            # goal/evidence judgment — untrusted data, never an
            # instruction: it informs the single governed recovery
            # reselection round only (plan 125 adendum / doc 143-B).
            group_payload = json.dumps(
                {
                    "capability_groups": json.loads(group_payload),
                    "relevance_feedback": json.loads(relevance_feedback),
                },
                ensure_ascii=False,
            )
        proposal = self._propose(
            input_text,
            block_tag="capability_groups",
            block_payload=group_payload,
            instruction_id=GROUP_SELECTION_INSTRUCTION_ID,
            instruction=self._instruction(GROUP_SELECTION_INSTRUCTION_ID),
            expected_fields=("applicable", "capability_group_id"),
            input_kind="capability_group_selection",
            allowed_keys=frozenset(
                {"applicable", "capability_group_id", "limitations"}
            ),
            workspace_context=workspace_context,
            # Full prior transcript stays out of group selection (latency);
            # the bounded prior_observation above is untrusted context.
            prior_turns=(),
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return ("not_applicable", None)
        applicable = proposal.get("applicable")
        if isinstance(applicable, str):
            applicable = applicable.strip().lower() == "true"
        if applicable is not True:
            return ("not_applicable", None)
        group_key = proposal.get("capability_group_id")
        if not isinstance(group_key, str):
            return ("invalid", None)
        group_key = group_key.strip()
        # Revalidate against the fresh groups — an invented or
        # removed group is never selectable. Accept an unambiguous
        # bare group_id only when it maps to exactly one live key
        # (membership, not lexical ranking).
        resolved = _resolve_live_group_key(group_key, groups)
        if resolved is None:
            return ("invalid", None)
        return ("selected", resolved)

    @staticmethod
    def _capability_from_selection_proposal(
        proposal: Mapping[str, Any] | None,
        invocable: Sequence[ProviderCapability],
    ) -> tuple[str, ProviderCapability | None]:
        """Deterministic revalidation of a capability selection proposal.

        Returns ``(status, capability)``:
        - ``selected`` — live capability
        - ``not_applicable`` — model said no capability is required
        - ``inconclusive`` — applicable claimed but remote missing/invalid
        """
        if proposal is None:
            return ("inconclusive", None)
        raw_applicable = proposal.get("applicable")
        if isinstance(raw_applicable, str):
            normalized = raw_applicable.strip().lower()
            if normalized == "true":
                applicable: bool | None = True
            elif normalized in {"false", "null", "none", ""}:
                applicable = False
            else:
                # Garbage tokens like "yes" are not a valid applicable
                # declaration — inconclusive, never conversational.
                return ("inconclusive", None)
        elif raw_applicable is True:
            applicable = True
        elif raw_applicable is False or raw_applicable is None:
            applicable = False
        else:
            return ("inconclusive", None)
        if applicable is not True:
            return ("not_applicable", None)
        remote_name = proposal.get("remote_name")
        if not isinstance(remote_name, str):
            return ("inconclusive", None)
        remote_name = remote_name.strip()
        match = next(
            (
                cap
                for cap in invocable
                if cap.remote_name == remote_name
            ),
            None,
        )
        if match is None:
            return ("inconclusive", None)
        return ("selected", match)

    def _select_capability(
        self,
        input_text: str,
        group: CapabilityGroup,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
        relevance_feedback: str | None = None,
    ) -> tuple[str, ProviderCapability | None]:
        """Stage 2: pick a capability from that group's surface."""
        invocable = [
            cap
            for cap in group.capabilities
            if invocable_in_interactive_phase(cap.operation_class)
        ]
        if not invocable:
            return ("inconclusive", None)
        # Q02-C keeps this short-circuit: exactly one READ whose published
        # schema enum includes action=tickets, and only when the existing
        # pagination intent already applies. It is not a continuity or
        # compare classifier and does not branch on provider name.
        # Removing it would add a model stage on the path that exhausted
        # the 30s budget before owner READ.
        structural = unique_structural_ticket_list_capability(
            invocable, input_text
        )
        if structural is not None:
            _logger.info(
                "orchestration stage=select_capability "
                "decision=structural_ticket_list capability=%s "
                "correlation_id=%s",
                structural.remote_name,
                correlation,
            )
            return ("selected", structural)
        # Note: a singleton invocable surface is NOT automatic FAST —
        # applicability to the user ask still requires a validated
        # proposal (applicable may be false).
        observation = _prior_observation_context(prior_turns)
        cap_payload = _capability_payload(
            group, prior_observation=observation
        )
        if relevance_feedback is not None:
            # Same bounded recovery signal as stage 1 — untrusted data.
            cap_payload = json.dumps(
                {
                    "capabilities": json.loads(cap_payload),
                    "relevance_feedback": json.loads(relevance_feedback),
                },
                ensure_ascii=False,
            )
        proposal = self._propose(
            input_text,
            block_tag="capabilities",
            block_payload=cap_payload,
            instruction_id=CAPABILITY_SELECTION_INSTRUCTION_ID,
            instruction=self._instruction(CAPABILITY_SELECTION_INSTRUCTION_ID),
            expected_fields=("applicable", "remote_name"),
            input_kind="capability_selection",
            allowed_keys=frozenset(
                {"applicable", "remote_name", "limitations"}
            ),
            workspace_context=workspace_context,
            # Full prior transcript stays out of selection (latency);
            # prior_observation in the catalog payload is untrusted context.
            prior_turns=(),
            correlation=correlation,
            deadline=deadline,
        )
        return self._capability_from_selection_proposal(
            proposal, invocable
        )

    def _select_capability_with_goal(
        self,
        input_text: str,
        group: CapabilityGroup,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
    ) -> tuple[
        str,
        ProviderCapability | None,
        "OperationalCapabilityOrchestrator._TurnGoal | None",
    ]:
        """I02-R3B: one typed proposal for capability + optional goal.

        Reuses ``select_capability`` purpose id. Capability fields remain
        required; when ``goal_class`` is present it is validated with the
        same rules as ``_understand_goal``. Missing goal fields return
        ``(capability, None)`` so the caller may issue a dedicated
        turn_goal proposal (legacy fixtures / incomplete models).
        """
        invocable = [
            cap
            for cap in group.capabilities
            if invocable_in_interactive_phase(cap.operation_class)
        ]
        if not invocable:
            return ("inconclusive", None, None)
        structural = unique_structural_ticket_list_capability(
            invocable, input_text
        )
        if structural is not None:
            _logger.info(
                "orchestration stage=select_capability "
                "decision=structural_ticket_list_with_goal "
                "capability=%s correlation_id=%s",
                structural.remote_name,
                correlation,
            )
            return (
                "selected",
                structural,
                self._TurnGoal(goal_class="read", declared=True),
            )
        observation = _prior_observation_context(prior_turns)
        allowed = frozenset(
            {"applicable", "remote_name", "limitations"}
        ) | self._GOAL_ALLOWED_KEYS
        proposal = self._propose(
            input_text,
            block_tag="capabilities",
            block_payload=_capability_payload(
                group, prior_observation=observation
            ),
            instruction_id=CAPABILITY_SELECTION_INSTRUCTION_ID,
            instruction=self._capability_goal_instruction,
            instruction_version=self._cri_instruction_version,
            expected_fields=("applicable", "remote_name"),
            input_kind="capability_selection_with_goal",
            allowed_keys=allowed,
            workspace_context=workspace_context,
            # Goal fields that need prior evidence may inspect turns;
            # capability revalidation stays against the live surface.
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        cap_status, descriptor = self._capability_from_selection_proposal(
            proposal, invocable
        )
        if cap_status != "selected" or descriptor is None:
            return (cap_status, None, None)
        selected_goal = self._turn_goal_from_proposal(
            proposal,
            prior_turns,
            correlation=correlation,
            require_goal_class=False,
        )
        return (cap_status, descriptor, selected_goal)

    def _propose_index_probe(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> bool:
        """Model proposes whether to run an empty index invoke first.

        Deterministic gates already constrained eligibility; this only
        accepts an explicit ``probe_index: true``. Missing/malformed
        proposals fail closed to no probe (never invent a catalog call).
        """
        block = {
            "remote_name": descriptor.remote_name,
            "operation_class": descriptor.operation_class.value,
            "description": (descriptor.description or "")[
                :MAX_DESCRIPTION_CHARS
            ],
            "input_schema": descriptor.input_schema,
        }
        proposal = self._propose(
            input_text,
            block_tag="capability",
            block_payload=json.dumps(
                block, ensure_ascii=False, default=str
            )[:MAX_ARGUMENTS_BLOCK_CHARS],
            instruction_id=INDEX_PROBE_INSTRUCTION_ID,
            instruction=self._instruction(INDEX_PROBE_INSTRUCTION_ID),
            expected_fields=("probe_index",),
            input_kind="capability_index_probe",
            allowed_keys=frozenset({"probe_index"}),
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return False
        return proposal.get("probe_index") is True

    def _bind_arguments_from_index(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        index_structured: Mapping[str, Any],
        declared_identifiers: frozenset[str],
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> dict[str, Any] | None:
        """Select an exact owner index id and project it into schema.

        Fail closed on missing/ambiguous/invented selections — never
        default to the first catalog entry.
        """
        field_keys = _optional_unconstrained_string_keys(descriptor)
        if not field_keys or not declared_identifiers:
            return None
        options = _index_option_rows(index_structured, field_keys)
        if not options:
            return None
        selected, argument_field = self._propose_index_identifier(
            input_text,
            options,
            field_keys,
            workspace_context,
            prior_turns,
            correlation,
            deadline,
        )
        if selected is None or argument_field is None:
            _logger.info(
                "orchestration stage=index_select "
                "decision=no_match correlation_id=%s",
                correlation,
            )
            return None
        if not _index_selection_is_member(selected, options):
            _logger.info(
                "orchestration stage=index_select "
                "decision=reject_non_member topic=%s "
                "correlation_id=%s",
                selected[:80],
                correlation,
            )
            return None
        projected = _project_selected_index_identifier(
            descriptor,
            selected,
            argument_field,
            declared_identifiers,
        )
        if projected is None:
            _logger.info(
                "orchestration stage=index_select "
                "decision=reject_unproven correlation_id=%s",
                correlation,
            )
            return None
        _logger.info(
            "orchestration stage=index_select decision=bound "
            "field=%s topic=%s correlation_id=%s",
            argument_field,
            selected[:80],
            correlation,
        )
        return projected

    def _propose_index_identifier(
        self,
        input_text: str,
        options: tuple[Mapping[str, str], ...],
        field_keys: tuple[str, ...],
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> tuple[str | None, str | None]:
        """Model selects one exact owner-declared index identifier."""
        block = {
            "owner_index_options": [
                {
                    "identifier": row["identifier"],
                    "label": row.get("label") or "",
                    "hints": row.get("hints") or "",
                }
                for row in options[:MAX_INDEX_OPTION_ENTRIES]
            ],
            "argument_fields": list(field_keys),
        }
        try:
            proposal = self._propose(
                input_text,
                block_tag="owner_index",
                block_payload=json.dumps(
                    block, ensure_ascii=False, default=str
                )[:MAX_ARGUMENTS_BLOCK_CHARS],
                instruction_id=INDEX_SELECT_INSTRUCTION_ID,
                instruction=self._instruction(INDEX_SELECT_INSTRUCTION_ID),
                expected_fields=("selected_identifier", "argument_field"),
                input_kind="capability_index_select",
                allowed_keys=frozenset(
                    {"selected_identifier", "argument_field", "limitations"}
                ),
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded:
            # INDEX already ran: a late select timeout must degrade to
            # no_match → clarification (deterministic ask-back exists),
            # not collapse the whole turn into PROCESSING_TIMEOUT.
            _logger.info(
                "orchestration stage=index_select "
                "decision=budget_skip remaining_ms=%d "
                "correlation_id=%s",
                int(deadline.remaining_seconds() * 1000),
                correlation,
            )
            return None, None
        if proposal is None:
            return None, None
        selected = proposal.get("selected_identifier")
        field = proposal.get("argument_field")
        if selected is None or field is None:
            return None, None
        if not isinstance(selected, str) or not isinstance(field, str):
            return None, None
        selected = selected.strip()
        field = field.strip()
        if not selected or not field:
            return None, None
        return selected, field

    def _build_arguments(
        self,
        input_text: str,
        descriptor: ProviderCapability,
        workspace_context: WorkspaceContext | None = None,
        owner_evidence: str | None = None,
        foreign_evidence: str | None = None,
        business_subject: str | None = None,
        relevance_feedback: str | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
    ) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
        """Stage 3: project intent into the live owner inputSchema.

        Returns ``(arguments, missing_inputs)``. The model sees the
        real schema (untrusted data) — plus bounded owner DISCOVERY
        evidence when the envelope required it — and proposes an
        "arguments" object; deterministic schema validation decides.
        ``missing_inputs`` carries owner-required inputs the turn
        cannot satisfy (clarification signal — the model declares
        them, deterministic bounding renders them). Orchestration-
        resolved fields are never model-supplied.
        """
        # Candidate-bound executors declare an ``arguments`` object
        # holding the inner action's payload — the model proposes it
        # like any other field; the candidate's own schema revalidates
        # it after the owner discovery flow.
        keys, required = _schema_keys(descriptor)
        if not (keys - ORCHESTRATED_FIELDS) and not (
            required - ORCHESTRATED_FIELDS
        ):
            return {}, ()
        deterministic = _deterministic_arguments_from_schema(descriptor)
        if deterministic is not None:
            _logger.info(
                "orchestration stage=arguments "
                "decision=deterministic_schema keys=%d "
                "correlation_id=%s",
                len(deterministic),
                correlation,
            )
            return deterministic, ()
        block: dict[str, Any] = {
            "capability": descriptor.remote_name,
            "description": (descriptor.description or "")[
                :MAX_DESCRIPTION_CHARS
            ],
            "input_schema": descriptor.input_schema,
        }
        evidence_blocks: dict[str, str] = {}
        if owner_evidence is not None:
            block["owner_vocabulary"] = owner_evidence
            evidence_blocks["owner_vocabulary"] = owner_evidence
        if foreign_evidence is not None:
            block["foreign_evidence"] = foreign_evidence
            evidence_blocks["foreign_evidence"] = foreign_evidence
        if business_subject is not None:
            # Bounded semantic subject from the validated turn goal —
            # keeps query-type arguments anchored on the business
            # concept, not on host/context stopwords (LOOP-03R1 D03).
            block["business_subject"] = business_subject
        if relevance_feedback is not None:
            # Bounded semantic-mismatch signal from a validated
            # goal/evidence judgment — untrusted data, never an
            # instruction: it only re-informs this argument stage
            # during the single governed recovery round (plan 125
            # adendum).
            block["relevance_feedback"] = relevance_feedback
        try:
            proposal = self._propose(
                input_text,
                block_tag="schema",
                block_payload=json.dumps(
                    block,
                    ensure_ascii=False,
                    default=str,
                )[:MAX_ARGUMENTS_BLOCK_CHARS],
                instruction_id=ARGUMENTS_INSTRUCTION_ID,
                instruction=self._instruction(ARGUMENTS_INSTRUCTION_ID),
                expected_fields=("arguments",),
                input_kind="capability_arguments",
                allowed_keys=frozenset(
                    {
                        "arguments",
                        "missing_inputs",
                        "limitations",
                        "selections",
                        "evidence_arguments",
                    }
                ),
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        except _StageDeadlineExceeded as exc:
            # model_timeout on arguments remains terminal (LOOP-03R2A).
            # Only turn_budget_exhausted after selection may project a
            # sole free-text field or clarify without inventing ids.
            if exc.reason != "turn_budget_exhausted":
                raise
            projected = _single_free_text_argument_from_input(
                input_text, descriptor
            )
            if projected is not None:
                _logger.info(
                    "orchestration stage=arguments "
                    "decision=budget_input_projection keys=%d "
                    "correlation_id=%s",
                    len(projected),
                    correlation,
                )
                return projected, ()
            missing = tuple(
                dict.fromkeys(
                    list(required - ORCHESTRATED_FIELDS)
                    + list(keys - ORCHESTRATED_FIELDS)
                )
            )[:MAX_MISSING_INPUTS]
            _logger.info(
                "orchestration stage=arguments "
                "decision=budget_skip remaining_ms=%d "
                "correlation_id=%s",
                int(
                    (deadline.remaining_seconds() * 1000)
                    if deadline is not None
                    else 0
                ),
                correlation,
            )
            return None, missing
        if proposal is None:
            return None, ()
        missing = _missing_inputs(proposal.get("missing_inputs"))
        normalized = normalize_arguments(proposal.get("arguments"))
        if normalized is None:
            return None, missing
        normalized = dict(normalized)
        normalized, sel_applied, sel_rejected, sel_unbound = (
            apply_evidence_bound_selections(
                proposal.get("selections"),
                normalized,
                evidence_blocks,
                descriptor.input_schema,
                declared=proposal.get("evidence_arguments"),
            )
        )
        if sel_applied or sel_rejected or sel_unbound:
            _logger.info(
                "orchestration stage=arguments "
                "decision=evidence_bound applied=%d rejected=%d "
                "unbound=%s correlation_id=%s",
                sel_applied,
                sel_rejected,
                ",".join(sel_unbound) or "-",
                correlation,
            )
        if sel_unbound:
            # Declared documental origin could not be verified —
            # running the proposal without that value would be an
            # unfiltered or under-filtered call the model itself
            # flagged as evidence-dependent. Route the field names
            # through missing_inputs so the bounded resolver/clarify
            # path answers honestly (doc 147 / review F1).
            missing = tuple(
                dict.fromkeys(list(missing) + list(sel_unbound))
            )[:MAX_MISSING_INPUTS]
            return None, missing
        validated = _validate_instance(normalized, descriptor.input_schema)
        if validated is None:
            return None, missing
        if missing and not validated:
            # The model declared owner-required inputs absent and
            # produced no arguments — clarify via the wording stage /
            # deterministic ask-back. Do not heuristically invent
            # query/limit values from free-text (doc 49 REWORK).
            return None, missing
        return validated, ()

    def _invoke_selected(
        self,
        group_key: str,
        remote_name: str,
        arguments: dict[str, Any],
        group: CapabilityGroup,
        input_text: str,
        correlation: str,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        deadline: TurnDeadline | None = None,
        goal: _TurnGoal | None = None,
    ) -> tuple[SpecialistOutcome, str, str] | None:
        """Invoke honoring the owner's flow shape.

        Returns (outcome, action_id, remote_name_used), or None when the
        owner produced no resolvable candidate for the intent (truthful
        NOT_APPLICABLE — post-consultation, never a failure disclosure).
        Candidate-bound capabilities (owner schema requiring
        candidate_token) always go through the specialist's owner
        discovery flow first; a DISCOVERY result carrying exactly one
        candidate chains into the specialist's candidate-bound READ
        when one is advertised.
        """
        capabilities = {
            cap.remote_name: cap for cap in group.capabilities
        }
        selected = capabilities[remote_name]

        if _is_candidate_bound(selected):
            found = self._discover_candidate(
                group, input_text, correlation, deadline, prior_turns
            )
            if found is None:
                return None
            candidate, discovery_outcome = found
            if candidate is None:
                terminal = self._unusable_candidate_terminal(
                    discovery_outcome,
                    capabilities.get(
                        discovery_outcome.provenance.remote_name
                    )
                    if discovery_outcome is not None
                    else None,
                    None,
                    goal,
                    correlation,
                )
                return (
                    (terminal, remote_name, remote_name)
                    if terminal is not None
                    else None
                )
            inner = arguments.get("arguments")
            merged = self._candidate_arguments(
                candidate,
                inner if isinstance(inner, Mapping) else {},
                input_text,
                prior_turns,
                correlation=correlation,
                deadline=deadline,
                business_subject=(
                    goal.business_subject if goal is not None else None
                ),
            )
            if merged is None:
                terminal = self._unusable_candidate_terminal(
                    discovery_outcome,
                    capabilities.get(
                        discovery_outcome.provenance.remote_name
                    )
                    if discovery_outcome is not None
                    else None,
                    candidate,
                    goal,
                    correlation,
                )
                return (
                    (terminal, remote_name, remote_name)
                    if terminal is not None
                    else None
                )
            outcome = self._invoke(
                group,
                remote_name,
                {
                    CANDIDATE_TOKEN_FIELD: candidate[CANDIDATE_TOKEN_FIELD],
                    "arguments": merged,
                },
                correlation,
                deadline,
            )
            return (
                outcome,
                str(candidate.get("action_id") or remote_name),
                remote_name,
            )

        outcome = self._invoke(
            group, remote_name, arguments, correlation, deadline
        )
        if selected.operation_class.value == "DISCOVERY":
            # Owner discovery may return candidate(s) for a
            # candidate-bound READ on the same specialist — chain when
            # the owner contracts it.
            candidate = self._resolve_candidate(
                outcome.structured,
                input_text,
                prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
            if candidate is None and not self._candidates_present(
                outcome.structured
            ):
                folded = _context_folded_discovery_query(
                    input_text, prior_turns
                )
                if folded is not None:
                    _logger.info(
                        "orchestration stage=discovery_retry "
                        "decision=context_folded correlation_id=%s",
                        correlation,
                    )
                    retry = self._invoke(
                        group,
                        remote_name,
                        {"query": folded},
                        correlation,
                        deadline,
                    )
                    candidate = self._resolve_candidate(
                        retry.structured,
                        input_text,
                        prior_turns,
                        correlation=correlation,
                        deadline=deadline,
                    )
            executors = [
                cap
                for cap in group.capabilities
                if cap.operation_class.value == "READ"
                and _is_candidate_bound(cap)
            ]
            if candidate is not None and len(executors) == 1:
                merged = self._candidate_arguments(
                    candidate,
                    arguments,
                    input_text,
                    prior_turns,
                    correlation=correlation,
                    deadline=deadline,
                    business_subject=(
                        goal.business_subject
                        if goal is not None
                        else None
                    ),
                )
                if merged is not None:
                    chained = self._invoke(
                        group,
                        executors[0].remote_name,
                        {
                            CANDIDATE_TOKEN_FIELD: candidate[
                                CANDIDATE_TOKEN_FIELD
                            ],
                            "arguments": merged,
                        },
                        correlation,
                        deadline,
                    )
                    return (
                        chained,
                        str(
                            candidate.get("action_id")
                            or executors[0].remote_name
                        ),
                        executors[0].remote_name,
                    )
            # Discovery did not resolve to a usable business result —
            # never render a bare "Discovery completed." as if it were
            # the answer. Zero candidates is a search result, not proof
            # that the owner catalog is empty — distinguish miss vs
            # absence using owner-declared eligible counts + live
            # tools/list surface. Control-plane envelopes
            # (capability_surface / agent_directives / telemetry)
            # stay out of user-facing content.
            if self._candidates_present(outcome.structured):
                terminal = self._unusable_candidate_terminal(
                    outcome, selected, candidate, goal, correlation
                )
                return (
                    (terminal, remote_name, remote_name)
                    if terminal is not None
                    else None
                )
            # S2 (RQ-SA04 / D5): the DISCOVERY payload may itself
            # publish the answer — owner-authored catalog/guidance
            # sections (display formats, a guide index). Project them
            # deterministically; declare the search miss only when
            # nothing projectable remains in the envelope.
            content = None
            guidance = _deterministic_guidance_content(
                outcome.structured, field_labels=self._field_labels
            )
            if guidance is not None:
                content, _guidance_omitted = guidance
            if not content:
                content = _render_zero_candidate_discovery(
                    outcome.structured
                    if isinstance(outcome.structured, Mapping)
                    else None,
                    group,
                )
            _logger.info(
                "orchestration stage=discovery_terminal "
                "decision=%s eligible=%s correlation_id=%s",
                _discovery_empty_result_class(
                    outcome.structured
                    if isinstance(outcome.structured, Mapping)
                    else None
                ),
                _owner_eligible_action_count(
                    outcome.structured
                    if isinstance(outcome.structured, Mapping)
                    else None
                ),
                correlation,
            )
            truthful = dataclasses.replace(
                outcome,
                content_text=content,
                structured=None,
                contract_facts=_contract_fact_rows(outcome),
                projected_content=(
                    content if guidance is not None else None
                ),
            )
            return truthful, remote_name, remote_name
        return outcome, remote_name, remote_name

    def _discover_candidate(
        self,
        group: CapabilityGroup,
        input_text: str,
        correlation: str,
        deadline: TurnDeadline | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
    ) -> tuple[Mapping[str, Any] | None, SpecialistOutcome | None] | None:
        """Owner discovery flow: exactly one DISCOVERY capability must
        exist for the candidate-bound READ to be resolvable. On a
        zero-candidate miss with prior context, one bounded retry uses
        the context-folded query (referential follow-ups carry no
        concrete identifier on their own). Returns the resolved
        candidate (or None) plus the discovery envelope outcome, so a
        non-executable result can still project its bounded contract
        terminal."""
        discovery_caps = [
            cap
            for cap in group.capabilities
            if cap.operation_class.value == "DISCOVERY"
        ]
        if len(discovery_caps) != 1:
            return None
        outcome = self._invoke(
            group,
            discovery_caps[0].remote_name,
            {"query": input_text[:MAX_DISCOVERY_QUERY_CHARS]},
            correlation,
            deadline,
        )
        candidate = self._resolve_candidate(
            outcome.structured,
            input_text,
            (),
            correlation=correlation,
            deadline=deadline,
        )
        if candidate is not None:
            return candidate, outcome
        if self._candidates_present(outcome.structured):
            return None, outcome
        folded = _context_folded_discovery_query(input_text, prior_turns)
        if folded is None:
            return None, outcome
        _logger.info(
            "orchestration stage=discovery_retry "
            "decision=context_folded correlation_id=%s",
            correlation,
        )
        retry = self._invoke(
            group,
            discovery_caps[0].remote_name,
            {"query": folded},
            correlation,
            deadline,
        )
        return (
            self._resolve_candidate(
                retry.structured,
                input_text,
                (),
                correlation=correlation,
                deadline=deadline,
            ),
            retry,
        )

    def _unusable_candidate_terminal(
        self,
        outcome: SpecialistOutcome | None,
        capability: ProviderCapability | None,
        resolved_candidate: Mapping[str, Any] | None,
        goal: "_TurnGoal | None",
        correlation: str,
    ) -> SpecialistOutcome | None:
        """Bounded contract terminal for a discovery that returned
        candidates none of which could execute under the declared
        arguments. Legitimate only when the model-declared contract
        subject provably bonds a specific candidate's published
        identity or the selected capability's surface — otherwise
        honest silence (``None``), never schema presented as a false
        answer."""
        if outcome is None or not self._candidates_present(
            outcome.structured
        ):
            return None
        bond = _contract_subject_bond(
            contract_subject=bool(
                getattr(goal, "contract_subject", False)
            ),
            business_subject=getattr(goal, "business_subject", None),
            capability=capability,
            resolved_candidate=resolved_candidate,
            structured=(
                outcome.structured
                if isinstance(outcome.structured, Mapping)
                else None
            ),
        )
        if bond is None:
            return None
        tier, bonded_candidate = bond
        if tier == "candidate":
            facts = _candidate_contract_rows(bonded_candidate)
            action_label = (
                bonded_candidate.get("action_id")
                or bonded_candidate.get("name")
                or bonded_candidate.get("entity")
            )
        else:
            facts = _contract_fact_rows(outcome)
            action_label = None
        if not facts:
            return None
        content = _render_unusable_candidate_discovery(action_label)
        _logger.info(
            "orchestration stage=discovery_terminal "
            "decision=UNUSABLE_CANDIDATE_CONTRACT tier=%s "
            "correlation_id=%s",
            tier,
            correlation,
        )
        return dataclasses.replace(
            outcome,
            content_text=content,
            structured=None,
            contract_facts=facts,
            projected_content=content,
        )

    @staticmethod
    def _candidates_present(
        structured: Mapping[str, object] | None,
    ) -> bool:
        if not isinstance(structured, Mapping):
            return False
        candidates = structured.get("candidates")
        return isinstance(candidates, (list, tuple)) and bool(candidates)

    def _resolve_candidate(
        self,
        structured: Mapping[str, object] | None,
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
    ) -> Mapping[str, Any] | None:
        """Resolve the owner candidate to chain — or none.

        Exactly one live-token candidate chains deterministically; a
        multi-candidate set requires a bounded model selection of the
        owner-declared ``action_id`` (a proposal, never authority —
        the token still comes only from the owner payload). Zero or
        unresolvable sets fail closed.
        """
        if not isinstance(structured, Mapping):
            return None
        candidates = structured.get("candidates")
        if not isinstance(candidates, (list, tuple)):
            return None
        matching = [
            c
            for c in candidates
            if isinstance(c, Mapping)
            and isinstance(c.get(CANDIDATE_TOKEN_FIELD), str)
            and c[CANDIDATE_TOKEN_FIELD].strip()
        ]
        if len(matching) == 1:
            return matching[0]
        if len(matching) > 1:
            return self._select_candidate(
                matching,
                input_text,
                prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        return None

    def _select_candidate(
        self,
        candidates: Sequence[Mapping[str, Any]],
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
    ) -> Mapping[str, Any] | None:
        """Bounded model disambiguation of a multi-candidate owner set.

        The model sees only action ids and bounded descriptions —
        candidate tokens never reach the model and are never accepted
        from a proposal.
        """
        entries = []
        by_action: dict[str, list[Mapping[str, Any]]] = {}
        for candidate in candidates[:MAX_CANDIDATE_ENTRIES]:
            action_id = candidate.get("action_id")
            if not isinstance(action_id, str) or not action_id.strip():
                continue
            action_id = action_id.strip()
            by_action.setdefault(action_id, []).append(candidate)
            description = candidate.get("description")
            entries.append(
                {
                    "action_id": action_id,
                    "description": (
                        description
                        if isinstance(description, str)
                        else ""
                    )[:MAX_DESCRIPTION_CHARS],
                }
            )
        if not entries:
            return None
        payload = json.dumps(entries, ensure_ascii=False)[
            :MAX_SURFACE_CHARS
        ]
        proposal = self._model_stage_proposal(
            input_text,
            block_tag="candidates",
            block_payload=payload,
            instruction_id=CANDIDATE_SELECTION_INSTRUCTION_ID,
            instruction=self._instruction(CANDIDATE_SELECTION_INSTRUCTION_ID),
            instruction_lineage=_lineage(
                    CANDIDATE_SELECTION_INSTRUCTION_ID,
                    self._instruction(CANDIDATE_SELECTION_INSTRUCTION_ID),
                ),
            expected_fields=("applicable", "action_id"),
            input_kind="specialist_candidate_selection",
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return None
        if set(proposal) - {"applicable", "action_id", "limitations"}:
            return None
        applicable = proposal.get("applicable")
        if isinstance(applicable, str):
            applicable = applicable.strip().lower() == "true"
        if applicable is not True:
            return None
        action_id = proposal.get("action_id")
        if not isinstance(action_id, str):
            return None
        hits = by_action.get(action_id.strip())
        if hits is None or len(hits) != 1:
            return None
        return hits[0]

    def _candidate_arguments(
        self,
        candidate: Mapping[str, Any],
        proposed: Mapping[str, Any],
        input_text: str,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
        business_subject: str | None = None,
    ) -> dict[str, Any] | None:
        """Resolve inner args against the candidate's own schema.

        The owner candidate's ``argument_schema`` is only known after
        discovery — the selection proposal's keys are tried first, and
        when they do not satisfy the owner schema a bounded second
        proposal scoped to that schema is attempted. Both paths end in
        the same deterministic validation; a proposal is never
        authority.
        """
        schema = candidate.get("argument_schema")
        effective_schema: Mapping[str, Any] | None = None
        if isinstance(schema, Mapping):
            effective_schema = dict(schema)
        required_args = candidate.get("required_arguments")
        if isinstance(required_args, (list, tuple)) and required_args:
            # Owner-declared required arguments are typed contract —
            # enforce them even when the published schema is absent
            # or malformed; a candidate never executes without them.
            effective_schema = (
                dict(effective_schema)
                if effective_schema is not None
                else {}
            )
            effective_schema["required"] = [
                str(r) for r in required_args
            ]
        if effective_schema is not None:
            merged = _validate_instance(dict(proposed), effective_schema)
        else:
            merged = (
                validate_untyped_arguments(proposed)
                if isinstance(proposed, Mapping)
                else None
            )
        if merged is not None:
            return merged
        second = self._propose_candidate_arguments(
            input_text,
            effective_schema,
            prior_turns,
            correlation=correlation,
            deadline=deadline,
            business_subject=business_subject,
        )
        if second is None:
            return None
        if effective_schema is not None:
            return _validate_instance(second, effective_schema)
        return (
            validate_untyped_arguments(second)
            if isinstance(second, Mapping)
            else None
        )

    def _propose_candidate_arguments(
        self,
        input_text: str,
        schema: Mapping[str, Any] | None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        correlation: str = "",
        deadline: TurnDeadline | None = None,
        business_subject: str | None = None,
    ) -> Mapping[str, Any] | None:
        """Bounded model proposal of inner arguments, schema-scoped."""
        schema_payload = json.dumps(
            {
                "business_subject": business_subject,
                "schema": schema or {"type": "object"},
            }
            if business_subject is not None
            else (schema or {"type": "object"}),
            ensure_ascii=False,
            default=str,
        )[:MAX_SURFACE_CHARS]
        proposal = self._model_stage_proposal(
            input_text,
            block_tag="schema",
            block_payload=schema_payload,
            instruction_id=CANDIDATE_ARGUMENTS_INSTRUCTION_ID,
            instruction=self._instruction(CANDIDATE_ARGUMENTS_INSTRUCTION_ID),
            instruction_lineage=_lineage(
                    CANDIDATE_ARGUMENTS_INSTRUCTION_ID,
                    self._instruction(CANDIDATE_ARGUMENTS_INSTRUCTION_ID),
                ),
            expected_fields=("arguments",),
            input_kind="specialist_candidate_arguments",
            prior_turns=prior_turns,
            correlation=correlation,
            deadline=deadline,
        )
        if proposal is None:
            return None
        if set(proposal) - {"arguments", "limitations"}:
            return None
        normalized = normalize_arguments(proposal.get("arguments"))
        if normalized is None:
            return None
        if set(normalized) & ORCHESTRATED_FIELDS:
            return None
        return normalized

    def _invoke(
        self,
        group: CapabilityGroup,
        remote_name: str,
        arguments: Mapping[str, Any],
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> SpecialistOutcome:
        """Dispatch one invocation through the owning provider adapter.

        The orchestrator never inspects the capability's binding —
        provider mechanics (transport, protocols, delegated
        credentials) stay inside the adapter.
        """
        capability = next(
            (
                cap
                for cap in group.capabilities
                if cap.remote_name == remote_name
            ),
            None,
        )
        if capability is None:
            raise CapabilityProviderError(
                "capability_not_on_surface",
                "capability is not on the live provider surface",
            )
        if deadline is not None:
            deadline.check("provider_invoke")
        # CP5/R3: cancellation observed mid-attempt stops the provider
        # call too — no new operation after a disconnect.
        if _cancel_observed():
            raise _TurnCancelled()
        # CP4 governed resume frontier — the capability is resolved
        # from the FRESH live group above, never from the checkpoint.
        # A recorded outcome replays only for an identical
        # non-mutating invocation; a PREPARE/ACT (or any class not
        # allowlisted) marks the frontier — once a material
        # invocation has started, no further attempt may run.
        resume_state = _RESUME_STATE.get()
        resumable = (
            capability.operation_class in _RESUMABLE_OPERATION_CLASSES
        )
        invoke_key = _resume_invoke_key(
            group.group_id, remote_name, arguments
        )
        if resume_state is not None:
            if not resumable:
                resume_state.mutating_invoke_started = True
            elif invoke_key in resume_state.invoke_outcomes:
                _logger.info(
                    "orchestration stage=provider_invoke "
                    "decision=resumed capability=%s.%s "
                    "correlation_id=%s",
                    group.group_id,
                    remote_name,
                    correlation,
                )
                return resume_state.invoke_outcomes[invoke_key]
        provider = self._providers.get(group.provider_id)
        if provider is None:
            raise CapabilityProviderError(
                "provider_unavailable",
                "capability provider is not configured",
            )
        started = time.monotonic()
        # LOOP-03R1 (observability): declared argument KEYS only —
        # never values, tokens, or payload content.
        arg_keys = ",".join(sorted(str(k) for k in arguments))[:200]
        # Real observation: the invocation is about to happen — emit the
        # semantic started event only at this boundary, never earlier.
        _emit_activity(
            phase=ActivityPhase.SOURCE_QUERY_STARTED,
            correlation=correlation,
            capability_ref=_activity_capability_ref(
                remote_name=remote_name,
                operation_class=capability.operation_class.value,
            ),
            **_group_activity_refs(group),
        )
        try:
            outcome = provider.invoke(
                capability,
                arguments,
                correlation_id=correlation,
                # LOOP-03R2A-R1: the invocation is bounded by the
                # remaining turn budget — the provider clamps to its
                # own stage max underneath.
                timeout_seconds=(
                    deadline.remaining_seconds()
                    if deadline is not None
                    else None
                ),
            )
        except CapabilityProviderError as exc:
            # Stage 6 attribution: a real owner-surface call that
            # failed — operational elapsed time, never model time.
            op_ledger = current_call_ledger()
            if op_ledger is not None:
                op_ledger.record_operational(
                    capability=remote_name,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    finish_status=(
                        "timeout"
                        if "timeout" in str(exc.code).lower()
                        else "error"
                    ),
                )
            # LOOP-03R1 (latency): bounded stage timing — declared keys
            # only, never values/tokens.
            _logger.info(
                "orchestration stage=provider_invoke decision=error "
                "capability=%s.%s class=%s arg_keys=%s timing_ms=%d "
                "correlation_id=%s",
                group.group_id,
                remote_name,
                capability.operation_class.value,
                arg_keys,
                int((time.monotonic() - started) * 1000),
                correlation,
            )
            _emit_activity(
                phase=ActivityPhase.SOURCE_QUERY_COMPLETED,
                state=ActivityState.FAILED,
                correlation=correlation,
                capability_ref=_activity_capability_ref(
                    remote_name=remote_name,
                    operation_class=capability.operation_class.value,
                ),
                outcome_ref=_activity_outcome_ref(
                    status=ActivityOutcomeStatus.ERROR
                ),
                **_group_activity_refs(group),
            )
            raise
        _logger.info(
            "orchestration stage=provider_invoke decision=ok "
            "capability=%s.%s class=%s arg_keys=%s timing_ms=%d "
            "correlation_id=%s",
            group.group_id,
            remote_name,
            capability.operation_class.value,
            arg_keys,
            int((time.monotonic() - started) * 1000),
            correlation,
        )
        # Stage 6 attribution: measured owner-surface execution time —
        # separated from semantic decision time in the turn ledger.
        op_ledger = current_call_ledger()
        if op_ledger is not None:
            op_ledger.record_operational(
                capability=remote_name,
                duration_ms=int((time.monotonic() - started) * 1000),
                finish_status="completed",
            )
        # The outcome provenance is the only legitimate protocol
        # evidence — it was actually observed on this invocation.
        _emit_activity(
            phase=ActivityPhase.SOURCE_QUERY_COMPLETED,
            state=(
                ActivityState.PARTIAL
                if outcome.status is SpecialistResultStatus.PARTIAL
                else ActivityState.COMPLETED
            ),
            correlation=correlation,
            capability_ref=_activity_capability_ref(
                remote_name=remote_name,
                protocol=outcome.provenance.protocol.value,
                operation_class=capability.operation_class.value,
            ),
            outcome_ref=_activity_outcome_summary(outcome),
            **_group_activity_refs(group),
        )
        # Only a verified non-mutating outcome is recorded — replay
        # applies to the identical invocation of a later attempt. It
        # is recorded BEFORE the post-invoke deadline check: the call
        # provably completed; a late deadline must not turn a finished
        # READ into a duplicated one on resume.
        # CP5/R1: only a COMPLETE, fully-postconditioned outcome is a
        # verifiable checkpoint — a partial/incomplete result is
        # degraded evidence, so the resumed attempt re-issues the same
        # non-mutating read instead of freezing it.
        if (
            resume_state is not None
            and resumable
            and outcome.is_complete
            and outcome.status is SpecialistResultStatus.COMPLETED
        ):
            resume_state.invoke_outcomes[invoke_key] = outcome
        # An outcome that arrives after the turn deadline may not be
        # processed — fail truthfully at the boundary.
        if deadline is not None:
            deadline.check("provider_invoke")
        return outcome
