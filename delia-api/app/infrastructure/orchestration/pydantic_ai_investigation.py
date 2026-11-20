"""Pydantic AI native-first investigation runtime (docs 231–235).

Production ``SupportsGovernedCapabilityAttempt`` implementation.
Semantic investigation is a bounded ``pydantic_ai.Agent`` tool loop.
Tools delegate ONLY to Application governed execution gates — never to
any second Application semantic controller (doc 241 — the
legacy ``_governed_owner_path`` sequencer was removed).

Native-first (doc 235): typed tool args, optional goal declaration,
clarification ask-back, agent-requested multi-source composition,
UsageLimits/telemetry. No intent-specific hardcoded workflows.

Layer position:

    SupportsGovernedCapabilityAttempt  (this adapter)
            │
            ▼
    SupportsGovernedStageGates         (catalog / invoke / finalize)
            │
            ▼
    CapabilityProviderPort / Evidence / Core AuthZ

``pydantic_ai`` imports stay in this infrastructure module only.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
import re
import time

from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Container,
    Literal,
    Mapping,
    NotRequired,
    Sequence,
    TypedDict,
)

from app.application.capability_provision.contracts import (
    InvestigationAnswer,
    InvestigationAnswerStatus,
)
from app.application.capability_provision.conversational_response import (
    MAX_RENDER_CONTENT_CHARS,
)
from app.application.capability_provision.generic_evidence_renderer import (
    extract_pagination_envelope,
)
from app.application.interaction.contracts import (
    LIMITATION_ARGUMENT_SCHEMA_REJECTED,
    LIMITATION_RESULT_TRUNCATED,
)
from app.application.capability_provision.governed_stage_gates import (
    SupportsGovernedStageGates,
)
from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_DISCOVERY,
    INVESTIGATION_PROGRESS_NEW,
    INVESTIGATION_PROGRESS_NONE,
    INVESTIGATION_PROGRESS_RELATED,
    _IDENTIFIER_LITERAL_RE,
    _INVOCATION_VOCABULARY_KEYS,
    _CONSULTATION_OPERATIONS,
    _PAGINATION_ARG_KEYS,
    _LAST_CATALOG_FAILURES,
    _OBLIGATION_OPERATIONS,
    _presentation_scope_arg_keys,
    OBLIGATION_SATISFIED,
    _attempt_identifier_roots,
    _emit_activity,
    _evaluate_material_obligations,
    _is_business_evidence_attempt,
    _listing_failure_is_transient,
    _plan_delivery_mode,
    classify_investigation_progress,
    observation_content_fingerprint,
)
from app.application.interaction.activity import (
    ActivityEventSink,
    ActivityPhase,
)
from app.application.interaction.capability_attempt import (
    EARLY_CONVERSATIONAL_ADMISSION,
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.domain.evidence.model import EpistemicClass
from app.application.interaction.workspace_context import WorkspaceContext
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    TurnKind,
)
from app.infrastructure.config.cri_instruction_resource import (
    CriInstructionResourceError,
    SelectedInvestigationInstructions,
    default_comprehension_instructions_path,
    default_investigation_instructions_path,
    load_comprehension_instructions,
    load_investigation_instructions,
    resolve_comprehension_instruction_version,
    resolve_investigation_instruction_version,
)
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
    OWNER_ARGUMENT_REJECTED,
    SpecialistInteropError,
)
from pydantic_ai.usage import RunUsage

_logger = logging.getLogger(__name__)

_INTERNAL_OBS_MARKER = __import__("re").compile(r"\[obs:\d+\]\s*")
_LOOKS_LIKE_DICT_REPR = __import__("re").compile(
    r"^\{[\s\S]{1,2000}:.*\}$"
)

# Library defaults for direct unit construction only — production
# composition always injects the validated runtime-config snapshot
# (doc 243); these literals are never a second source of truth.
_DEFAULT_REQUEST_LIMIT = 12
_DEFAULT_TOOL_CALL_LIMIT = 8
_DEFAULT_AGENT_RETRIES = 1
_DEFAULT_TOOL_PROJECTION_LIMIT = 6000
_DEFAULT_PRIOR_TURNS_LIMIT = 4


def build_openai_compatible_investigation_model(
    *,
    base_url: str,
    api_key: str,
    model: str,
):
    """Compose the Agent model behind infrastructure boundaries."""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    if not (base_url and api_key and model):
        raise ValueError(
            "investigation model requires base_url, api_key and model"
        )
    return OpenAIChatModel(
        model,
        provider=OpenAIProvider(
            base_url=base_url.rstrip("/"), api_key=api_key
        ),
    )


# Instruction lineage is the governed JSON resource
# ``config/investigation_instructions.delpi.json`` (INT-1 isolation).
# Keep content owner-/tool-agnostic: live capability names, schemas and
# argument contracts come from tools/list + each tool description —
# never from hardcoded specialist workflows in the resource text.
_INVESTIGATION_INSTRUCTIONS_PATH = (
    default_investigation_instructions_path()
)


def load_selected_investigation_instructions(
    *,
    instruction_version: str | None = None,
    path: Path | str | None = None,
) -> SelectedInvestigationInstructions:
    """Load INT-1 instructions; fail closed when the resource is invalid."""
    resource_path = path or _INVESTIGATION_INSTRUCTIONS_PATH
    try:
        bundle = load_investigation_instructions(resource_path)
    except CriInstructionResourceError:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed at boundary
        raise CriInstructionResourceError(
            "investigation_instruction_resource_unreadable",
            str(exc),
        ) from exc
    selected = resolve_investigation_instruction_version(
        instruction_version
    )
    return bundle.select(selected)


# Compatibility exports for tests/harnesses that still reference the
# historical module constants. Values are the *default* resource
# version at import time (baseline), not the possibly overridden
# candidate selected later via env for a single eval process.
try:
    _DEFAULT_SELECTED = load_selected_investigation_instructions()
except CriInstructionResourceError:  # pragma: no cover — fail at use
    _DEFAULT_SELECTED = None  # type: ignore[assignment]

_INVESTIGATION_INSTRUCTION_VERSION = (
    _DEFAULT_SELECTED.instruction_version
    if _DEFAULT_SELECTED is not None
    else "generalist-semantic-v2"
)
_INVESTIGATION_INSTRUCTIONS = (
    _DEFAULT_SELECTED.text if _DEFAULT_SELECTED is not None else ""
)


def load_selected_comprehension_instructions(
    *,
    instruction_version: str | None = None,
    path: Path | str | None = None,
) -> SelectedInvestigationInstructions:
    """Load INT-2 comprehension instructions; fail closed when invalid.

    Governed resource ``config/comprehension_instructions.delpi.json`` —
    the comprehension specialist's own versioned text, never a copy of
    the investigation instructions.
    """
    resource_path = path or default_comprehension_instructions_path()
    try:
        bundle = load_comprehension_instructions(resource_path)
    except CriInstructionResourceError:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed at boundary
        raise CriInstructionResourceError(
            "comprehension_instruction_resource_unreadable",
            str(exc),
        ) from exc
    selected = resolve_comprehension_instruction_version(
        instruction_version
    )
    return bundle.select(selected)


@dataclass(frozen=True)
class ComprehensionTurnOutcome:
    """Bounded end-of-run signal from the comprehension specialist.

    Observability only — the authoritative comprehension artifacts are
    the Application-accepted plan (``deps.investigation_plan``) and the
    recorded clarification question, never this declared status.
    """

    status: str
    note: str = ""


def _build_native_mcp_toolset(config, *, process_tool_call):
    """One real ``MCPToolset`` per specialist from the governed
    connection config — SDK discovery (tools/list) only; every call is
    intercepted by ``process_tool_call`` before the wire."""
    from pydantic_ai.mcp import MCPToolset

    return MCPToolset(
        config.endpoint,
        headers=dict(config.headers) or None,
        process_tool_call=process_tool_call,
        init_timeout=config.timeout_seconds,
        read_timeout=config.timeout_seconds,
    )


class ObligationProposal(TypedDict):
    """Typed material-obligation proposal for declare_investigation_goal.

    ``description`` is required; ``evidence_source`` anchors the
    obligation to live owner vocabulary (entity/action/capability
    token), ``operation`` requires a SpecialistOperationClass, and
    ``required_args`` binds the obligation to a declared business
    scope (a nested argument object mirroring the invocation args —
    e.g. ``{"params": {"status": "ativo"}}``) — all verifiable
    proposals, never authorization (RC5).
    """

    description: str
    evidence_source: NotRequired[str]
    operation: NotRequired[str]
    required_args: NotRequired[dict]


def _tool_prop_declares_object(prop: Any) -> bool:
    if not isinstance(prop, Mapping):
        return False
    if prop.get("type") == "object":
        return True
    for key in ("anyOf", "oneOf"):
        alts = prop.get(key)
        if not isinstance(alts, Sequence):
            continue
        for alt in alts:
            if isinstance(alt, Mapping) and alt.get("type") == "object":
                return True
    return False


def _prepare_tool_definitions_envelope_hints(ctx: Any, tool_defs: list) -> list:
    """Schema-derived usage guidance via the native ``prepared()`` seam.

    The old synthesized Python tools carried ``Pass arguments as an
    object / do not invent candidate_token`` in their descriptions —
    without it the model calls execute tools with an empty
    ``arguments`` envelope. The hint is derived ONLY from the
    published inputSchema (presence of ``candidate_token`` /
    ``arguments``): never owner-specific, never fabricated args.
    ``prepared()`` participates in ``Agent.for_run`` / ``for_run_step``
    rebinding natively, so the hint layer survives the per-run toolset
    rebuild that dropped plain proxies (B3).

    Live owner schemas often publish nullable objects as
    ``anyOf: [{type: object}, {type: null}]``; hint detection must
    recognize that shape or EnvelopeHint stays silent on B3.
    """
    import dataclasses as _dc

    prepared = []
    for tdef in tool_defs:
        schema = tdef.parameters_json_schema
        props = (
            schema.get("properties")
            if isinstance(schema, Mapping)
            else None
        )
        if isinstance(props, Mapping):
            desc = (tdef.description or "").strip()
            hints: list[str] = []
            if "candidate_token" in props:
                hints.append(
                    " Arguments: pass candidate_token verbatim "
                    "from a prior discovery result (never invent "
                    "it) and arguments as a non-empty object built "
                    "from that candidate's "
                    "argument_schema/required_arguments "
                    '(e.g. {"code": "50220013"}).'
                )
            if (
                "capability" in props
                and "arguments" in props
                and _tool_prop_declares_object(props.get("arguments"))
            ):
                hints.append(
                    " Business fields declared by the selected "
                    "capability schema belong inside the "
                    "arguments object — not as top-level siblings "
                    "of capability."
                )
            if any(
                _tool_prop_declares_object(prop)
                for prop in props.values()
            ):
                hints.append(
                    " Object-typed parameters must be real JSON "
                    "objects — never JSON-encoded strings."
                )
            hint = "".join(hints)
            if hint and hint.strip() not in desc:
                # Preserve the published MCP description in full.
                # Truncating ``(desc + hint)[:500]`` destroyed owner
                # semantic discrimination (long TEO/DAVI contracts).
                # Hints stay schema-derived and length-bounded; the
                # owner text is never shortened to make room for them.
                tdef = _dc.replace(
                    tdef,
                    description=desc + hint[:280],
                )
        prepared.append(tdef)
    return prepared


@dataclass
class InvestigationDeps:
    """Closed-over turn authority — the model never supplies these."""

    gates: SupportsGovernedStageGates
    input_text: str
    correlation: str
    actor_user_id: str | None
    session_id: str | None
    workspace_context: WorkspaceContext | None
    prior_turns: tuple[ConversationContextTurn, ...]
    prepare_only: bool
    unbound_outcome: str | None
    deadline: TurnDeadline
    collected: list[GovernedCapabilityAttempt] = field(
        default_factory=list
    )
    tool_projection_limit: int = _DEFAULT_TOOL_PROJECTION_LIMIT
    tool_calls: int = 0
    investigation_plan: object | None = None
    clarification_question: str | None = None
    composed_attempt: GovernedCapabilityAttempt | None = None
    non_progress_calls: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )
    # Content fingerprints of prior SUCCESS observations — used to
    # detect repeated equivalent bodies that do not advance coverage.
    observed_content_fingerprints: set[str] = field(default_factory=set)
    # One-shot flag: the insufficiency ModelRetry may buy a single
    # extra investigation pass per run — a re-declared insufficiency
    # must never burn the whole retry budget as agent_error.
    insufficiency_retry_used: bool = False
    # Same one-shot pattern: an unbound evidence_ref may recover once
    # via ModelRetry; a second bad declaration is handled by the
    # deterministic acceptor, never by burning more retry budget.
    evidence_ref_retry_used: bool = False
    # One-shot owner_argument_rejected recovery via ModelRetry with
    # the owner validation hint — never infinite equivalent retries.
    owner_argument_retry_used: bool = False
    # One-shot continuity nudge when an observation made NO_PROGRESS
    # while user identifiers remain uncovered — never forces an owner
    # or capability; asks the model to re-select from live contracts.
    no_progress_continuity_retry_used: bool = False
    # Per-fingerprint transient retry budget: an identical call after a
    # transient owner failure (timeout/unavailable/transport/connection)
    # may re-reach the owner ONCE. Terminal, AUTHZ and unknown failures
    # stay fail-closed — same classification contract as listing.
    transient_invoke_retries: set[str] = field(default_factory=set)
    # Measured provider usage for the whole turn (both legs in variant
    # B) — populated by the counting model wrapper so consumption is
    # accounted even when a run ends on an exception.
    turn_usage: RunUsage | None = None




def _is_authorization_denial(attempt: GovernedCapabilityAttempt) -> bool:
    """True when Core/Domain/MCP denied access — never a NO_PROGRESS retry."""
    if attempt.status is GovernedCapabilityStatus.AUTHZ_DENIED:
        return True
    return attempt.error_code in (
        MCP_AUTHORIZATION_DENIED,
        "authz_denied",
    )


def continuity_model_retry_allowed(
    *,
    attempt: GovernedCapabilityAttempt,
    investigation_progress: str | None,
    uncovered: Sequence[str] | tuple[str, ...] | list[str],
    already_used: bool,
    under_tool_limit: bool,
) -> bool:
    """Gate for the one-shot NO_PROGRESS continuity ModelRetry.

    Authorization denials are terminal for the protected evidence: a
    generic continuity retry must never encourage bypass via another
    owner for the same data. Argument-schema rejections already carry
    actionable INVALID_ARGUMENTS feedback in the observation — a
    generic "select a different capability" retry would mask the real
    correction and push the model away from the right tool.
    """
    if _is_authorization_denial(attempt):
        return False
    if LIMITATION_ARGUMENT_SCHEMA_REJECTED in (attempt.limitations or ()):
        return False
    if already_used or not under_tool_limit:
        return False
    if not uncovered:
        return False
    return investigation_progress == INVESTIGATION_PROGRESS_NONE


# Keys that must survive projection overflow — continuity, provenance,
# coverage and recovery. Never silently drop these for a bare overview.
_BOUNDED_ESSENTIAL_KEYS: frozenset[str] = frozenset(
    {
        "status",
        "error_code",
        "authorization_denied",
        "limitations",
        "investigation_progress",
        "pagination",
        "continuation_note",
        "coverage_note",
        "evidence_citable",
        "evidence_handle",
        "observation_index",
        "action_id",
        "operation_class",
        "authoritative_root_code",
        "owner_validation_hint",
        "uncovered_user_identifiers",
        "provenance_specialist",
        "provenance_capability",
        "source_ids",
        "has_verified_composition",
        "entity",
        "candidates",
        "repeated_observation_no_progress",
    }
)


def _bounded_json(payload: Any, *, limit: int = 6000) -> str:
    """Serialize tool observations with explicit, recoverable truncation.

    Scale field/list caps with the configured projection budget. When the
    final payload still exceeds ``limit``, keep essential continuity /
    provenance / pagination fields and mark incompleteness — never replace
    the observation with a status/content stub that drops recovery signals.
    """
    truncated = False
    safe_limit = max(500, int(limit))
    # Scale with budget so a 20k projection is not crushed by historical
    # 1200/40 magic constants; still bounded for runaway nesting.
    str_cap = max(1200, min(safe_limit // 2, 50_000))
    list_cap = max(40, min(safe_limit // 100, 500))
    key_cap = max(48, min(safe_limit // 80, 256))

    def _shrink(value: Any, *, depth: int = 0) -> Any:
        nonlocal truncated
        if depth > 8:
            truncated = True
            return None
        if isinstance(value, Mapping):
            out: dict[str, Any] = {}
            items = list(value.items())
            # Prefer essential keys first so overflow drops voluminous
            # business fields, not recovery/provenance metadata.
            ordered = sorted(
                items,
                key=lambda pair: (
                    0 if str(pair[0]) in _BOUNDED_ESSENTIAL_KEYS else 1,
                    str(pair[0]),
                ),
            )
            for idx, (key, item) in enumerate(ordered):
                if idx >= key_cap:
                    truncated = True
                    break
                out[str(key)[:120]] = _shrink(item, depth=depth + 1)
            return out
        if isinstance(value, (list, tuple)):
            items = list(value)
            if len(items) > list_cap:
                truncated = True
                items = items[:list_cap]
            return [_shrink(item, depth=depth + 1) for item in items]
        if isinstance(value, str):
            if len(value) > str_cap:
                truncated = True
                return value[:str_cap]
            return value
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        text = str(value)
        if len(text) > min(400, str_cap):
            truncated = True
            return text[: min(400, str_cap)]
        return text

    body = _shrink(payload)
    if truncated:
        if isinstance(body, dict):
            body = dict(body)
            body["truncated"] = True
            body.setdefault(
                "note",
                "tool_observation_fields_reduced_for_model_budget",
            )
        else:
            body = {"value": body, "truncated": True}
    raw = json.dumps(body, ensure_ascii=False, default=str)
    if len(raw) <= safe_limit:
        return raw

    # Final-budget overflow: preserve essential investigation fields.
    overview: dict[str, Any] = {
        "truncated": True,
        "note": "tool_observation_exceeded_model_budget",
        "coverage_note": (
            "Observation projection exceeded the configured model "
            "budget. Essential continuity fields are preserved; "
            "remaining business payload was not fully delivered — "
            "do not treat this as a complete population."
        ),
    }
    if isinstance(body, Mapping):
        for key in _BOUNDED_ESSENTIAL_KEYS:
            if key in body and key not in overview:
                overview[key] = body[key]
        content = body.get("content")
        if content is not None:
            content_budget = max(200, safe_limit // 4)
            text = str(content)
            overview["content"] = (
                text
                if len(text) <= content_budget
                else text[:content_budget]
            )
    else:
        overview["content"] = str(body)[: max(200, safe_limit // 4)]

    overflow_raw = json.dumps(overview, ensure_ascii=False, default=str)
    if len(overflow_raw) <= safe_limit:
        return overflow_raw
    # Last resort: drop voluminous optional essentials, keep recovery spine.
    spine_keys = (
        "status",
        "error_code",
        "limitations",
        "pagination",
        "continuation_note",
        "investigation_progress",
        "evidence_handle",
        "observation_index",
        "authoritative_root_code",
        "uncovered_user_identifiers",
        "provenance_specialist",
        "provenance_capability",
        "action_id",
    )
    spine: dict[str, Any] = {
        "truncated": True,
        "note": "tool_observation_exceeded_model_budget",
        "coverage_note": overview["coverage_note"],
    }
    for key in spine_keys:
        if key in overview:
            spine[key] = overview[key]
    if "content" in overview:
        spine["content"] = str(overview["content"])[
            : max(120, safe_limit // 8)
        ]
    return json.dumps(spine, ensure_ascii=False, default=str)


def _declared_container_only(declared: object) -> bool:
    """True when the published schema requires an object/array that a
    serialized string cannot satisfy (``string`` absent from union)."""
    if declared in ("object", "array"):
        return True
    if isinstance(declared, (list, tuple)):
        return (
            ("object" in declared or "array" in declared)
            and "string" not in declared
        )
    return False


# Descriptions carry the owner-published selector FIELD vocabulary
# (e.g. "process: filial_id/.../q/page") the comprehension needs to
# declare required_args/required_scope with real fields — a tighter
# bound silently drops it and forces invented fields (INT2_A2:
# params.name vs the declared params.q).
_COMPREHENSION_CATALOG_DESC_LIMIT = 1400
_COMPREHENSION_CATALOG_BLOCK_LIMIT = 12000


def _comprehension_catalog_block(
    live_catalog: object,
    *,
    goal_classes: object = (),
    delivery_modes: object = (),
) -> str | None:
    """Bounded advisory projection of the Application-owned catalog.

    The comprehension specialist needs the live anchor vocabulary to
    formulate valid typed goals on the first declaration instead of
    learning it through acceptor rejections. The projection carries
    only selection-relevant metadata — the invocation surface name,
    owner, operation class, a bounded description excerpt, the
    selector vocabulary the schema declares and the typed contract
    vocabularies (selector args, operation classes) — embedded as
    untrusted JSON data. It grants no authorization: the same
    acceptor remains the only authority.

    Returns ``None`` when the catalog is unavailable/empty, and a
    ``catalog_truncated`` marker when the bounded projection cannot
    carry every entry — never a silently partial catalog.
    """
    entries: list[dict[str, Any]] = []
    if isinstance(live_catalog, (list, tuple)):
        for entry in live_catalog:
            if not isinstance(entry, Mapping):
                continue
            cap_id = entry.get("capability_id")
            if not isinstance(cap_id, str) or not cap_id.strip():
                continue
            selectors: dict[str, str] = {}
            selector_args: list[str] = []
            schema = entry.get("input_schema")
            if isinstance(schema, Mapping):
                props = schema.get("properties")
                if isinstance(props, Mapping):
                    for name, spec in list(props.items())[:12]:
                        if isinstance(spec, Mapping):
                            kind = spec.get("type")
                            enum = spec.get("enum")
                            label = (
                                str(kind)
                                if isinstance(kind, str)
                                else "value"
                            )
                            if isinstance(enum, (list, tuple)):
                                label += "=" + "|".join(
                                    str(v)[:40]
                                    for v in list(enum)[:8]
                                )
                            selectors[str(name)[:60]] = label
                        if str(name) in _INVOCATION_VOCABULARY_KEYS:
                            selector_args.append(str(name))
            item: dict[str, Any] = {
                # Named for what it is — the governed invocation
                # surface — so it is never mistaken for an
                # ``evidence_source`` anchor (real-eval flake: the
                # model copied ``capability_id`` values like
                # ``teo.read`` into the anchor field).
                "invocation_surface": cap_id.strip()[:120],
            }
            owner = entry.get("group_id") or entry.get("owner")
            if isinstance(owner, str) and owner.strip():
                item["owner"] = owner.strip()[:80]
            op = entry.get("operation_class")
            if isinstance(op, str) and op.strip():
                item["operation_class"] = op.strip()[:40]
            item["selector_args"] = selector_args[:8]
            desc = entry.get("description")
            if isinstance(desc, str) and desc.strip():
                item["description"] = desc.strip()[
                    :_COMPREHENSION_CATALOG_DESC_LIMIT
                ]
            if selectors:
                item["selectors"] = selectors
            entries.append(item)
    if not entries:
        return None
    block: dict[str, Any] = {
        "anchor_contract": (
            "evidence_source is an owner-vocabulary VALUE the "
            "invocation passes in one of the capability's "
            "selector_args (e.g. the `entity` value like \"process\" "
            "or an `action` value) — never the invocation_surface "
            "id; dotted surface ids are rejected. operation takes "
            "one operation_classes value only (entity actions like "
            "search/get belong in required_args, never in "
            "operation — omit operation unless the objective itself "
            "demands that class; under aggregation delivery operation "
            "is rejected as non-material (the aggregate is the "
            "demonstration). required_args declares only the "
            "material business scope the user asked for (filters, "
            "identities, units, periods) using the field vocabulary "
            "the owner publishes — never presentation selectors like "
            "view/format (rejected as non-material) and never a "
            "mirror of the call you intend to make. goal_class and "
            "expected_delivery take ONLY values from the "
            "goal_classes and expected_delivery lists."
        ),
        "operation_classes": sorted(_OBLIGATION_OPERATIONS),
        "goal_classes": sorted(
            str(item) for item in goal_classes if str(item)
        ),
        "expected_delivery": sorted(
            str(item) for item in delivery_modes if str(item)
        ),
        "capabilities": entries,
    }
    rendered = _bounded_json(block, limit=_COMPREHENSION_CATALOG_BLOCK_LIMIT)
    if len(entries) > 1:
        # When the bound cut entries, mark the bound honestly rather
        # than presenting a partial catalog as complete.
        rendered_full = _bounded_json(block, limit=_COMPREHENSION_CATALOG_BLOCK_LIMIT * 8)
        if len(rendered) < len(rendered_full):
            rendered = rendered + (
                "\ncatalog_truncated: projection bounded; remaining "
                "capabilities are still discoverable via the "
                "investigation tool surface."
            )
    return rendered


def _schema_pagination_arg_names(input_schema: object) -> tuple[str, ...]:
    """Schema-declared pagination-capable argument names.

    A property qualifies when its name is a proven slice selector or
    its owner-published description declares pagination semantics.
    Derived from the capability's own contract — never invented.
    """
    if not isinstance(input_schema, Mapping):
        return ()
    props = input_schema.get("properties")
    if not isinstance(props, Mapping):
        return ()
    names: list[str] = []
    for name, spec in props.items():
        token = str(name)
        if token in _PAGINATION_ARG_KEYS:
            names.append(token)
            continue
        if isinstance(spec, Mapping):
            desc = spec.get("description")
            if isinstance(desc, str) and "paginat" in desc.casefold():
                names.append(token)
    return tuple(names[:8])


def _attempt_projection(
    attempt: GovernedCapabilityAttempt,
    *,
    observation_index: int,
    uncovered_after: Sequence[str] | tuple[str, ...] | list[str] = (),
    plan: object | None = None,
    operation_class: str | None = None,
    prior_content_fingerprints: frozenset[str] | set[str] = frozenset(),
    capability_id: str | None = None,
    pagination_args: Sequence[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    structured = (
        attempt.outcome.structured
        if attempt.outcome is not None
        and isinstance(attempt.outcome.structured, Mapping)
        else {}
    )
    data = structured.get("data") if isinstance(structured, Mapping) else None
    candidates_raw = ()
    if isinstance(structured, Mapping):
        raw = structured.get("candidates")
        if not isinstance(raw, (list, tuple)) and isinstance(data, Mapping):
            raw = data.get("candidates")
        if isinstance(raw, (list, tuple)):
            candidates_raw = tuple(raw[:8])
    candidate_summaries: list[dict[str, Any]] = []
    for item in candidates_raw:
        if not isinstance(item, Mapping):
            continue
        summary: dict[str, Any] = {}
        token = item.get("candidate_token")
        if isinstance(token, str) and token.strip():
            summary["candidate_token"] = token.strip()[:240]
        for key in (
            "action_id",
            "operation_id",
            "title",
            "label",
            "summary",
            "name",
            "description",
        ):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                summary[key] = value.strip()[:160]
        # The follow-up execute needs the candidate's argument contract —
        # without it the agent guesses argument names (e.g. `query`)
        # that the owner schema does not accept and the READ silently
        # degrades to an unfiltered list.
        required_args = item.get("required_arguments")
        if isinstance(required_args, (list, tuple)):
            summary["required_arguments"] = [
                str(arg)[:80] for arg in required_args[:12]
            ]
        arg_schema = item.get("argument_schema")
        if isinstance(arg_schema, Mapping):
            props = arg_schema.get("properties")
            if isinstance(props, Mapping):
                summary["argument_schema"] = {
                    "type": "object",
                    "properties": {
                        str(name)[:60]: {
                            "type": (
                                spec.get("type")
                                if isinstance(spec, Mapping)
                                else None
                            )
                        }
                        for name, spec in list(props.items())[:16]
                    },
                    "required": [
                        str(req)[:80]
                        for req in (
                            arg_schema.get("required")
                            if isinstance(
                                arg_schema.get("required"), (list, tuple)
                            )
                            else ()
                        )
                    ][:12],
                }
        if summary:
            candidate_summaries.append(summary)
    root_code = None
    if isinstance(data, Mapping):
        root = data.get("root")
        if isinstance(root, Mapping):
            code = root.get("code")
            if isinstance(code, str) and code.strip():
                root_code = code.strip()[:120]
        elif isinstance(root, str) and root.strip():
            root_code = root.strip()[:120]
    progress = classify_investigation_progress(
        attempt,
        prior_content_fingerprints=prior_content_fingerprints,
        uncovered_after=tuple(uncovered_after),
        plan=plan if plan is not None else None,  # type: ignore[arg-type]
        operation_class=operation_class,
    )
    projection: dict[str, Any] = {
        "observation_index": observation_index,
        "evidence_handle": f"obs:{observation_index}",
        # Requested capability — rejected attempts carry no provenance,
        # so the id must come from the invocation boundary.
        "capability_id": capability_id,
        # Same deterministic classification the governed acceptor
        # applies: discovery metadata, errors and empty results are
        # observations the model may READ, never citable business
        # evidence. Report them under limitations instead.
        "evidence_citable": _is_business_evidence_attempt(attempt),
        "investigation_progress": progress,
        "status": attempt.status.value,
        # Full owner content — size policy lives solely in ``_bounded_json``
        # (configured ``tool_projection_limit``). Silent ``[:2000]`` here
        # destroyed business records before the budget serializer ran.
        "content": (attempt.content or "") or None,
        "limitations": list(attempt.limitations),
        "error_code": attempt.error_code,
        "has_verified_composition": (
            attempt.verified_composition is not None
        ),
        "provenance_specialist": (
            attempt.provenance.specialist_id
            if attempt.provenance is not None
            else None
        ),
        "provenance_capability": (
            attempt.provenance.remote_capability
            if attempt.provenance is not None
            else None
        ),
        "action_id": (
            attempt.provenance.action_id
            if attempt.provenance is not None
            else structured.get("action_id")
            if isinstance(structured, Mapping)
            else None
        ),
        "entity": (
            structured.get("entity")
            if isinstance(structured, Mapping)
            else None
        ),
        "authoritative_root_code": root_code,
        "operation_class": operation_class,
        "candidates": candidate_summaries or None,
        "source_ids": [
            ref.source_id
            for ref in (
                attempt.provenance.source_refs
                if attempt.provenance is not None
                else ()
            )
        ][:8],
    }
    owner_hint = getattr(attempt, "owner_hint", None)
    if isinstance(owner_hint, str) and owner_hint.strip():
        projection["owner_validation_hint"] = owner_hint.strip()[:500]
    if _is_authorization_denial(attempt):
        # Fail-closed projection: denial is not missing data, not a
        # validation miss, and not a recoverable NO_PROGRESS cue.
        projection["authorization_denied"] = True
        projection["evidence_citable"] = False
        projection["coverage_note"] = (
            "Authorization denied by the governing authority. This is "
            "not missing data, not an argument error, and not technical "
            "unavailability. Do not retry equivalent access through "
            "another capability for the same protected evidence. "
            "Communicate the access limitation; preserve any separately "
            "authorized observations."
        )
    elif LIMITATION_ARGUMENT_SCHEMA_REJECTED in (attempt.limitations or ()):
        # Fixable contract violation on THIS capability — the generic
        # "select a different capability" note would push the model
        # away from the right tool and replay the same rejection. When
        # the owner exposes a context-discovery capability, name it:
        # the nested argument contract lives there, not in the tool
        # schema's top-level fields.
        _group = (
            capability_id.split(".", 1)[0].strip()
            if isinstance(capability_id, str) and "." in capability_id
            else ""
        )
        _discovery_hint = (
            f" Call {_group}.get_context to learn the entity/argument "
            "contract before retrying."
            if _group
            else " Consult the owner's context capability before "
            "retrying."
        )
        projection["coverage_note"] = (
            "Arguments were rejected by the owner schema — this is a "
            "correctable contract violation, not missing data or a "
            "dead end. Rebuild the arguments per the INVALID_ARGUMENTS "
            "feedback and this capability's declared schema — nested "
            "entity/action filters belong inside the declared object "
            "fields."
            + _discovery_hint
        )
    elif progress == INVESTIGATION_PROGRESS_RELATED:
        projection["coverage_note"] = (
            "Observation is related but does not satisfy the user "
            "objective. Choose a live capability whose contract "
            "matches the requested evidence kind."
        )
    elif progress == INVESTIGATION_PROGRESS_DISCOVERY:
        projection["coverage_note"] = (
            "Discovery/catalog metadata is not business evidence."
        )
    elif progress == INVESTIGATION_PROGRESS_NONE and uncovered_after:
        projection["coverage_note"] = (
            "No objective progress for open identifiers. Preserve the "
            "original objective and select a different live capability "
            "whose description matches the still-missing evidence."
        )
    # Surface open identifiers in the same projection the Agent reads.
    # Callers historically appended these after ``_attempt_projection``,
    # which left eval traces and any early return path without the
    # recovery signal even though ``uncovered_after`` already informed
    # progress classification.
    if uncovered_after:
        projection["uncovered_user_identifiers"] = list(uncovered_after)
        if "coverage_note" not in projection:
            projection["coverage_note"] = (
                "Named identifiers still lack an authoritative "
                "observation. Choose the next owner tool yourself."
            )
    # INT-2 typed objective: while no goal is declared the finalize
    # coverage verdict stays coverage_unknown — surface that as a
    # model-visible signal on every observation, never silently.
    # Higher-priority notes (authorization denial, schema rejection)
    # keep their coverage_note; the pending flag still travels.
    if plan is None:
        projection["goal_declaration_pending"] = True
        if "coverage_note" not in projection:
            projection["coverage_note"] = (
                "Typed objective undeclared — coverage cannot be "
                "evaluated. Declare the user's objective, expected "
                "delivery and evidence obligations once via "
                "declare_investigation_goal before finalizing."
            )
    # Reuse the canonical owner pagination detector — do not invent
    # cursors. Surface page/has_more so the model can continue a
    # truncated list with the same tool schema (P2 continuity).
    envelope = extract_pagination_envelope(structured)
    if envelope is not None:
        projection["pagination"] = {
            "page": envelope.page,
            "page_size": envelope.page_size,
            "has_more": envelope.has_more,
            "total_count": envelope.total_count,
            "items_in_page": len(envelope.items),
        }
        # next_page is contract-derived (page + 1) only when the owner
        # declared page semantics and more pages exist — never invented
        # when the owner provides no page numbering.
        if envelope.has_more is True and isinstance(envelope.page, int):
            projection["pagination"]["next_page"] = envelope.page + 1
        if pagination_args:
            projection["pagination"]["pagination_args"] = list(
                pagination_args
            )
    truncated = LIMITATION_RESULT_TRUNCATED in (
        attempt.limitations or ()
    )
    needs_continuation = truncated or (
        envelope is not None and envelope.has_more is True
    )
    if needs_continuation:
        hint = ""
        if pagination_args:
            hint = (
                " This capability declares pagination-capable argument"
                " %s — pass the next page through it (for example as"
                " its page/page_size selector), preserving the same"
                " filters and scope across pages." % (
                    "s " + ", ".join(
                        str(a) for a in pagination_args[:4]
                    )
                    if len(pagination_args) > 1
                    else " `" + str(pagination_args[0]) + "`"
                )
            )
        projection["continuation_note"] = (
            "Owner result is truncated or an incomplete page. If the "
            "tool schema exposes page/page_size (or equivalent), call "
            "again with the next page parameters to continue — do not "
            "treat a single page as the full population." + hint
        )
    return projection


def uncovered_user_identifiers(
    input_text: str,
    collected: list[GovernedCapabilityAttempt] | tuple[GovernedCapabilityAttempt, ...],
) -> list[str]:
    """Identifiers named by the user that no business observation roots.

    Generic coverage hint for the model. Does not choose the next tool.
    """
    found = list(
        dict.fromkeys(_IDENTIFIER_LITERAL_RE.findall(input_text or ""))
    )
    covered: set[str] = set()
    for attempt in collected:
        if not _is_business_evidence_attempt(attempt):
            continue
        covered.update(
            item.casefold() for item in _attempt_identifier_roots(attempt)
        )
    return [item for item in found if item.casefold() not in covered]


# Alphanumeric record-like codes that slip past ``_IDENTIFIER_LITERAL_RE``
# (e.g. ``P12345``) — letter/digit mixes with a numeric run, never plain
# filter adjectives like ``ativos``.
_RECORD_CODEY_RE = re.compile(
    r"(?:"
    r"[A-Za-z]+\d{3,}[A-Za-z\d]*"
    r"|"
    r"\d{3,}[A-Za-z]+[A-Za-z\d]*"
    r")"
)


_NON_USER_PRIOR_KIND_TOKENS = frozenset(
    {
        "delia_result",
        "assistant",
        "system",
        "tool",
        "function",
        "model",
        "agent",
        "developer",
    }
)


def _prior_turn_is_user_authorized(turn: object) -> bool:
    """True when the turn may authorize record identifiers (R6).

    The real contract is ``ConversationContextTurn.kind`` /
    ``TurnKind`` (``USER_INPUT`` vs ``DELIA_RESULT``). Provider-style
    ``role``/``speaker`` appear only in harness fixtures — accepted as
    a secondary signal, never as a substitute that ignores ``kind``.
    Unknown shapes fail closed (do not authorize).
    """
    if isinstance(turn, str):
        # Bare strings are harness fixtures treated as user text.
        return bool(turn.strip())
    kind = getattr(turn, "kind", None)
    if kind is TurnKind.USER_INPUT:
        return True
    if kind is TurnKind.DELIA_RESULT:
        return False
    if isinstance(turn, Mapping):
        raw_kind = turn.get("kind")
        if raw_kind is not None:
            token = str(
                getattr(raw_kind, "value", raw_kind) or ""
            ).strip().casefold()
            if token == "user_input":
                return True
            if token in _NON_USER_PRIOR_KIND_TOKENS:
                return False
        role = str(
            turn.get("role") or turn.get("speaker") or ""
        ).strip().casefold()
        if role in {"user", "human"}:
            return True
        if role in _NON_USER_PRIOR_KIND_TOKENS:
            return False
        # Mapping without kind/role: fail closed.
        return False
    role = str(
        getattr(turn, "role", None)
        or getattr(turn, "speaker", None)
        or ""
    ).strip().casefold()
    if role in {"user", "human"}:
        return True
    if role in _NON_USER_PRIOR_KIND_TOKENS:
        return False
    # Legacy role-less objects with content only (unit fixtures): keep
    # authorizing so historical harness turns without kind still work.
    content = str(
        getattr(turn, "content", None)
        or getattr(turn, "text", "")
        or ""
    )
    return bool(content.strip()) and kind is None


def _context_turn_text(turn: object) -> str:
    if isinstance(turn, str):
        return turn
    if isinstance(turn, Mapping):
        return str(turn.get("content") or turn.get("text") or "")
    return str(
        getattr(turn, "content", None)
        or getattr(turn, "text", "")
        or ""
    )


def _prior_turns_blob(prior_turns: object) -> str:
    """Authorized user-context text from prior turns (R6).

    Only ``USER_INPUT`` (and legacy user-role / role-less harness turns)
    may authorize record identifiers. ``DELIA_RESULT`` and
    assistant/tool/system content never expand the authorized set — a
    model-invented code in an earlier result turn must not legitimize
    the same fabrication later.
    """
    parts: list[str] = []
    for turn in prior_turns or ():
        if not _prior_turn_is_user_authorized(turn):
            continue
        content = _context_turn_text(turn)
        if content:
            parts.append(content)
    return " ".join(parts)


def _prior_turn_is_grounded_result(turn: object) -> bool:
    """Whether a prior turn is a server-grounded DELIA result.

    The grounded read path stamps evidence-carrying results with
    ``EpistemicClass.OBSERVATION`` (plus provenance); ungrounded model
    prose (hypotheses, clarifications, fabricated candidates) carries
    other classes. Presence of an identifier here means coverage only
    — never authority: re-validation stays with live Core/Domain.
    """
    if isinstance(turn, str):
        return False
    if isinstance(turn, Mapping):
        kind = str(
            turn.get("kind") or turn.get("role") or ""
        ).upper()
        epistemic = str(turn.get("epistemic_class") or "").upper()
        return (
            kind == TurnKind.DELIA_RESULT.value
            and epistemic == EpistemicClass.OBSERVATION.value
        )
    kind = getattr(turn, "kind", None)
    kind_token = str(
        getattr(kind, "value", kind) or ""
    ).strip().casefold()
    if kind_token != TurnKind.DELIA_RESULT.value.casefold():
        return False
    epistemic = getattr(turn, "epistemic_class", None)
    epistemic_token = str(
        getattr(epistemic, "value", epistemic) or ""
    ).strip().casefold()
    return epistemic_token == EpistemicClass.OBSERVATION.value.casefold()


def _prior_turns_presence_blob(prior_turns: object) -> str:
    """Prior-turn content where an identifier counts as on the table.

    ``USER_INPUT`` (and legacy user-role / role-less) turns always
    count — the user authored the identifier. ``DELIA_RESULT`` turns
    count only when server-grounded (OBSERVATION): asking the user to
    re-confirm an identifier from real owner evidence is redundant,
    while a candidate the model itself emitted ungrounded stays a
    legitimate clarification target.
    """
    parts: list[str] = []
    for turn in prior_turns or ():
        if not (
            _prior_turn_is_user_authorized(turn)
            or _prior_turn_is_grounded_result(turn)
        ):
            continue
        content = _context_turn_text(turn)
        if content:
            parts.append(content)
    return " ".join(parts)


def invented_record_tokens(
    candidates: object,
    *,
    input_text: str,
    prior_turns: object = (),
) -> list[str]:
    """Record-shaped tokens absent from the authorized user context.

    Used to reject goal declarations that invent product/process codes
    when the user (and prior turns) never named them — forces
    clarification instead of a fabricated lookup (R6).
    """
    blob = f"{input_text or ''} {_prior_turns_blob(prior_turns)}"
    present = set(_IDENTIFIER_LITERAL_RE.findall(blob))
    blob_cf = blob.casefold()
    invented: list[str] = []
    seen: set[str] = set()
    for raw in candidates or ():
        token = str(raw or "").strip()
        if not token or token.casefold() in seen:
            continue
        # Angle-bracket placeholders (e.g. ``<código_do_produto>``) are
        # never user-named identifiers — treat as invented.
        is_placeholder = token.startswith("<") and token.endswith(">")
        is_literal = bool(_IDENTIFIER_LITERAL_RE.fullmatch(token))
        is_codey = bool(_RECORD_CODEY_RE.fullmatch(token))
        if not (is_placeholder or is_literal or is_codey):
            continue
        if (
            not is_placeholder
            and (token in present or token.casefold() in blob_cf)
        ):
            continue
        seen.add(token.casefold())
        invented.append(token)
    return invented


def omitted_context_identifiers(
    declared_tokens: object,
    *,
    input_text: str,
    prior_turns: object = (),
) -> list[str]:
    """User-context record identifiers the declared plan drops.

    The inverse direction of ``invented_record_tokens``: an
    identifier literal the user named in this turn or a
    user-authorized prior turn must appear somewhere in the declared
    contract (targets, required scope leaves, obligation
    descriptions, business subject) — a plan that omits it silently
    narrows the objective before the typed handoff (INT-2 functional
    completion). Same authorized-context basis as the invented
    check: ungrounded model prose never counts as user-named.
    """
    blob = f"{input_text or ''} {_prior_turns_blob(prior_turns)}"
    context = _IDENTIFIER_LITERAL_RE.findall(blob)
    if not context:
        return []
    declared_blob = " ".join(
        str(item or "") for item in declared_tokens or ()
    ).casefold()
    return sorted(
        token
        for token in dict.fromkeys(context)
        if token.casefold() not in declared_blob
    )


def _obligation_scope_tokens(evidence_needed: object) -> list[str]:
    """Collect nested string leaves from obligation ``required_args``."""
    tokens: list[str] = []

    def _walk(node: object) -> None:
        if isinstance(node, Mapping):
            for value in node.values():
                _walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)
        elif isinstance(node, str) and node.strip():
            tokens.append(node.strip())

    for item in evidence_needed or ():
        if isinstance(item, Mapping):
            _walk(item.get("required_args"))
        else:
            req = getattr(item, "required_args", None)
            if req is not None:
                _walk(req)
    return tokens


def focus_arguments_on_next_identifier(
    arguments: Mapping[str, Any] | None,
    *,
    input_text: str,
    collected: list[GovernedCapabilityAttempt] | tuple[GovernedCapabilityAttempt, ...],
    declared_properties: Container[str] | None = None,
) -> dict[str, Any]:
    """Narrow a multi-identifier query to the next uncovered literal.

    The agent already chose the tool. When its query still names
    several identifiers from the user text, the owner schema that
    accepts one identifier at a time would otherwise repeat the same
    miss. Identifiers are copied from the user text only.

    ``declared_properties`` is the tool's published top-level field
    set: the focused literal may only be written into ``query`` when
    the owner schema actually declares it — injecting an undeclared
    top-level field would make DÉLIA reject its own mutation.
    """
    args = dict(arguments or {})
    uncovered = uncovered_user_identifiers(input_text, collected)
    if not uncovered:
        return args
    source = str(args.get("query") or "").strip() or (input_text or "").strip()
    query_ids = list(dict.fromkeys(_IDENTIFIER_LITERAL_RE.findall(source)))
    uncovered_keys = {item.casefold() for item in uncovered}
    if (
        len(query_ids) == 1
        and query_ids[0].casefold() in uncovered_keys
    ):
        return args
    if len(query_ids) == 0:
        return args
    keep = uncovered[0]
    keep_keys = {keep.casefold()}
    # A repeated already-covered identifier is retargeted to the next
    # uncovered literal. Wording around it stays; values come only
    # from identifiers the user already named.
    if len(query_ids) == 1:
        keep_keys.add(query_ids[0].casefold())
    narrowed = _IDENTIFIER_LITERAL_RE.sub(
        lambda match: keep
        if match.group(0).casefold() in keep_keys
        else "",
        source,
    )
    narrowed = " ".join(narrowed.split())
    if narrowed and (
        declared_properties is None or "query" in declared_properties
    ):
        args["query"] = narrowed
    return args


def _invocation_fingerprint(
    capability_id: str, arguments: Mapping[str, Any]
) -> str:
    canonical = json.dumps(
        arguments, sort_keys=True, ensure_ascii=False, default=str
    )
    return f"{capability_id}\x00{canonical}"


def _close_investigation_client(model: Any) -> None:
    """Close the HTTP client created for this turn.

    The shared test model is left untouched. A factory-built provider
    owns an AsyncOpenAI client whose lock must not leak into the next
    event loop.
    """
    provider = getattr(model, "_provider", None)
    client = getattr(provider, "client", None) if provider is not None else None
    closer = getattr(client, "close", None)
    if not callable(closer):
        return
    try:
        result = closer()
    except Exception:
        _logger.info(
            "orchestration engine=pydantic_ai "
            "stage=investigation decision=client_close_failed"
        )
        return
    if not asyncio.iscoroutine(result):
        return
    try:
        asyncio.run(result)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(result)
        finally:
            loop.close()


def _prior_message_history(
    prior_turns: tuple[ConversationContextTurn, ...],
    *,
    turns_limit: int = _DEFAULT_PRIOR_TURNS_LIMIT,
):
    """Native ``message_history`` for continuity — untrusted context,
    never authority (doc 272 §4).

    ``ConversationContextTurn.kind`` maps to the native message type:
    ``USER_INPUT`` → ``ModelRequest(UserPromptPart)``;
    ``DELIA_RESULT`` → ``ModelResponse(TextPart)``. Other kinds are
    skipped rather than speculatively converted.
    """
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        TextPart,
        UserPromptPart,
    )
    if not prior_turns or turns_limit <= 0:
        return []
    history = []
    for turn in prior_turns[-turns_limit:]:
        content = str(getattr(turn, "content", "") or "").strip()
        if not content:
            continue
        kind = getattr(turn, "kind", None)
        if kind is TurnKind.USER_INPUT:
            history.append(
                ModelRequest(parts=[UserPromptPart(content)])
            )
        elif kind is TurnKind.DELIA_RESULT:
            history.append(
                ModelResponse(parts=[TextPart(content)])
            )
    return history


def _investigation_model_settings(
    max_output_tokens: int | None = None,
):
    """Model settings for the investigation run — ``extra_body``
    ``chat_template_kwargs.enable_thinking=False`` disables qwen3
    ``<think>`` reasoning which otherwise consumes generation budget
    and corrupts the strict structured output under full context.
    Providers without this kwarg ignore it. ``max_tokens`` carries
    the runtime-profile generation budget — without it the provider
    sees an unbounded request (model context size) and may reject it
    (openrouter 402)."""
    from pydantic_ai.models.openai import OpenAIChatModelSettings

    return OpenAIChatModelSettings(
        max_tokens=max_output_tokens,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False}
        },
    )


class _InvestigationHistoryIntegrityError(Exception):
    """Malformed native history — orphan/mismatched tool results must
    never be attached to an unrelated unit or treated as valid
    business evidence (doc 274 §2)."""


def _history_units(messages):
    """Complete causal units (doc 272/274): a ModelRequest containing
    ToolReturnParts joins the preceding unit ONLY when that unit's
    ModelResponses issued matching ``ToolCallPart``s — matched by
    ``tool_call_id`` (fallback ``tool_name``) for EVERY return part.
    An orphan or mismatched return raises
    ``_InvestigationHistoryIntegrityError`` — never attached to an
    unrelated user prompt, never relabeled valid evidence."""
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        ToolCallPart,
        ToolReturnPart,
    )

    units = []
    for msg in messages:
        returns = (
            [p for p in msg.parts if isinstance(p, ToolReturnPart)]
            if isinstance(msg, ModelRequest)
            else []
        )
        if returns and units:
            calls = [
                p
                for prior in units[-1]
                if isinstance(prior, ModelResponse)
                for p in prior.parts
                if isinstance(p, ToolCallPart)
            ]
            call_ids = {c.tool_call_id for c in calls}
            # Explicit IDs are the pairing key — a name match never
            # rescues a divergent explicit ID (doc 275 §2). Name-only
            # matching applies solely when the return lacks an
            # explicit id and exactly one call by that name exists.
            seen_return_ids: set[str] = set()
            for r in returns:
                rid = getattr(r, "tool_call_id", None)
                if rid:
                    if rid in seen_return_ids:
                        raise _InvestigationHistoryIntegrityError(
                            f"duplicate tool_return id {rid!r}"
                        )
                    seen_return_ids.add(rid)
                    if rid not in call_ids:
                        raise _InvestigationHistoryIntegrityError(
                            f"tool_return id {rid!r} matches no call"
                        )
                    continue
                candidates = [
                    c for c in calls if c.tool_name == r.tool_name
                ]
                if len(candidates) != 1:
                    raise _InvestigationHistoryIntegrityError(
                        "tool_return without explicit id is not "
                        f"uniquely matchable ({r.tool_name!r})"
                    )
            units[-1].append(msg)
            continue
        if returns:
            raise _InvestigationHistoryIntegrityError(
                "tool_return with no preceding unit"
            )
        units.append([msg])
    return units


def _estimate_history_tokens(messages):
    """ESTIMATED tokens — text content of message parts via the
    existing heuristic; never claimed as measured provider usage
    (doc 272 §3)."""
    from app.application.model_invocation.context_budget import (
        estimate_text_tokens,
    )

    return sum(
        estimate_text_tokens(
            str(getattr(p, "content", "") or str(p)[:400])
        )
        for m in messages
        for p in m.parts
    )


def _select_surviving_messages(messages, window: int):
    """Compaction policy (doc 273): the CURRENT objective is the
    suffix starting at the last user-prompt unit — never presume
    units[0] is current (it may be old prior conversation). Earlier
    units drop oldest-first as WHOLE units; if the mandatory
    current-turn suffix alone exceeds the window, raise
    ``_InvestigationContextOverflow`` — never discard the current
    question or fabricate."""
    from pydantic_ai.messages import ModelRequest, UserPromptPart

    units = _history_units(messages)
    current_idx = 0
    for idx, unit in enumerate(units):
        head = unit[0]
        if isinstance(head, ModelRequest) and any(
            isinstance(p, UserPromptPart) for p in head.parts
        ):
            current_idx = idx
    droppable = list(units[:current_idx])
    mandatory = list(units[current_idx:])
    while droppable and (
        _estimate_history_tokens(
            [m for u in droppable + mandatory for m in u]
        )
        > window
    ):
        droppable.pop(0)
    flat = [m for u in droppable + mandatory for m in u]
    if _estimate_history_tokens(flat) > window:
        raise _InvestigationContextOverflow(
            f"mandatory context > window ({window})"
        )
    return flat


class _InvestigationContextOverflow(Exception):
    """Mandatory context exceeds the configured window — fail closed."""


def build_test_investigation_model():
    """Deterministic framework test model — test composition only."""
    from pydantic_ai.models.test import TestModel

    return TestModel()


class PydanticAiInvestigationOrchestrator:
    """``SupportsGovernedCapabilityAttempt`` via Pydantic AI tools.

    Deterministic stages (confirmation, admission, surface inquiry)
    remain Application gates. The former owner-path semantic
    selection/sequencing engine was removed (doc 241).
    """

    def __init__(
        self,
        gates: SupportsGovernedStageGates,
        *,
        model: Any = None,
        model_factory: Callable[[], Any] | None = None,

        request_limit: int = _DEFAULT_REQUEST_LIMIT,
        tool_calls_limit: int = _DEFAULT_TOOL_CALL_LIMIT,
        agent_retries: int = _DEFAULT_AGENT_RETRIES,
        tool_projection_limit: int = _DEFAULT_TOOL_PROJECTION_LIMIT,
        prior_turns_limit: int = _DEFAULT_PRIOR_TURNS_LIMIT,
        context_window_tokens: int | None = None,
        max_output_tokens: int | None = None,
        two_agent_experiment: bool = False,
    ) -> None:
        if model is None and model_factory is None:
            raise ValueError("investigation model is required")
        self._gates = gates
        self._model = model
        self._model_factory = model_factory
        self._request_limit = max(1, int(request_limit))
        self._tool_calls_limit = max(1, int(tool_calls_limit))
        self._agent_retries = max(0, int(agent_retries))
        self._tool_projection_limit = max(
            500, int(tool_projection_limit)
        )
        self._prior_turns_limit = max(0, int(prior_turns_limit))
        self._context_window_tokens = (
            int(context_window_tokens)
            if context_window_tokens
            else None
        )
        self._max_output_tokens = (
            int(max_output_tokens)
            if max_output_tokens
            else None
        )
        # Experimental split Comprehension × Investigação
        # (DELIA_TWO_AGENT_EXPERIMENT, doc 293/335 gate): OFF is the
        # productive baseline A; ON runs a dedicated comprehension
        # Agent whose only tool surface is the typed goal declaration
        # + clarification, validated by the SAME Application acceptor.
        self._two_agent_experiment = bool(two_agent_experiment)
        self.last_node_trace: list[str] = []

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
        thread_id: str | None = None,
    ) -> GovernedCapabilityAttempt:
        del thread_id  # durable graph resume retired with LangGraph

        def attempt_once(
            correlation: str, deadline: TurnDeadline
        ) -> GovernedCapabilityAttempt:
            return self._attempt_once(
                input_text,
                correlation=correlation,
                actor_user_id=actor_user_id,
                session_id=session_id,
                confirmation=confirmation,
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                prepare_only=max_execution_stage == "prepare",
                deadline=deadline,
            )

        return self._gates._run_governed_attempts(
            attempt_once,
            correlation_id=correlation_id,
            confirmation=confirmation,
            activity_sink=activity_sink,
            cancel_check=cancel_check,
            turn_deadline=turn_deadline,
        )

    def _attempt_once(
        self,
        input_text: str,
        *,
        correlation: str,
        actor_user_id: str | None,
        session_id: str | None,
        confirmation: Mapping[str, Any] | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        prepare_only: bool,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt:
        trace: list[str] = []
        deadline.check("turn_start")
        _emit_activity(
            phase=ActivityPhase.CONTEXTUALIZING, correlation=correlation
        )
        trace.append("preflight")

        if confirmation is not None:
            trace.append("confirmation")
            attempt = self._gates._attempt_confirmation(
                confirmation,
                actor_user_id=actor_user_id,
                correlation=correlation,
                prepare_only=prepare_only,
                deadline=deadline,
            )
            self.last_node_trace = trace
            return attempt

        admission_class, admission_owner_required = (
            self._gates._admit_conversational_turn(
                input_text,
                workspace_context=workspace_context,
                prior_turns=prior_turns,
                correlation=correlation,
                deadline=deadline,
            )
        )
        trace.append("admission")
        unbound_outcome = (
            OWNER_PATH_UNBOUND if admission_owner_required else None
        )

        if admission_class == "surface_inquiry":
            groups, failures = self._gates._groups(correlation, deadline)
            attempt = self._gates._surface_inquiry_attempt(
                groups, failures, correlation
            )
            trace.append("surface_inquiry")
            self.last_node_trace = trace
            return attempt

        if admission_class is not None:
            _logger.info(
                "orchestration engine=pydantic_ai "
                "stage=interaction_admission decision=conversational "
                "class=%s correlation_id=%s",
                admission_class,
                correlation,
            )
            trace.append("conversational")
            self.last_node_trace = trace
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=EARLY_CONVERSATIONAL_ADMISSION,
            )

        trace.append("investigation")
        attempt = self._run_agent_investigation(
            input_text,
            correlation=correlation,
            actor_user_id=actor_user_id,
            session_id=session_id,
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            prepare_only=prepare_only,
            unbound_outcome=unbound_outcome,
            deadline=deadline,
        )
        extra = [
            item
            for item in self.last_node_trace
            if isinstance(item, str) and item.startswith("assessment_")
        ]
        self.last_node_trace = trace + extra
        return attempt

    def _run_agent_investigation(
        self,
        input_text: str,
        *,
        correlation: str,
        actor_user_id: str | None,
        session_id: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        prepare_only: bool,
        unbound_outcome: str | None,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt:
        os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
        from pydantic_ai import Agent, ModelRetry, RunContext, UsageLimits
        from pydantic_ai.toolsets import FunctionToolset

        deps = InvestigationDeps(
            gates=self._gates,
            input_text=input_text,
            correlation=correlation,
            actor_user_id=actor_user_id,
            session_id=session_id,
            workspace_context=workspace_context,
            prior_turns=prior_turns,
            prepare_only=prepare_only,
            unbound_outcome=unbound_outcome,
            deadline=deadline,
            tool_projection_limit=self._tool_projection_limit,
        )
        toolset = FunctionToolset()
        # Variant B (DELIA_TWO_AGENT_EXPERIMENT): the typed goal
        # declaration lives on a dedicated comprehension toolset —
        # the investigation Agent never sees declare_investigation_goal,
        # so the objective can only come from the accepted handoff.
        # Baseline A keeps the same single toolset as before.
        comprehension_toolset = (
            FunctionToolset() if self._two_agent_experiment else None
        )
        declare_toolset = (
            comprehension_toolset
            if comprehension_toolset is not None
            else toolset
        )

        def _proj(payload):
            """Tool-result projection bounded by the runtime-config
            snapshot (doc 243) — one source for the char budget."""
            return _bounded_json(
                payload, limit=deps.tool_projection_limit
            )

        def _governed_invoke(
            ctx,
            *,
            capability_id: str,
            arguments: dict[str, Any] | None,
        ) -> str:
            ctx.deps.deadline.check("tool_invoke_capability")
            ctx.deps.tool_calls += 1
            # Typed-argument gate (proven defect, diagnostic task):
            # object/array-typed parameters serialized as strings
            # reached the owner untouched — filters were silently
            # ignored (unfiltered dumps → retries → tool_calls_limit).
            # Reject BEFORE the governed invoke with a native
            # recoverable ModelRetry; never parse/coerce the string.
            declared = _schema_arg_types.get(
                str(capability_id or "").strip(), {}
            )
            _logger.info(
                "orchestration engine=pydantic_ai stage=investigation "
                "decision=arg_type_gate capability=%s declared=%s "
                "args=%s correlation_id=%s",
                capability_id,
                declared,
                {
                    k: type(v).__name__
                    for k, v in (arguments or {}).items()
                }
                if isinstance(arguments, dict)
                else type(arguments).__name__,
                ctx.deps.correlation,
            )
            inner_args = (
                arguments.get("arguments")
                if (
                    isinstance(arguments, dict)
                    and isinstance(
                        arguments.get("arguments"), Mapping
                    )
                )
                else arguments
            )
            bad_types = [
                name
                for name, value in (
                    inner_args.items()
                    if isinstance(inner_args, Mapping)
                    else ()
                )
                if isinstance(value, str)
                and _declared_container_only(declared.get(name))
            ]
            # Schema-free shape check: published owner schemas
            # sometimes leave params untyped, so a serialized dict
            # repr ("{'a': 1}") can reach the wire undeclared — no
            # contract to reject against. A braces-shaped string is
            # almost always model serialization leakage; flag every
            # occurrence — ModelRetry here is already bounded by the
            # agent's native tool-retry budget (no local flag needed:
            # a per-run flag let subsequent bad calls slip through).
            if not bad_types:
                suspects = [
                    name
                    for name, value in (
                        inner_args.items()
                        if isinstance(inner_args, Mapping)
                        else ()
                    )
                    if isinstance(value, str)
                    and _LOOKS_LIKE_DICT_REPR.match(value.strip())
                ]
                if suspects:
                    raise ModelRetry(
                        f"arguments {suspects} look like serialized "
                        "dict strings — pass real JSON objects, not "
                        "string representations."
                    )
            if bad_types:
                raise ModelRetry(
                    f"arguments {bad_types} must be real JSON "
                    "objects/arrays as declared in the tool schema, "
                    "not serialized strings — pass structured values."
                )
            cap_key = str(capability_id or "").strip()
            catalog_entry = next(
                (
                    entry
                    for entry in live_catalog
                    if isinstance(entry, Mapping)
                    and str(entry.get("capability_id") or "") == cap_key
                ),
                None,
            )
            op_class = None
            if isinstance(catalog_entry, Mapping):
                raw_op = catalog_entry.get("operation_class")
                if isinstance(raw_op, str) and raw_op.strip():
                    op_class = raw_op.strip()
            if (
                ctx.deps.investigation_plan is None
                and op_class != "DISCOVERY"
            ):
                # INT-3 R1 governed pre-invocation boundary: an owner
                # call whose operation class produces business evidence
                # (READ/ANALYSIS/unknown — anything other than the
                # owner-published DISCOVERY class) must not execute
                # while no typed objective is accepted; the projection
                # would carry no evaluable coverage. ModelRetry is the
                # same bounded, native recovery the arg-type gate uses:
                # the model declares via declare_investigation_goal and
                # reissues this call through the identical governed
                # path — never a fabricated plan, never a cached
                # invocation. Discovery-class calls stay exempt so the
                # model can identify capabilities before declaring.
                # The classification grants no permission — AuthZ,
                # Policy and Domain checks still run on every call.
                raise ModelRetry(
                    f"Call to {cap_key} was not executed — a typed "
                    "investigation goal has not been declared yet, "
                    "so no owner was contacted. Do not reissue this "
                    "call before the goal is accepted: it will be "
                    "rejected again and consume your retry budget. "
                    "Call declare_investigation_goal once now with "
                    "goal_class, expected_delivery and "
                    "evidence_needed describing the user's "
                    "objective; after the declaration is accepted, "
                    "reissue this same call unchanged."
                )
            _schema_props = (
                (catalog_entry.get("input_schema") or {}).get(
                    "properties"
                )
                if isinstance(catalog_entry, Mapping)
                and isinstance(catalog_entry.get("input_schema"), Mapping)
                else None
            )
            raw_args = focus_arguments_on_next_identifier(
                arguments if isinstance(arguments, dict) else {},
                input_text=ctx.deps.input_text,
                collected=ctx.deps.collected,
                declared_properties=(
                    _schema_props if isinstance(_schema_props, Mapping) else None
                ),
            )
            focused_query = str(raw_args.get("query") or "").strip()
            invoke_text = focused_query or ctx.deps.input_text
            fingerprint = _invocation_fingerprint(cap_key, raw_args)
            previous = ctx.deps.non_progress_calls.get(fingerprint)
            if previous is not None and not (
                previous.get("error_code")
                and _listing_failure_is_transient(
                    str(previous.get("error_code") or "")
                )
                and fingerprint not in ctx.deps.transient_invoke_retries
            ):
                # Identical capability+arguments only — a material arg
                # change is a new fingerprint and must reach the owner.
                repeated = dict(previous)
                repeated["repeated_equivalent_call"] = True
                if not previous.get("authoritative_root_code"):
                    repeated["repeated_failure_no_progress"] = True
                    repeated["error_class"] = "repeated_equivalent_failure"
                    repeated["investigation_progress"] = (
                        INVESTIGATION_PROGRESS_NONE
                    )
                return _proj(repeated)
            if (
                previous is not None
                and previous.get("error_code")
                and _listing_failure_is_transient(
                    str(previous.get("error_code") or "")
                )
                and fingerprint not in ctx.deps.transient_invoke_retries
            ):
                ctx.deps.transient_invoke_retries.add(fingerprint)
            inner_keys = (
                ",".join(sorted(str(k) for k in raw_args["arguments"]))[
                    :200
                ]
                if isinstance(raw_args.get("arguments"), Mapping)
                else "-"
            )
            _logger.info(
                "orchestration engine=pydantic_ai "
                "stage=investigation decision=tool_call_args "
                "capability=%s outer_keys=%s inner_keys=%s "
                "correlation_id=%s",
                capability_id,
                ",".join(sorted(str(k) for k in raw_args))[:200],
                inner_keys,
                ctx.deps.correlation,
            )
            attempt = ctx.deps.gates._governed_semantic_tool_invoke(
                capability_id=cap_key,
                arguments=raw_args,
                input_text=invoke_text,
                correlation=ctx.deps.correlation,
                actor_user_id=ctx.deps.actor_user_id,
                session_id=ctx.deps.session_id,
                workspace_context=ctx.deps.workspace_context,
                prior_turns=ctx.deps.prior_turns,
                prepare_only=ctx.deps.prepare_only,
                deadline=ctx.deps.deadline,
            )
            ctx.deps.collected.append(attempt)
            index = len(ctx.deps.collected) - 1
            # Uncovered identifiers AFTER this observation — used both
            # for progress classification and Agent coverage hints.
            uncovered = uncovered_user_identifiers(
                ctx.deps.input_text, ctx.deps.collected
            )
            pagination_args = (
                _schema_pagination_arg_names(
                    catalog_entry.get("input_schema")
                )
                if isinstance(catalog_entry, Mapping)
                else ()
            )
            projection = _attempt_projection(
                attempt,
                observation_index=index,
                uncovered_after=uncovered,
                plan=ctx.deps.investigation_plan,
                operation_class=op_class,
                prior_content_fingerprints=(
                    ctx.deps.observed_content_fingerprints
                ),
                capability_id=cap_key,
                pagination_args=pagination_args,
            )
            content_fp = observation_content_fingerprint(attempt)
            if content_fp is not None:
                if content_fp in ctx.deps.observed_content_fingerprints:
                    projection["repeated_observation_no_progress"] = True
                    projection["investigation_progress"] = (
                        INVESTIGATION_PROGRESS_NONE
                    )
                else:
                    ctx.deps.observed_content_fingerprints.add(content_fp)
            _logger.info(
                "orchestration engine=pydantic_ai "
                "stage=investigation decision=tool_observed "
                "capability=%s action=%s root=%s uncovered=%s "
                "progress=%s status=%s error=%s correlation_id=%s",
                capability_id,
                projection.get("action_id"),
                projection.get("authoritative_root_code"),
                ",".join(uncovered[:8]),
                projection.get("investigation_progress"),
                attempt.status.value if attempt.status else "-",
                attempt.error_code or "-",
                ctx.deps.correlation,
            )
            ctx.deps.non_progress_calls[fingerprint] = dict(projection)
            if attempt.error_code == OWNER_ARGUMENT_REJECTED:
                hint = projection.get("owner_validation_hint") or (
                    "owner rejected the proposed arguments"
                )
                # One-shot native recovery with owner feedback. Further
                # calls with *different* arguments still invoke; only the
                # identical fingerprint short-circuit above prevents loops.
                if not ctx.deps.owner_argument_retry_used:
                    ctx.deps.owner_argument_retry_used = True
                    raise ModelRetry(
                        f"Owner rejected arguments: {hint}. "
                        "Rebuild arguments from the published tool "
                        "schema and any owner_validation_hint — do not "
                        "resubmit an equivalent rejected payload."
                    )
            # Continuity: NO_PROGRESS with open identifiers must not
            # silently become an unrelated specialist tour. One-shot
            # ModelRetry re-asks for semantic re-selection — never
            # names an owner or hardcodes a capability. AUTHZ_DENIED
            # is excluded: never encourage bypass of a denial.
            if continuity_model_retry_allowed(
                attempt=attempt,
                investigation_progress=projection.get(
                    "investigation_progress"
                ),
                uncovered=uncovered,
                already_used=ctx.deps.no_progress_continuity_retry_used,
                under_tool_limit=(
                    ctx.deps.tool_calls < self._tool_calls_limit
                ),
            ):
                ctx.deps.no_progress_continuity_retry_used = True
                raise ModelRetry(
                    "Observation made no progress on open user "
                    "identifiers. Preserve the original objective. "
                    "Select a different live capability whose "
                    "description and schema match the still-missing "
                    "business evidence — do not repeat an equivalent "
                    "call or treat guidance/documentation as "
                    "operational records."
                )
            return _proj(projection)

        # Prefetch live catalog once so each capability is a native tool.
        # AuthZ is re-checked on every invoke; catalog metadata is never
        # permission. Empty catalog → agent runs with no owner tools.
        live_catalog = self._gates._project_semantic_tool_catalog(
            correlation=correlation,
            deadline=deadline,
            actor_user_id=actor_user_id,
        )
        catalog_failures = tuple(_LAST_CATALOG_FAILURES.get())
        _schema_arg_types = {
            str(entry.get("capability_id")): {
                str(name): (
                    spec.get("type")
                    if isinstance(spec, Mapping)
                    else None
                )
                for name, spec in (
                    (entry.get("input_schema") or {}).get(
                        "properties"
                    )
                    or {}
                ).items()
            }
            for entry in live_catalog
            if isinstance(entry, Mapping)
        }
        selected_instructions = load_selected_investigation_instructions()
        instructions = selected_instructions.text
        instruction_version = selected_instructions.instruction_version
        # Legacy DELIA_INSTRUCTION_VARIANT=v42-experimental is retired:
        # recovery/progress guidance lives in versioned candidates
        # (e.g. generalist-semantic-v3-objective-progress), not inline.
        if catalog_failures:
            instructions += (
                "\nOwners that failed to enumerate this turn "
                "(unavailable, not an authorization denial, not proof "
                "they have no capabilities): "
                + ", ".join(catalog_failures)
                + ".\n"
            )
        prior_blob = " ".join(
            str(
                getattr(turn, "content", None)
                or getattr(turn, "text", "")
                or ""
            )
            for turn in prior_turns
        )
        if not _IDENTIFIER_LITERAL_RE.search(
            input_text or ""
        ) and not _IDENTIFIER_LITERAL_RE.search(prior_blob):
            instructions += (
                "\nThe user did not name an identifier and prior turns "
                "do not either. If the request depends on a specific "
                "record, call request_user_clarification before "
                "spending owner tools.\n"
            )
        import hashlib as _hashlib

        # Fingerprint the *effective* prompt text (base version + any
        # runtime appends such as catalog failures / identifier gate).
        instruction_fingerprint = _hashlib.sha256(
            instructions.encode("utf-8")
        ).hexdigest()[:16]
        _logger.info(
            "orchestration engine=pydantic_ai "
            "stage=investigation decision=dynamic_toolset "
            "catalog_len=%d instruction_version=%s "
            "instruction_base_fingerprint=%s "
            "instruction_fingerprint=%s correlation_id=%s",
            len(live_catalog),
            instruction_version,
            selected_instructions.text_fingerprint,
            instruction_fingerprint,
            correlation,
        )

        @declare_toolset.tool
        def declare_investigation_goal(
            ctx,
            goal_class: str,
            comparison_requested: bool = False,
            target_identities: list[str] | None = None,
            evidence_needed: (
                list[str | ObligationProposal] | None
            ) = None,
            business_subject: str = "",
            expected_delivery: str = "unspecified",
        ) -> str:
            """Typed investigation goal declaration (INT-2/RC5).

            Declare the user's objective, the expected delivery and the
            material evidence obligations before or alongside the first
            business-evidence call so coverage can be evaluated at
            finalize. ``goal_class`` is one of: read, analyze, compare,
            create_or_modify, clarify. ``expected_delivery`` is one of:
            enumeration, aggregation, explanation, record_detail,
            comparison, unspecified — choose ``aggregation`` when the
            user asks how many/how much/a total (the owner-declared
            metric is the deliverable, even when records are paged);
            choose ``enumeration`` only when the user asks to see the
            records themselves. ``evidence_needed`` names the
            material obligations derived from the objective —
            collection coverage for enumeration, metric+scope for
            aggregation, pertinent facts for explanation. Each item is
            a plain obligation text OR a typed object
            ``{"description": ..., "evidence_source": ...,
            "operation": ..., "required_args": ...}``:
            ``evidence_source`` anchors the
            obligation to the live owner vocabulary (an entity,
            action or capability token the owner echoes in results or
            that you pass as an invocation selector — e.g.
            ``get_product_structure`` or ``process``); ``operation``
            requires a specific operation class (read, analysis,
            prepare, act, discovery) and is a restriction only, never
            a pertinence proof. ``required_args`` declares the material
            business scope the USER asked for — filters, identities,
            units or periods under the published argument carrier, e.g.
            ``{"params": {"status": "ativo"}}`` for "processos ativos"
            or ``{"params": {}}`` only when the objective requires the
            explicitly unfiltered set: a query carrying a contradictory
            filter, missing the declared one, or adding an extra
            business argument inside the declared container cannot
            demonstrate the obligation. It is NOT a mirror of the call
            you plan to make: never declare presentation/viewport
            selectors (``view``, ``format``, ``display``, ``layout``) —
            they freeze a capability's rendering into a restriction no
            other governed capability can echo and are rejected; a
            demanded presentation belongs in ``evidence_source`` or the
            description. Declare only the filters the user's request
            actually requires.
            ``evidence_source`` is the owner-vocabulary VALUE you pass
            as the invocation selector in that same call's args — the
            ``entity``/``capability``/``action`` token such as
            ``process`` or ``get_product_structure`` — never the
            governed tool name: a dotted surface identifier
            (``{specialist}.{remote}``) is rejected with correction
            guidance naming the selector values you already declared.
            ``operation`` takes only an operation CLASS (read,
            analysis, prepare, act, discovery) — entity actions like
            ``search``/``get`` belong to the invocation args; omit
            ``operation`` unless the OBJECTIVE itself demands that
            operation kind (e.g. "analise…" → analysis): it restricts
            which capability classes may demonstrate the obligation,
            so a class you merely preferred as strategy silently
            disqualifies other capable capabilities. Under
            ``expected_delivery="aggregation"`` ``operation`` is
            rejected outright as non-material — the authoritative
            owner aggregate is the demonstration and any
            consultation-class invocation producing it qualifies.
            Anchored
            obligations are verified mechanically against
            owner-declared evidence metadata; unanchored text binds
            evidence but never proves pertinence. A declaration is a
            semantic proposal only — it never grants access or
            authorization. A goal may be declared once per turn.
            """
            ctx.deps.deadline.check("tool_declare_goal")
            ctx.deps.tool_calls += 1
            if ctx.deps.investigation_plan is not None:
                # Goal mutation after acceptance would let untrusted
                # mid-turn influence rewrite declared obligations — the
                # first valid declaration stands (INT-2 Case F).
                return _proj(
                    {
                        "status": "INVALID_GOAL",
                        "error_code": "investigation_goal_already_declared",
                    }
                )
            targets = (
                target_identities
                if isinstance(target_identities, list)
                else []
            )
            needed = (
                evidence_needed if isinstance(evidence_needed, list) else []
            )
            invented = invented_record_tokens(
                list(targets) + _obligation_scope_tokens(needed),
                input_text=ctx.deps.input_text,
                prior_turns=ctx.deps.prior_turns,
            )
            if invented:
                # Record codes absent from the user/prior context are
                # not material obligations — inventing them skips the
                # clarification ask-back (R6). Reject so the specialist
                # can call request_user_clarification instead.
                return _proj(
                    {
                        "status": "INVALID_GOAL",
                        "error_code": (
                            "investigation_target_not_in_user_context"
                        ),
                        "invented_record_tokens": invented[:8],
                        "guidance": (
                            "Do not invent product/process codes. When "
                            "the user did not name the record, call "
                            "request_user_clarification for the missing "
                            "identifier; declare targets only from the "
                            "user text or prior turns."
                        ),
                    }
                )
            omitted = omitted_context_identifiers(
                list(targets)
                + _obligation_scope_tokens(needed)
                + [
                    str(item.get("description") or "")
                    for item in needed
                    if isinstance(item, dict)
                ]
                + [
                    str(item)
                    for item in needed
                    if isinstance(item, str)
                ]
                + [str(business_subject or "")],
                input_text=ctx.deps.input_text,
                prior_turns=ctx.deps.prior_turns,
            )
            if omitted:
                # A user-named identifier absent from every declared
                # surface silently narrows the objective — the
                # accepted plan would hand the investigation an
                # objective missing material scope. Reject naming
                # the dropped identifiers so the bounded redeclare
                # carries them (INT-2 functional completion).
                return _proj(
                    {
                        "status": "INVALID_GOAL",
                        "error_code": (
                            "investigation_goal_omits_user_identifier"
                        ),
                        "missing_user_identifiers": omitted[:8],
                        "guidance": (
                            "The user named identifiers the plan does "
                            "not carry — include each in "
                            "target_identities, required_args or the "
                            "obligation description, or call "
                            "request_user_clarification when they are "
                            "out of scope for this objective."
                        ),
                    }
                )
            plan = ctx.deps.gates._accept_semantic_investigation_plan(
                goal_class=str(goal_class or ""),
                comparison_requested=bool(comparison_requested),
                target_identities=targets,
                evidence_needed=needed,
                business_subject=business_subject or None,
                expected_delivery=expected_delivery,
                correlation=ctx.deps.correlation,
            )
            if plan is None:
                # Owner-side schema feedback: echo the bounded
                # vocabularies so a wrong proposal can be corrected on
                # the next call instead of retried blindly.
                rejected: dict[str, Any] = {
                    "status": "INVALID_GOAL",
                    "error_code": "investigation_goal_rejected",
                    "valid_goal_classes": sorted(
                        ctx.deps.gates._GOAL_CLASSES
                    ),
                    "valid_expected_delivery": sorted(
                        ctx.deps.gates._DELIVERY_MODES
                    ),
                    "valid_operations": sorted(
                        _OBLIGATION_OPERATIONS
                    ),
                }
                surface_anchors = [
                    item.get("evidence_source")
                    for item in needed
                    if isinstance(item, dict)
                    and isinstance(item.get("evidence_source"), str)
                    and "." in item["evidence_source"]
                ]
                if surface_anchors:
                    # Dotted tokens name the governed transport surface
                    # ({specialist}.{remote}), never the owner evidence
                    # kind — bound only, never demonstrated (RC5-R1).
                    rejected["rejected_anchors"] = surface_anchors[:8]
                    rejected["anchor_guidance"] = (
                        "evidence_source must be a live owner "
                        "vocabulary token — the entity/action/"
                        "capability VALUE you pass as an invocation "
                        "selector in the owner call args (e.g. the "
                        "`entity` value), never the dotted envelope "
                        "tool name ({specialist}.{remote})."
                    )
                # Field-level diagnosis (INT-3 R1 declaration
                # reliability): a rejected plan echoes WHICH declared
                # fields are invalid so a correction fixes the actual
                # divergence instead of mutating a correct field —
                # real-eval qwen14b corrected the anchor while breaking
                # `operation` with an action token ("search"), burning
                # the bounded retry budget.
                invalid_ops = sorted(
                    {
                        str(item.get("operation"))
                        for item in needed
                        if isinstance(item, dict)
                        and isinstance(item.get("operation"), str)
                        and item["operation"].strip()
                        and item["operation"].strip().casefold()
                        not in _OBLIGATION_OPERATIONS
                    }
                )
                if invalid_ops:
                    rejected["invalid_operations"] = invalid_ops[:8]
                    rejected["operation_guidance"] = (
                        "operation must be an operation CLASS "
                        "(read, analysis, prepare, act, discovery) — "
                        "entity actions like 'search'/'get' belong to "
                        "the invocation args, not this field; omit "
                        "operation unless the objective itself demands "
                        "that class."
                    )
                undemonstrable_ops = sorted(
                    {
                        str(item.get("operation")).strip().casefold()
                        for item in needed
                        if isinstance(item, dict)
                        and isinstance(item.get("operation"), str)
                        and item["operation"].strip()
                        and item["operation"].strip().casefold()
                        in _OBLIGATION_OPERATIONS
                        and item["operation"].strip().casefold()
                        not in _CONSULTATION_OPERATIONS
                    }
                )
                if undemonstrable_ops:
                    rejected["undemonstrable_operations"] = (
                        undemonstrable_ops[:8]
                    )
                    rejected["undemonstrable_operation_guidance"] = (
                        "a prepare/act obligation can never be "
                        "demonstrated on this governed READ surface — "
                        "write classes are not invocable here; omit "
                        "operation or declare the consultation class "
                        "the objective demands (read, analysis, "
                        "discovery)."
                    )
                non_material_ops = sorted(
                    {
                        str(item.get("operation")).strip()
                        for item in needed
                        if isinstance(item, dict)
                        and isinstance(item.get("operation"), str)
                        and item["operation"].strip()
                        and item["operation"].strip().casefold()
                        in _OBLIGATION_OPERATIONS
                    }
                ) if (
                    str(expected_delivery).strip().casefold()
                    == "aggregation"
                ) else []
                if non_material_ops:
                    rejected["non_material_operations"] = (
                        non_material_ops[:8]
                    )
                    rejected["operation_guidance"] = (
                        "under aggregation delivery the authoritative "
                        "owner aggregate is the demonstration — an "
                        "operation-class restriction only freezes "
                        "your chosen strategy into a scope no other "
                        "consultation-class capability can echo; omit "
                        "operation and declare analytic demands in "
                        "the obligation description or "
                        "evidence_source."
                    )
                presentation_scope_keys = sorted(
                    {
                        key
                        for item in needed
                        if isinstance(item, dict)
                        for key in _presentation_scope_arg_keys(
                            item.get("required_args")
                        )
                    }
                )
                if (
                    any(
                        isinstance(item, dict)
                        and "required_args" in item
                        and not isinstance(item.get("required_args"), dict)
                        for item in needed
                    )
                    or presentation_scope_keys
                ):
                    rejected["invalid_required_args"] = True
                    if presentation_scope_keys:
                        rejected["presentation_scope_keys"] = (
                            presentation_scope_keys[:8]
                        )
                        rejected["required_args_guidance"] = (
                            "required_args declares only the material "
                            "business scope the user asked for (filters, "
                            "identities, units, periods under the "
                            "published carrier) — a presentation/"
                            "viewport selector like 'view' is not "
                            "business scope: it freezes your chosen "
                            "rendering into a restriction no other "
                            "capability can echo. Declare a demanded "
                            "presentation via evidence_source or the "
                            "obligation description instead."
                        )
                # Legitimate anchor candidates already in the model's
                # own proposal: the selector values it declared in
                # ``required_args`` are exactly the owner-vocabulary
                # tokens the governed layer records as invocation
                # vocabulary. Echoing them is bounded correction
                # feedback, never an anchor catalog and never proof —
                # the accepted anchor is still verified mechanically
                # against the invoked/echoed owner vocabulary.
                selector_candidates: list[str] = []
                for item in needed:
                    if not isinstance(item, dict):
                        continue
                    req = item.get("required_args")
                    if not isinstance(req, dict):
                        continue
                    for key, value in req.items():
                        if (
                            str(key) in _INVOCATION_VOCABULARY_KEYS
                            and isinstance(value, str)
                            and value.strip()
                            and "." not in value
                            and value.strip() not in selector_candidates
                        ):
                            selector_candidates.append(value.strip())
                if selector_candidates:
                    rejected["anchor_candidates"] = (
                        selector_candidates[:8]
                    )
                # Live owner vocabulary the model already used as
                # invocation selectors in this turn (recorded by the
                # governed layer) — legitimate anchor candidates at
                # correction time, never a catalog (RC5-R1/WS-4).
                observed: list[str] = []
                for att in ctx.deps.collected:
                    prov = getattr(att, "provenance", None)
                    for tok in (
                        getattr(prov, "invocation_vocabulary", ()) or ()
                    ):
                        if tok not in observed:
                            observed.append(tok)
                if observed:
                    rejected["observed_invocation_vocabulary"] = (
                        observed[:8]
                    )
                return _proj(rejected)
            ctx.deps.investigation_plan = plan
            accepted: dict[str, Any] = {
                "status": "ACCEPTED",
                "goal_class": plan.goal.goal_class,
                "comparison_requested": plan.goal.comparison_requested,
                "expected_delivery": plan.goal.output_mode,
                "target_identities": list(plan.target_identities),
                "evidence_needed": [
                    item.to_projection()
                    for item in plan.evidence_needed
                ],
            }
            # Echo the accepted subject so the Agent retains the same
            # declared interpretation across subsequent tool calls.
            # Omission made the field write-only after acceptance.
            subject = getattr(plan.goal, "business_subject", None)
            if isinstance(subject, str) and subject.strip():
                accepted["business_subject"] = subject.strip()
            return _proj(accepted)

        # Native MCP interop (task MCPTOOLSET-MIGRATION-01, extended by
        # NATIVE-MCPTOOLSET-DIRECT-ORCHESTRATION-01): each enabled
        # specialist is a real ``MCPToolset`` — tool discovery and input
        # schemas come from the owner's own tools/list, renamed to the
        # live capability_id (``{group_id}.{remote_name}``). No
        # synthesized Python signatures, no proxy meta-tools, no
        # parallel listing/invoke surface for the model.
        #
        # Governance boundary (doc 231): ``process_tool_call`` intercepts
        # every invocation BEFORE the wire and delegates to
        # ``_governed_invoke`` — live surface resolution, write-class
        # rejection, candidate-token relay, schema validation,
        # AuthZ and evidence stay Application-owned. The SDK's raw
        # client never executes business calls ungoverned; tools/list
        # remains the only traffic the SDK client performs.
        #
        # Connection config comes through the legitimate contract chain
        # (gates → provider → interop → port/adapter) — never by
        # reaching into private attributes of sibling components.
        from pydantic_ai.toolsets import (
            CombinedToolset,
            RenamedToolset,
        )

        # Group the live eligible surface by provider group: each
        # (provider_id, group_id) gets its own native toolset filtered
        # to the remote names the catalog marks eligible.
        group_caps: dict[tuple[str, str], dict[str, str]] = {}
        for entry in live_catalog:
            cap_id = str(entry.get("capability_id") or "").strip()
            remote = str(entry.get("remote_name") or "").strip()
            pid = str(entry.get("provider_id") or "").strip()
            gid = str(entry.get("group_id") or "").strip()
            if cap_id and remote and pid and gid:
                group_caps.setdefault((pid, gid), {})[cap_id] = remote

        def _governed_mcp_hook(group_id: str):
            async def _hook(ctx, call_tool, name, args):
                """Intercept BEFORE the wire: delegate the whole call to
                the canonical governed path — identical evidence,
                provenance, coverage and audit as the manual tools it
                replaces. Returns the same bounded projection."""
                return _governed_invoke(
                    ctx,
                    capability_id=f"{group_id}.{name}",
                    arguments=args if isinstance(args, dict) else {},
                )

            return _hook

        extra_toolsets: list[Any] = []
        for (pid, gid), caps in sorted(group_caps.items()):
            try:
                config = self._gates._native_toolset_config(
                    provider_id=pid,
                    group_id=gid,
                    timeout_seconds=max(
                        0.1, deadline.remaining_seconds()
                    ),
                )
            except SpecialistInteropError as exc:
                # Honest fail-closed: an unobtainable profile or
                # delegated credential means no toolset at all — never
                # an unauthenticated native client on the wire.
                _logger.info(
                    "orchestration engine=pydantic_ai "
                    "stage=investigation "
                    "decision=native_toolset_blocked provider=%s "
                    "group=%s error=%s correlation_id=%s",
                    pid,
                    gid,
                    exc.code,
                    correlation,
                )
                continue
            if config is None:
                continue
            try:
                ts = _build_native_mcp_toolset(
                    config,
                    process_tool_call=_governed_mcp_hook(gid),
                )
            except Exception as exc:
                # Fail-closed: an unusable endpoint/transport config must
                # degrade the specialist, never kill the turn.
                _logger.info(
                    "orchestration engine=pydantic_ai "
                    "stage=investigation "
                    "decision=native_toolset_blocked provider=%s "
                    "group=%s error=%s correlation_id=%s",
                    pid,
                    gid,
                    type(exc).__name__,
                    correlation,
                )
                continue
            allowed_remote = frozenset(caps.values())
            # Filter to the remote names the live eligible surface
            # declares, then rename to the capability_id itself so the
            # Agent sees the same id the governed surface validates.
            ts = ts.filtered(
                lambda ctx, td, names=allowed_remote: td.name in names
            )
            ts = RenamedToolset(ts, dict(caps))
            # Bounded schema-derived guidance (doc 231 parity): the old
            # synthesized tools carried "pass arguments as an object /
            # do not invent candidate_token" in their description —
            # without it the model calls execute tools empty. Appended
            # per-tool, derived only from the published inputSchema.
            ts = ts.prepared(_prepare_tool_definitions_envelope_hints)
            extra_toolsets.append(ts)
        _logger.info(
            "orchestration engine=pydantic_ai "
            "stage=investigation decision=native_mcp_toolsets "
            "groups=%s catalog_caps=%s toolsets=%s correlation_id=%s",
            ",".join(f"{p}:{g}" for (p, g) in sorted(group_caps))
            if group_caps
            else "-",
            ",".join(
                sorted(
                    cap
                    for caps in group_caps.values()
                    for cap in caps
                )
            )[:200],
            len(extra_toolsets),
            correlation,
        )
        agent_toolset = CombinedToolset([toolset, *extra_toolsets])

        @toolset.tool
        def compose_verified_observations(
            ctx,
            left_observation_index: int,
            right_observation_index: int,
        ) -> str:
            """Optionally compose two verified structure observations.

            Indexes come from prior owner-tool observations.
            Application verifies authoritative roots and provenance —
            this is not a free-form comparison script.
            """
            ctx.deps.deadline.check("tool_compose_observations")
            ctx.deps.tool_calls += 1
            collected = ctx.deps.collected
            try:
                left = collected[int(left_observation_index)]
                right = collected[int(right_observation_index)]
            except (IndexError, TypeError, ValueError):
                return _proj(
                    {
                        "status": "INVALID_ARGUMENTS",
                        "error_code": "observation_index_invalid",
                    }
                )
            composed = ctx.deps.gates._compose_observation_pair(
                left=left,
                right=right,
                correlation=ctx.deps.correlation,
                workspace_context=ctx.deps.workspace_context,
                deadline=ctx.deps.deadline,
            )
            if composed is None:
                return _proj(
                    {
                        "status": "NOT_APPLICABLE",
                        "error_code": "composition_unavailable",
                    }
                )
            ctx.deps.composed_attempt = composed
            return _proj(
                {
                    "status": composed.status.value,
                    "has_verified_composition": True,
                    # Size policy is ``_bounded_json`` / tool_projection_limit.
                    "content": composed.content or None,
                    "limitations": list(composed.limitations),
                    "error_code": composed.error_code,
                }
            )

        @toolset.tool
        def request_user_clarification(
            ctx,
            question: str,
            missing_aspects: list[str] | None = None,
        ) -> str:
            """Ask the user to clarify before continuing investigation.

            Stops further owner READs this turn. Application returns
            CLARIFICATION_REQUIRED. Prior verified observations remain
            in session history for the next turn.
            """
            ctx.deps.deadline.check("tool_request_clarification")
            ctx.deps.tool_calls += 1
            if ctx.deps.investigation_plan is not None:
                # A typed objective was already accepted this turn —
                # recording a clarification now would short-circuit
                # finalize into CLARIFICATION_REQUIRED and discard
                # the valid declared plan (INT-2 completion, defect
                # class 7). Legitimate mid-flight asks already fail
                # on the evidence-present gate below, so the only
                # reachable case is clarification-instead-of-
                # investigating: refuse and keep the contract.
                return _proj(
                    {
                        "status": "CONTINUE_REQUIRED",
                        "error_code": (
                            "clarification_rejected_plan_accepted"
                        ),
                        "note": (
                            "A typed objective was already declared "
                            "and accepted — investigate it through "
                            "the governed owner tools. Ask the user "
                            "only before declaring an objective."
                        ),
                    }
                )
            text = (question or "").strip()
            if missing_aspects:
                aspects = ", ".join(
                    str(item).strip()
                    for item in missing_aspects[:8]
                    if str(item).strip()
                )
                if aspects and aspects not in text:
                    text = f"{text} ({aspects})".strip()
            if not text:
                text = "Preciso de mais informações para continuar."
            uncovered = uncovered_user_identifiers(
                ctx.deps.input_text, ctx.deps.collected
            )
            if uncovered:
                # The user already named concrete identifiers. Asking
                # again would end the turn before the agent can choose
                # the next tool. Do not record a terminal clarification.
                return _proj(
                    {
                        "status": "CONTINUE_REQUIRED",
                        "error_code": "clarification_rejected_identifiers_present",
                        "uncovered_user_identifiers": uncovered,
                        "note": (
                            "Do not ask the user to repeat identifiers "
                            "already present. Call an owner tool for each "
                            "remaining identifier."
                        ),
                    }
                )
            question_identifiers = {
                item.casefold()
                for item in _IDENTIFIER_LITERAL_RE.findall(text)
            }
            if len(question_identifiers) == 1:
                # Asking the user to re-confirm a single identifier that
                # is already on the conversational table (this input, a
                # prior user turn, or a server-grounded DELIA result) is
                # redundant: record validity is established by the
                # governed READ surface, never by user re-confirmation.
                # Presence here is coverage, not authority — a
                # single-identifier ask naming a code the user never saw
                # stays allowed (the model surfaces its own candidate),
                # and identifiers only present in ungrounded DELIA prose
                # do not count. Multi-identifier asks are referent
                # selection (disambiguation) and identifier-free asks
                # are missing-scope questions: both remain legitimate
                # clarifications.
                context_blob = " ".join(
                    part
                    for part in (
                        ctx.deps.input_text or "",
                        _prior_turns_presence_blob(ctx.deps.prior_turns),
                    )
                    if part
                )
                context_identifiers = {
                    item.casefold()
                    for item in _IDENTIFIER_LITERAL_RE.findall(context_blob)
                }
                if question_identifiers <= context_identifiers:
                    return _proj(
                        {
                            "status": "CONTINUE_REQUIRED",
                            "error_code": "clarification_rejected_identifier_already_in_context",
                            "note": (
                                "The identifier is already present in "
                                "the conversation — do not ask the "
                                "user to repeat or confirm it. Verify "
                                "it through the authorized owner "
                                "tools instead."
                            ),
                        }
                    )
            if any(
                _is_business_evidence_attempt(item)
                for item in ctx.deps.collected
            ):
                return _proj(
                    {
                        "status": "CLARIFICATION_REJECTED",
                        "error_code": "clarification_rejected_evidence_present",
                        "note": (
                            "Verified owner evidence is already collected. "
                            "Do not ask the user to confirm it."
                        ),
                    }
                )
            ctx.deps.clarification_question = text[:800]
            return _proj(
                {
                    "status": "CLARIFICATION_RECORDED",
                    "question": ctx.deps.clarification_question,
                }
            )

        if comprehension_toolset is not None:
            # Variant B: initial-ambiguity clarification belongs to the
            # comprehension specialist (R6 split); mid-flight gaps stay
            # available to the investigation Agent on its own toolset.
            comprehension_toolset.tool(request_user_clarification)

        # A fresh provider/client per turn avoids httpx/asyncio locks
        # bound to a previous event loop (RuntimeError on the next turn).
        model = (
            self._model_factory()
            if self._model_factory is not None
            else self._model
        )
        # Measured per-turn usage: request-granularity accounting that
        # survives run exceptions — the variant-B handoff subtracts
        # real comprehension consumption, never a presumed zero.
        turn_usage = RunUsage()
        deps.turn_usage = turn_usage
        run_model = model
        agent_capabilities = ()
        if self._context_window_tokens:
            from pydantic_ai.capabilities import ProcessHistory

            # Native history boundary (doc 271 §4): the processor sees
            # the REAL messages pydantic_ai will send — including tool
            # results accumulated during the run, which no pre-call
            # estimate can cap. Oldest non-anchor messages are dropped
            # first; the initial request and latest context stay.
            reserve = self._context_window_tokens // 5
            window = self._context_window_tokens - reserve

            def _trim_overflow(messages):
                return _select_surviving_messages(messages, window)

            agent_capabilities = (
                ProcessHistory(processor=_trim_overflow),
            )
        agent = Agent(
            run_model,
            deps_type=InvestigationDeps,
            toolsets=[agent_toolset],
            instructions=instructions,
            retries=self._agent_retries,
            output_type=InvestigationAnswer,
            capabilities=list(agent_capabilities),
        )

        # Shape-only validation (doc 256 G1): the validator enforces the
        # bounded contract — bounded answer text, non-negative refs,
        # no clarification text declared in a non-clarification status.
        # It NEVER validates truth/authorization; the deterministic
        # acceptor in the finalize binds refs and verifies coverage.
        @agent.output_validator
        def _investigation_answer_shape(
            ctx: RunContext[InvestigationDeps],
            output: InvestigationAnswer,
        ) -> InvestigationAnswer:
            if any(index < 0 for index in output.evidence_refs):
                raise ModelRetry(
                    "evidence_refs must be non-negative indexes into "
                    "the collected tool observations"
                )
            # Recoverable structural fix BEFORE the acceptor: refs
            # must point at citable business evidence (the same
            # classification exposed in each observation's
            # evidence_citable flag). Discovery metadata, empty
            # results and failed calls are informative observations —
            # the model may report them in limitations, never cite
            # them as evidence. One-shot per run; a persistent bad
            # ref falls through to the deterministic acceptor, which
            # drops it and marks the declaration honestly.
            if not ctx.deps.evidence_ref_retry_used:
                citable = [
                    index
                    for index, item in enumerate(ctx.deps.collected)
                    if _is_business_evidence_attempt(item)
                ]
                bad_refs = [
                    index
                    for index in output.evidence_refs
                    if index >= len(ctx.deps.collected)
                    or not _is_business_evidence_attempt(
                        ctx.deps.collected[index]
                    )
                ]
                if bad_refs and citable:
                    ctx.deps.evidence_ref_retry_used = True
                    raise ModelRetry(
                        f"evidence_refs {bad_refs} point to "
                        "observations that are not citable business "
                        "evidence (discovery metadata, empty result "
                        "or failed call). Cite only indexes "
                        f"{citable}; report the rest under "
                        "limitations."
                    )
            # INT-2 bounded correction (same one-shot budget,
            # provider-neutral): finalizing with collected business
            # evidence but NO declared typed goal leaves coverage
            # permanently unevaluable (coverage_unknown). Buy ONE
            # native pass so the model can declare the objective via
            # declare_investigation_goal — never fabricates a plan; a
            # second goal-less declaration finalizes honestly with the
            # unknown verdict preserved.
            if (
                output.status
                in (
                    InvestigationAnswerStatus.COMPLETE,
                    InvestigationAnswerStatus.PARTIAL,
                    InvestigationAnswerStatus.INSUFFICIENT,
                    InvestigationAnswerStatus.NO_EVIDENCE,
                    InvestigationAnswerStatus.EMPTY,
                )
                and ctx.deps.collected
                and ctx.deps.investigation_plan is None
                and not ctx.deps.insufficiency_retry_used
                and ctx.deps.tool_calls < self._tool_calls_limit
            ):
                ctx.deps.insufficiency_retry_used = True
                raise ModelRetry(
                    "You collected owner evidence but never declared "
                    "the typed investigation goal — coverage cannot be "
                    "evaluated without it. Call "
                    "declare_investigation_goal once now with the "
                    "objective's goal class, expected delivery and the "
                    "material evidence obligations it required, then "
                    "re-submit your answer."
                )
            # Native technical retry (bounded by UsageLimits, one-shot
            # per run): a declaration of insufficiency while tool
            # budget remains may simply mean the selected capability
            # projected a subset — the model may call another owner
            # tool before settling. The verdict stays in the
            # deterministic acceptor; this only buys ONE more pass.
            if (
                output.status
                in (
                    InvestigationAnswerStatus.INSUFFICIENT,
                    InvestigationAnswerStatus.NO_EVIDENCE,
                    InvestigationAnswerStatus.EMPTY,
                )
                and output.answer.strip()
                and not ctx.deps.insufficiency_retry_used
                and ctx.deps.tool_calls < self._tool_calls_limit
            ):
                ctx.deps.insufficiency_retry_used = True
                raise ModelRetry(
                    "You declared insufficient evidence while tool "
                    "calls remain. If another listed owner capability "
                    "could supply the missing data, call it now; "
                    "otherwise re-declare."
                )
            # R01 bounded correction (same one-shot budget, provider-
            # neutral): a COMPLETE/PARTIAL declaration produced with
            # ZERO owner calls and ZERO collected observations claims
            # satisfaction with no evidence path exercised. When owner
            # capabilities were actually exposed this turn, buy ONE
            # native pass so the model can either gather evidence or
            # honestly re-declare; it never forces a call — conceptual
            # objectives can re-declare with limitations.
            if (
                output.status
                in (
                    InvestigationAnswerStatus.COMPLETE,
                    InvestigationAnswerStatus.PARTIAL,
                )
                and not ctx.deps.collected
                and ctx.deps.tool_calls == 0
                and live_catalog
                and not ctx.deps.insufficiency_retry_used
                and ctx.deps.tool_calls < self._tool_calls_limit
            ):
                ctx.deps.insufficiency_retry_used = True
                raise ModelRetry(
                    "You answered without consulting any owner "
                    "capability. If an objective needs operational "
                    "data, call the authorized capability that can "
                    "supply it now; if the question is purely "
                    "conceptual, re-declare with honest limitations."
                )
            # INT-1: COMPLETE while named identifiers remain uncovered
            # is not objective satisfaction — buy one more pass or
            # force an honest re-declaration with unmet obligations.
            if (
                output.status is InvestigationAnswerStatus.COMPLETE
                and not ctx.deps.insufficiency_retry_used
                and ctx.deps.tool_calls < self._tool_calls_limit
            ):
                still_open = uncovered_user_identifiers(
                    ctx.deps.input_text, ctx.deps.collected
                )
                if still_open:
                    ctx.deps.insufficiency_retry_used = True
                    raise ModelRetry(
                        "Named identifiers still lack authoritative "
                        f"observations: {still_open[:8]}. Call an "
                        "owner capability that can observe each "
                        "remaining identifier, or re-declare as "
                        "insufficient/partial with unmet_obligations."
                    )
            # INT-1/INT-3 bounded correction (same one-shot budget,
            # provider-neutral): a COMPLETE/PARTIAL declaration whose
            # collected business evidence does not demonstrate every
            # material obligation is rejected silently by the
            # deterministic acceptor — the model never learned which
            # obligation remains open. Evaluate the obligations with
            # the same deterministic helper the acceptor uses; when
            # any stays undemonstrated and tool budget remains, buy
            # ONE native pass naming the gap so the model may call a
            # complementary governed capability or re-declare
            # honestly. Verdict authority stays with the acceptor — a
            # second unproven declaration finalizes INCONCLUSIVE.
            if (
                output.status
                in (
                    InvestigationAnswerStatus.COMPLETE,
                    InvestigationAnswerStatus.PARTIAL,
                )
                and ctx.deps.investigation_plan is not None
                and ctx.deps.collected
                and not ctx.deps.insufficiency_retry_used
                and ctx.deps.tool_calls < self._tool_calls_limit
            ):
                plan = ctx.deps.investigation_plan
                needed = getattr(plan, "evidence_needed", ()) or ()
                if needed:
                    coverage = _evaluate_material_obligations(
                        obligations=needed,
                        business=tuple(
                            item
                            for item in ctx.deps.collected
                            if _is_business_evidence_attempt(item)
                        ),
                        delivery=_plan_delivery_mode(plan),
                    )
                    unmet = [
                        description
                        for description, state in coverage
                        if state != OBLIGATION_SATISFIED
                    ]
                    if unmet:
                        ctx.deps.insufficiency_retry_used = True
                        raise ModelRetry(
                            "Your declared answer does not yet "
                            "demonstrate these material obligations: "
                            f"{unmet[:4]}. If another listed governed "
                            "capability can supply the missing evidence "
                            "under the accepted plan, call it now; "
                            "otherwise re-declare honestly as "
                            "insufficient/partial with "
                            "unmet_obligations."
                        )
            # Cosmetic normalization only — the internal evidence
            # handle ``[obs:N]`` is an implementation detail, never
            # user-facing answer text. Evidence binding is unchanged.
            answer = _INTERNAL_OBS_MARKER.sub("", output.answer)
            if answer != output.answer or len(answer) > (
                MAX_RENDER_CONTENT_CHARS
            ):
                output = dataclasses.replace(
                    output,
                    answer=answer[:MAX_RENDER_CONTENT_CHARS],
                )
            if (
                output.status
                is not InvestigationAnswerStatus.NEEDS_CLARIFICATION
                and output.clarification_question is not None
            ):
                return dataclasses.replace(
                    output, clarification_question=None
                )
            return output

        remaining = max(1.0, deadline.remaining_seconds())
        prompt = input_text
        message_history = _prior_message_history(
            prior_turns, turns_limit=self._prior_turns_limit
        )
        # Variant B — governed programmatic handoff, Application-owned
        # sequencing (never AgentToolset delegation): the comprehension
        # specialist runs first on a reduced surface — the SAME typed
        # goal declaration validated by the SAME Application acceptor
        # plus the clarification signal, no owner tools. Its output is a
        # proposal; the investigation run starts only when the
        # Application-accepted plan exists on deps (R1 gate unchanged).
        comp_usage: dict[str, int] | None = None
        handoff_error: str | None = None
        investigation_request_limit = self._request_limit
        investigation_tool_limit = self._tool_calls_limit
        if self._two_agent_experiment:
            comp_usage, handoff_error = self._run_comprehension_pass(
                deps=deps,
                model=run_model,
                turn_usage=turn_usage,
                toolset=comprehension_toolset,
                prompt=prompt,
                message_history=message_history,
                agent_capabilities=agent_capabilities,
                deadline=deadline,
                correlation=correlation,
                live_catalog=live_catalog,
            )
            if (
                handoff_error is None
                and deps.investigation_plan is None
                and deps.clarification_question is None
            ):
                # Run completed but produced neither an accepted plan
                # nor a clarification — conservative insufficient, zero
                # owner calls.
                handoff_error = "comprehension_no_accepted_plan"
            # Shared turn budget — strictly subtractive. An unknown
            # consumption is conservatively treated as fully consumed
            # (never presumed zero), and a remaining balance <= 0 can
            # never be regranted by a max(1, ...) floor.
            investigation_request_limit = self._request_limit - (
                comp_usage["requests"]
                if comp_usage
                else self._request_limit
            )
            investigation_tool_limit = (
                self._tool_calls_limit - deps.tool_calls
            )
            if (
                handoff_error is None
                and deps.investigation_plan is not None
                and (
                    investigation_request_limit <= 0
                    or investigation_tool_limit <= 0
                )
            ):
                handoff_error = "investigation_budget_exhausted"
            if handoff_error is None and (
                deps.investigation_plan is not None
            ):
                # An Application-accepted plan means comprehension
                # produced a clear-enough objective. A residual
                # ``request_user_clarification`` from the same pass must
                # not survive into investigation finalization — that
                # short-circuited SUCCESS evidence into
                # CLARIFICATION_REQUIRED + NON_GROUNDED while publishing
                # the COMPLETE answer (G2 grounding incoherence).
                if deps.clarification_question is not None:
                    deps.clarification_question = None
                # Accepted-plan echo: the Application-validated contract
                # the investigator consumes — bounded structured
                # projection, never model-authored text.
                accepted_plan = deps.investigation_plan
                prompt += (
                    "\n\nAccepted investigation objective (validated "
                    "by the coordination layer — investigate it "
                    "directly; the objective is already declared and "
                    "cannot be changed):\n"
                    + _bounded_json(
                        {
                            "goal_class": (
                                accepted_plan.goal.goal_class
                            ),
                            "expected_delivery": (
                                accepted_plan.goal.output_mode
                            ),
                            "comparison_requested": (
                                accepted_plan.goal.comparison_requested
                            ),
                            "business_subject": getattr(
                                accepted_plan.goal,
                                "business_subject",
                                None,
                            ),
                            "target_identities": list(
                                accepted_plan.target_identities
                            )[:8],
                            "evidence_needed": [
                                item.to_projection()
                                for item in (
                                    accepted_plan.evidence_needed
                                )
                            ][:8],
                        },
                        limit=1600,
                    )
                )
        if self._context_window_tokens:
            from app.application.model_invocation.context_budget import (
                ADAPTER_OVERHEAD_TOKENS,
                DEFAULT_GENERATION_RESERVE_TOKENS,
                estimate_text_tokens,
            )
            import json as _json

            # Full pre-call envelope (doc 270 §2-3): instructions +
            # prompt + serialized tool schemas + output schema +
            # protocol overhead + generation reserve — never just
            # instructions+prompt. Constants are the existing budget
            # module's bounded estimates (labeled, not exact native
            # overhead); tool_result growth is bounded separately by
            # tool_projection_limit/tool_calls_limit.
            tool_schemas = _json.dumps(
                [
                    {
                        "id": c.get("capability_id"),
                        "description": c.get("description") or "",
                        "input_schema": c.get("input_schema") or {},
                    }
                    for c in live_catalog
                ],
                ensure_ascii=False,
                default=str,
            )
            estimated = (
                estimate_text_tokens(instructions)
                + estimate_text_tokens(prompt)
                + estimate_text_tokens(tool_schemas)
                + estimate_text_tokens(
                    _json.dumps(InvestigationAnswer.__dict__, default=str)
                )
                + ADAPTER_OVERHEAD_TOKENS
                + DEFAULT_GENERATION_RESERVE_TOKENS
            )
            if estimated >= self._context_window_tokens:
                _logger.info(
                    "orchestration engine=pydantic_ai "
                    "stage=investigation "
                    "decision=context_budget_fail "
                    "estimated=%d window=%d correlation_id=%s",
                    estimated,
                    self._context_window_tokens,
                    correlation,
                )
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    error_code="investigation_context_overflow",
                    admission_outcome=unbound_outcome,
                    limitations=(
                        "investigation_context_overflow:"
                        f"{estimated}>={self._context_window_tokens}",
                    ),
                )
        result = None
        usage_limited = False
        # Variant B handoff boundary: the investigation run starts ONLY
        # with an Application-accepted plan — a rejected/absent proposal
        # or a comprehension failure means zero owner calls.
        run_investigation = (
            not self._two_agent_experiment
            or (
                handoff_error is None
                and deps.investigation_plan is not None
            )
        )
        try:
            try:
                if run_investigation:
                    result = agent.run_sync(
                        prompt,
                        message_history=message_history or None,
                        deps=deps,
                        model_settings=_investigation_model_settings(
                            self._max_output_tokens
                        ),
                        usage=turn_usage,
                        usage_limits=UsageLimits(
                            request_limit=investigation_request_limit,
                            tool_calls_limit=investigation_tool_limit,
                        ),
                    )
            except (
                _InvestigationContextOverflow,
                _InvestigationHistoryIntegrityError,
            ) as exc:
                integrity = isinstance(
                    exc, _InvestigationHistoryIntegrityError
                )
                _logger.info(
                    "orchestration engine=pydantic_ai "
                    "stage=investigation decision=%s "
                    "correlation_id=%s",
                    "history_integrity" if integrity else "context_overflow",
                    correlation,
                )
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    error_code=(
                        "investigation_history_invalid"
                        if integrity
                        else "investigation_context_overflow"
                    ),
                    admission_outcome=unbound_outcome,
                    limitations=(
                        (
                            "investigation_history_invalid:"
                            + str(exc)[:200],
                        )
                        if integrity
                        else ("investigation_context_overflow:in-run",)
                    ),
                )
            except Exception as exc:
                if type(exc).__name__ == "UsageLimitExceeded":
                    usage_limited = True
                    _logger.info(
                        "orchestration engine=pydantic_ai "
                        "stage=investigation decision=usage_limit_finalize "
                        "tool_calls=%d collected=%d correlation_id=%s",
                        deps.tool_calls,
                        len(deps.collected),
                        correlation,
                    )
                else:
                    from app.application.capability_provision.semantic_capability_support import (
                        _StageDeadlineExceeded,
                        _TurnCancelled,
                    )
                    from app.application.interaction.turn_budget import (
                        TurnBudgetExhausted,
                    )

                    if isinstance(
                        exc,
                        (
                            _StageDeadlineExceeded,
                            TurnBudgetExhausted,
                            _TurnCancelled,
                        ),
                    ):
                        raise
                    cause = getattr(exc, "__cause__", None)
                    if isinstance(
                        cause,
                        (
                            _StageDeadlineExceeded,
                            TurnBudgetExhausted,
                            _TurnCancelled,
                        ),
                    ):
                        raise cause from exc
                    exc_cause = getattr(exc, "__cause__", None)
                    # Typed-safe metadata only (doc 283 §2): exception
                    # classes, stage, category and counts — never raw
                    # model output, bodies, causes or messages, which
                    # may carry business data, identifiers or secrets.
                    exc_name = type(exc).__name__
                    error_category = (
                        "output_retries_exhausted"
                        if exc_name == "UnexpectedModelBehavior"
                        else (
                            "provider_error"
                            if exc_name
                            in ("ModelHTTPError", "ModelAPIError")
                            else "agent_behavior"
                        )
                    )
                    # Doc 286 §3: classify WHICH stage exhausted output
                    # retries from the native ToolRetryError cause — only
                    # typed fields (tool_name, pydantic error type/loc
                    # paths), never raw args/input values/messages.
                    retry_tool = "-"
                    retry_errors = "-"
                    from pydantic_ai.exceptions import ToolRetryError

                    if isinstance(exc_cause, ToolRetryError):
                        tr = exc_cause.tool_retry
                        retry_tool = (
                            str(getattr(tr, "tool_name", None) or "output")
                        )
                        tr_content = getattr(tr, "content", None)
                        if isinstance(tr_content, list):
                            retry_errors = ",".join(
                                sorted(
                                    {
                                        ".".join(
                                            str(x)
                                            for x in e.get("loc", ())
                                        )
                                        + ":"
                                        + str(e.get("type", "?"))
                                        for e in tr_content
                                        if isinstance(e, Mapping)
                                    }
                                )
                            )[:400]
                            # TEMP-DIAG removed (doc 286 §3 evidence
                            # collected: output-stage json_invalid —
                            # model emitted prose instead of structured
                            # output).
                    _logger.info(
                        "orchestration engine=pydantic_ai "
                        "stage=investigation decision=agent_error "
                        "error_type=%s cause_type=%s category=%s "
                        "retry_tool=%s retry_errors=%s "
                        "tool_calls=%d correlation_id=%s",
                        exc_name,
                        type(exc_cause).__name__
                        if exc_cause is not None
                        else "-",
                        error_category,
                        retry_tool,
                        retry_errors,
                        deps.tool_calls,
                        correlation,
                    )
                    return GovernedCapabilityAttempt(
                        status=GovernedCapabilityStatus.PROCESSING_TIMEOUT
                        if deadline.remaining_seconds() <= 2.0
                        else GovernedCapabilityStatus.NOT_APPLICABLE,
                        correlation_id=correlation,
                        error_code="investigation_agent_error",
                        admission_outcome=unbound_outcome,
                        limitations=(
                            "investigation_agent_error:"
                            f"{type(exc).__name__}",
                        ),
                    )

            if (
                not deps.clarification_question
                and not any(
                    _is_business_evidence_attempt(item)
                    for item in deps.collected
                )
                and not _IDENTIFIER_LITERAL_RE.search(input_text or "")
                and not _IDENTIFIER_LITERAL_RE.search(prior_blob)
            ):
                deps.clarification_question = (
                    "Preciso saber qual registro consultar. "
                    "Informe o identificador ou descreva o item."
                )
            declared_answer = None
            if result is not None:
                candidate_output = getattr(result, "output", None)
                if isinstance(candidate_output, InvestigationAnswer):
                    declared_answer = candidate_output
            terminal = self._gates._finalize_semantic_investigation(
                input_text=input_text,
                collected=tuple(deps.collected),
                correlation=correlation,
                workspace_context=workspace_context,
                deadline=deadline,
                unbound_outcome=unbound_outcome,
                plan=deps.investigation_plan,
                clarification_question=deps.clarification_question,
                composed_attempt=deps.composed_attempt,
                declared_answer=declared_answer,
            )

            extra_limitations: list[str] = []
            if usage_limited:
                extra_limitations.append("tool_calls_limit_reached")
            if self._two_agent_experiment:
                extra_limitations.append("experiment_variant=split")
                extra_limitations.append(
                    "comprehension_llm_requests="
                    + str(comp_usage["requests"] if comp_usage else 0)
                )
                if handoff_error is not None:
                    extra_limitations.append(
                        f"comprehension_handoff={handoff_error}"
                    )
            if (
                catalog_failures
                and not any(
                    _is_business_evidence_attempt(item)
                    for item in deps.collected
                )
            ):
                extra_limitations.extend(
                    f"catalog_failure:{code}"
                    for code in catalog_failures[:6]
                )
                if terminal.status is GovernedCapabilityStatus.NOT_APPLICABLE:
                    terminal = dataclasses.replace(
                        terminal,
                        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                        error_code="catalog_owner_unavailable",
                    )
            if extra_limitations:
                terminal = dataclasses.replace(
                    terminal,
                    limitations=tuple(terminal.limitations)
                    + tuple(extra_limitations),
                )
            _logger.info(
                "orchestration engine=pydantic_ai "
                "stage=investigation decision=finalized "
                "status=%s error_code=%s collected=%d tool_calls=%d "
                "clarification=%s composed=%s correlation_id=%s",
                terminal.status.value,
                terminal.error_code,
                len(deps.collected),
                deps.tool_calls,
                bool(deps.clarification_question),
                deps.composed_attempt is not None,
                correlation,
            )
            return terminal
        finally:
            if self._model_factory is not None:
                _close_investigation_client(model)

    def _run_comprehension_pass(
        self,
        *,
        deps: InvestigationDeps,
        model: Any,
        toolset: Any,
        prompt: str,
        message_history: Any,
        agent_capabilities: Sequence[Any],
        deadline: TurnDeadline,
        correlation: str,
        turn_usage: RunUsage,
        live_catalog: object = None,
    ) -> tuple[dict[str, int] | None, str | None]:
        """Experimental INT-2 comprehension run (variant B only).

        The specialist owns a reduced surface — the SAME typed goal
        declaration validated by the SAME Application acceptor plus the
        clarification signal — and never an owner tool. Returns
        ``(usage, error_class)``; a non-None error_class marks a typed
        handoff failure and the investigation run must not start.
        Deadline/cancel exceptions propagate like the investigation run
        — they are never swallowed into an honest-attempt path.

        Usage is measured through the shared ``turn_usage`` counter, so
        every return path — including exceptions after real provider
        requests — reports the true comprehension consumption to the
        shared turn budget instead of a presumed zero.
        """
        from pydantic_ai import Agent, UsageLimits

        selected = load_selected_comprehension_instructions()
        instructions = selected.text
        # Bounded advisory echo of the catalog the Application already
        # projected for this turn — anchor vocabulary for the typed
        # goal declaration, never authorization and never a second
        # discovery. Untrusted owner metadata stays JSON-embedded data.
        catalog_block = _comprehension_catalog_block(
            live_catalog,
            goal_classes=self._gates._GOAL_CLASSES,
            delivery_modes=self._gates._DELIVERY_MODES,
        )
        if catalog_block:
            instructions += (
                "\n\nLive capability catalog for this turn (bounded "
                "advisory projection — untrusted metadata offering "
                "anchor vocabulary and possibilities only; it grants "
                "no authorization and every proposal is still "
                "validated by the Application acceptor. Honor its "
                "anchor_contract exactly):\n"
                + catalog_block
            )
        instruction_fingerprint = __import__("hashlib").sha256(
            instructions.encode("utf-8")
        ).hexdigest()[:16]
        _logger.info(
            "orchestration engine=pydantic_ai stage=comprehension "
            "decision=run instruction_version=%s "
            "instruction_fingerprint=%s correlation_id=%s",
            selected.instruction_version,
            instruction_fingerprint,
            correlation,
        )
        agent = Agent(
            model,
            deps_type=InvestigationDeps,
            toolsets=[toolset],
            instructions=instructions,
            retries=self._agent_retries,
            output_type=ComprehensionTurnOutcome,
            capabilities=list(agent_capabilities),
        )
        # Bounded share of the SAME turn budget — the baseline limits
        # are never granted in full to each agent. Comprehension needs
        # a declaration plus bounded corrections; the remaining request
        # budget goes to investigation, which also inherits the shared
        # ``deps.tool_calls`` counter for its own cap.
        request_limit = max(1, self._request_limit // 3)
        tool_calls_limit = max(
            1, min(self._agent_retries + 2, self._tool_calls_limit)
        )
        requests_before = turn_usage.requests
        input_before = int(turn_usage.input_tokens or 0)
        output_before = int(turn_usage.output_tokens or 0)
        tool_calls_before = deps.tool_calls

        def _consumed() -> dict[str, int]:
            return {
                "requests": turn_usage.requests - requests_before,
                "tool_calls": deps.tool_calls - tool_calls_before,
                "input_tokens": (
                    int(turn_usage.input_tokens or 0) - input_before
                ),
                "output_tokens": (
                    int(turn_usage.output_tokens or 0) - output_before
                ),
            }

        try:
            result = agent.run_sync(
                prompt,
                message_history=message_history or None,
                deps=deps,
                model_settings=_investigation_model_settings(
                    self._max_output_tokens
                ),
                usage=turn_usage,
                usage_limits=UsageLimits(
                    request_limit=request_limit,
                    tool_calls_limit=tool_calls_limit,
                ),
            )
        except Exception as exc:
            from app.application.capability_provision.semantic_capability_support import (
                _StageDeadlineExceeded,
                _TurnCancelled,
            )
            from app.application.interaction.turn_budget import (
                TurnBudgetExhausted,
            )

            _terminal = (
                _StageDeadlineExceeded,
                TurnBudgetExhausted,
                _TurnCancelled,
            )
            if isinstance(exc, _terminal):
                raise
            cause = getattr(exc, "__cause__", None)
            if isinstance(cause, _terminal):
                raise cause from exc
            if (
                deps.investigation_plan is not None
                or deps.clarification_question is not None
            ):
                # The authoritative artifact already exists — the plan
                # was validated by the Application acceptor (or the
                # specialist emitted the clarification signal) before
                # the run failed on its observability-only output.
                _logger.info(
                    "orchestration engine=pydantic_ai "
                    "stage=comprehension decision=artifact_kept "
                    "error_type=%s correlation_id=%s",
                    type(exc).__name__,
                    correlation,
                )
                return _consumed(), None
            if type(exc).__name__ == "UsageLimitExceeded":
                _logger.info(
                    "orchestration engine=pydantic_ai "
                    "stage=comprehension decision=usage_limit "
                    "tool_calls=%d correlation_id=%s",
                    deps.tool_calls,
                    correlation,
                )
                return _consumed(), "comprehension_budget_exhausted"
            exc_name = type(exc).__name__
            error_class = (
                "comprehension_output_retries_exhausted"
                if exc_name == "UnexpectedModelBehavior"
                else f"comprehension_agent_error:{exc_name}"
            )
            _logger.info(
                "orchestration engine=pydantic_ai "
                "stage=comprehension decision=agent_error "
                "error_type=%s correlation_id=%s",
                exc_name,
                correlation,
            )
            return _consumed(), error_class
        snapshot = _consumed()
        _logger.info(
            "orchestration engine=pydantic_ai stage=comprehension "
            "decision=completed requests=%d tool_calls=%d plan=%s "
            "clarification=%s correlation_id=%s",
            snapshot["requests"],
            snapshot["tool_calls"],
            deps.investigation_plan is not None,
            deps.clarification_question is not None,
            correlation,
        )
        return snapshot, None
