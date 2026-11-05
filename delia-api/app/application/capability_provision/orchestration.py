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


import contextvars
import dataclasses
import hashlib
import json
import logging
import re
import time
import unicodedata
import uuid
from typing import (
    Any,
    Callable,
    Mapping,
    MutableMapping,
    Sequence,
)

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
    validate_arguments as _validate_instance,
    validate_untyped_arguments,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityBinding,
    GovernedCapabilityStatus,
    OWNER_PATH_UNBOUND,
    SURFACE_INQUIRY_ADMISSION,
    _error_attempt,
    _success_attempt,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    LIMITATION_CAPABILITY_SURFACE_LISTING,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    LIMITATION_RESULT_TRUNCATED,
    VerifiedCompositeEvidence,
)
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
    EMPTY_RESULT_TEXT,
    FieldLabels,
    MAX_RENDER_CONTENT_CHARS,
    _business_lines,
    _format_structured,
    _md_business_lines,
    _md_format_structured,
    _md_leaf,
    field_display_label,
)
from app.application.capability_provision.generic_evidence_renderer import (
    MAX_DESCRIPTION_CHARS,
    MAX_OWNER_EVIDENCE_ENTRY_CHARS,
    MAX_RENDER_LIST_ITEMS,
    MAX_SURFACE_ENTRIES,
    _CAPABILITY_VOCABULARY_KEYS,
    _CONTROL_PLANE_KEYS,
    _RESOLVER_ENVELOPE_KEYS,
    _canonical_key,
    _comparison_records,
    _contract_fact_rows,
    _is_generic_status,
    _mapping_items_excluding_control,
    _redact_text,
    _resolver_entities,
    _sanitize_renderable,
    _unwrap_owner_payload,
    extract_pagination_envelope,
    parse_temporal_value,
)
from app.application.capability_provision.ports import (
    CapabilityProviderPort,
)
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.model_invocation.model import (
    InstructionLineage,
    ModelInvocationId,
)
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
# Bounded owner-responsibility excerpt projected per group for stage-1
# selection (see ``_group_scope_text``). Small enough that every group
# keeps semantic signal inside the surface budget before individual
# capability descriptions are compacted away.
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
MAX_ARGUMENTS_BLOCK_CHARS = 14000
# Catalog INDEX options may exceed resolver ambiguity shortlists.
# Keep bounded (budget/prompt), but large enough for owner registries.

# Hierarchical selection (R1): the model makes three bounded
# proposals — specialist, then capability on that specialist's live
# surface, then arguments projected into the owner's live inputSchema.
# Each stage is independently revalidated against fresh catalog data;
# a proposal is never authority.



# I02-R3B: cold-start may request capability selection and turn-goal
# fields in one typed proposal (same purpose id). Expected fields stay
# capability-only so legacy fixtures without goal_class still validate;
# when goal_class is present the runtime skips a second turn_goal call.












# CRI E2 (doc 73 §3-§6 / spec 75): when the response-intelligence
# switch is ON, the SAME goal stage also proposes typed sufficiency
# requirements — a hypothesis the runtime verifies against typed
# evidence at the outcome edge. The clause itself is a governed
# declarative resource (config/cri_instructions.delpi.json, E2-R3)
# injected by composition; baseline instructions stay byte-identical
# and the mode deactivates when the resource is absent.


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
# Bounded reconcile signal (typed, untrusted data — never an
# instruction): the group stage judged this surface applicable to the
# information need, yet the capability stage bound none. One governed
# re-proposal asks the model to reconcile — binding the capability
# that answers the need remains as valid as confirming
# ``applicable: false`` when no listed capability owns the entity.




# Bounded prior-continuation reformulation (Task 21): render-level
# proposal malformations the model may correct on a single retry.
# Deliberate outcomes (empty_selection) are never retried — that
# would pressure the model to invent a selection it judged absent.

# Owner-visible context for the same reformulation: the concrete
# arguments that produced the empty result, with permission to vary
# lexical form (shorter, simpler, singular or canonical term) — the
# model performs the semantic reformulation; nothing is hardcoded.





# R1 (doc 35): after a group was chosen but capability selection is
# inconclusive, prefer a bounded ask-back over bare NOT_APPLICABLE
# that previously fell through to a second model call → 504.
# Group-level applicable=false is different: it means no owner surface
# is required → NOT_APPLICABLE → conversational fallback (CONV recovery).

# Typed lineage version of the governed instruction resource
# entries consumed by the retained model stages (typed admission and
# the agent-requested evidence composition).
SELECTION_INSTRUCTION_VERSION = "13"

EVIDENCE_COMPOSITION_INSTRUCTION_ID = (
    "delia.capability_orchestration.evidence_composition"
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



def _is_candidate_bound(descriptor: ProviderCapability) -> bool:
    """True when the owner schema declares a candidate_token input."""
    return _requires_field(descriptor, CANDIDATE_TOKEN_FIELD)


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


def _bind_missing_required_query(
    arguments: Mapping[str, Any],
    *,
    input_schema: Mapping[str, Any] | None,
    input_text: str,
) -> dict[str, Any]:
    """Fill omitted required ``query`` from the turn utterance.

    Generic schema binding only — does not choose a capability or
    invent business identifiers beyond the user text already present.
    """
    args = dict(arguments or {})
    if not isinstance(input_schema, Mapping):
        return args
    properties = input_schema.get("properties")
    required = input_schema.get("required")
    if not isinstance(properties, Mapping) or "query" not in properties:
        return args
    required_names = (
        {str(name) for name in required}
        if isinstance(required, (list, tuple))
        else set()
    )
    if "query" not in required_names:
        return args
    if str(args.get("query") or "").strip():
        return args
    utterance = (input_text or "").strip()
    if not utterance:
        return args
    args["query"] = utterance[:MAX_RENDER_CONTENT_CHARS]
    return args



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










# SpecialistOperationClass -> canonical OperationCharacter for the
# shared plan validator. OperationCharacter intentionally models
# side-effect character only: DISCOVERY, READ and ANALYSIS are all
# non-mutating for planning purposes and project as READ — the
# specialist class stays authoritative on the descriptor itself
# (ANALYSIS is never collapsed on the capability contract).




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



# Provenance/transport-only scalar keys — excluded from the shared
# context gate: differing technical metadata never forces INCONCLUSIVE
# (LOOP-03R1 §17). Canonical key forms, never owner names.


_EVIDENCE_CODE_KEYS = (
    "code",
    "product_code",
    "component_code",
    "item_code",
    "material_code",
    "codigo",
)
_EVIDENCE_QTY_KEYS = ("quantity", "qty", "quantidade")
_EVIDENCE_UNIT_KEYS = ("unit", "unidade", "un")
_EVIDENCE_TYPE_KEYS = ("type", "tipo")
_EVIDENCE_DESC_KEYS = ("description", "descricao", "desc", "name")
_EVIDENCE_CHILD_KEYS = ("components", "children", "componentes", "items")


def _flatten_evidence_records(
    records: Any, path: tuple[int, ...] = ()
) -> list[dict[str, Any]]:
    """Flatten owner evidence records — flat lists or nested BOM
    trees — into typed rows (code, path, qty, unit, type, desc).
    Codes are preserved verbatim as strings; path marks structural
    occurrence so identical codes at different positions are never
    silently collapsed."""
    rows: list[dict[str, Any]] = []
    for index, rec in enumerate(records or ()):
        if not isinstance(rec, Mapping):
            continue
        node_path = path + (index,)
        code = None
        for key in _EVIDENCE_CODE_KEYS:
            if rec.get(key) not in (None, ""):
                code = str(rec[key])
                break
        if code:
            qty = next(
                (
                    rec[k]
                    for k in _EVIDENCE_QTY_KEYS
                    if rec.get(k) is not None
                ),
                None,
            )
            unit = next(
                (
                    str(rec[k])
                    for k in _EVIDENCE_UNIT_KEYS
                    if rec.get(k) not in (None, "")
                ),
                None,
            )
            rtype = next(
                (
                    str(rec[k])
                    for k in _EVIDENCE_TYPE_KEYS
                    if rec.get(k) not in (None, "")
                ),
                None,
            )
            desc = next(
                (
                    str(rec[k])
                    for k in _EVIDENCE_DESC_KEYS
                    if rec.get(k) not in (None, "")
                ),
                "",
            )
            rows.append(
                {
                    "code": code,
                    "path": node_path,
                    "qty": qty,
                    "unit": unit,
                    "type": rtype,
                    "description": desc,
                }
            )
        for key in _EVIDENCE_CHILD_KEYS:
            child = rec.get(key)
            if isinstance(child, (list, tuple)) and child:
                rows.extend(_flatten_evidence_records(child, node_path))
                break
    return rows


def _evidence_rows_by_code(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["code"], []).append(row)
    return grouped


def _verify_evidence_composition(
    sources: dict[str, list[dict[str, Any]]],
    proposal: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Deterministic full-coverage comparison of two evidence
    sources plus strict validation of model-proposed claims.

    Per doc 222: the model may only propose candidate
    correspondences — every FACT comes from this deterministic
    diff over ALL flattened records; a fabricated/out-of-range
    reference is rejected and an omitted true match is still
    covered (coverage is never model-bounded)."""
    limitations: list[str] = []
    grouped = {
        sid: _evidence_rows_by_code(_flatten_evidence_records(records))
        for sid, records in sources.items()
    }
    ids = [sid for sid, g in grouped.items() if g]
    if len(ids) != 2 or len(sources) != 2:
        return {
            "verdict": "inconclusive",
            "claims": (),
            "limitations": ("evidence_partial",),
        }
    left, right = ids[0], ids[1]
    left_codes, right_codes = set(grouped[left]), set(grouped[right])
    common: list[dict[str, Any]] = []
    qty_diffs: list[dict[str, Any]] = []
    occurrence_diffs: list[dict[str, Any]] = []
    for code in sorted(left_codes & right_codes):
        lrows, rrows = grouped[left][code], grouped[right][code]
        left_qty = sum(
            (r["qty"] if isinstance(r["qty"], (int, float)) else 0)
            for r in lrows
        )
        right_qty = sum(
            (r["qty"] if isinstance(r["qty"], (int, float)) else 0)
            for r in rrows
        )
        entry = {
            "code": code,
            "description": lrows[0]["description"],
            "left_qty": left_qty,
            "right_qty": right_qty,
            "unit": lrows[0]["unit"] or rrows[0]["unit"],
            "left_occurrences": len(lrows),
            "right_occurrences": len(rrows),
        }
        common.append(entry)
        if len(lrows) != len(rrows):
            occurrence_diffs.append(entry)
        if left_qty != right_qty:
            qty_diffs.append(entry)
        if (lrows[0]["unit"] or "") != (rrows[0]["unit"] or ""):
            limitations.append(f"unit_mismatch:{code}")
    claims = {
        "common": common,
        "exclusive_left": [
            {"code": c, "description": grouped[left][c][0]["description"]}
            for c in sorted(left_codes - right_codes)
        ],
        "exclusive_right": [
            {
                "code": c,
                "description": grouped[right][c][0]["description"],
            }
            for c in sorted(right_codes - left_codes)
        ],
        "qty_differences": qty_diffs,
        "occurrence_differences": occurrence_diffs,
    }
    all_codes = left_codes | right_codes
    rejected = 0
    for pair in (proposal or {}).get("proposed_pairs") or ():
        if not isinstance(pair, Mapping):
            rejected += 1
            continue
        for key in ("left_code", "right_code"):
            ref = pair.get(key)
            if ref is not None and str(ref) not in all_codes:
                rejected += 1
    if rejected:
        limitations.append(f"unsupported_proposal_refs:{rejected}")
    verdict = (
        "agreement"
        if not claims["exclusive_left"]
        and not claims["exclusive_right"]
        and not qty_diffs
        and not occurrence_diffs
        else "differences_found"
    )
    return {
        "verdict": verdict,
        "claims": claims,
        "limitations": tuple(limitations),
        "source_ids": (left, right),
    }


def _render_evidence_comparison(result: Mapping[str, Any]) -> str:
    """Deterministic PT-BR comparison render — verbatim evidence
    values only; every line traces to a verified record ref."""
    claims = result["claims"]
    left, right = result["source_ids"]
    lines = ["**Comparação das estruturas:**", ""]
    lines.append(f"**Componentes comuns ({len(claims['common'])}):**")
    for e in claims["common"]:
        lines.append(
            f"- {e['code']} — {e['description']} "
            f"(qtd {e['left_qty']} × {e['right_qty']} {e['unit'] or ''})"
            .rstrip()
        )
    if claims["exclusive_left"]:
        lines.append("")
        lines.append(
            f"**Exclusivos de {left} "
            f"({len(claims['exclusive_left'])}):**"
        )
        for e in claims["exclusive_left"]:
            lines.append(f"- {e['code']} — {e['description']}")
    if claims["exclusive_right"]:
        lines.append("")
        lines.append(
            f"**Exclusivos de {right} "
            f"({len(claims['exclusive_right'])}):**"
        )
        for e in claims["exclusive_right"]:
            lines.append(f"- {e['code']} — {e['description']}")
    if claims["qty_differences"]:
        lines.append("")
        lines.append("**Diferenças de quantidade:**")
        for e in claims["qty_differences"]:
            lines.append(
                f"- {e['code']}: {e['left_qty']} vs {e['right_qty']} "
                f"{e['unit'] or ''}".rstrip()
            )
    if claims["occurrence_differences"]:
        lines.append("")
        lines.append("**Diferenças hierárquicas (ocorrências):**")
        for e in claims["occurrence_differences"]:
            lines.append(
                f"- {e['code']}: {e['left_occurrences']} ocorrências "
                f"em {left} vs {e['right_occurrences']} em {right}"
            )
    if result["limitations"]:
        lines.append("")
        lines.append("**Limitações:**")
        for lim in result["limitations"]:
            lines.append(f"- {lim}")
    return "\n".join(lines)



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

# Provider-semantic errors where the capability surface changed under
# the initial selection — eligible for one bounded repair round.

# Owner-side contract/admissibility rejections (a remote capability
# error reported by the specialist itself — never transport, auth or
# timeout): eligible for ONE bounded contextual-recovery round that
# consults the group's DISCOVERY vocabulary and re-proposes
# arguments under the real owner contract (C3 contextual discovery).

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











# Loose identifier candidates are business codes first — a field whose
# canonical name *starts* with a code/number family is as anchorable
# as a suffixed one (``codigo_processo``, ``numero_serie``,
# ``code_product``).

# A UUID-valued identifier is a surrogate key — acceptable verbatim
# evidence, but a poor conversational subject when a human-readable
# business code exists in the same record.





# Generic resolver-step helpers (§6.140): a RESOLVER is a role, never
# a tool class — any non-mutating same-owner capability whose result
# may supply evidence for a missing target input. All owner data is
# sanitized/bounded; resolved values must provably occur in the owner
# result, and multiple plausible entities produce a bounded
# clarification — never a silent selection.

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



def _prior_observation_context(
    prior_turns: tuple[ConversationContextTurn, ...],
) -> dict[str, Any] | None:
    """Bounded untrusted prior observation for the selection proposal.

    The model interprets references. This block does not count
    identifiers, detect list wording, or grant provenance.
    """
    # Doc 242 leftover repair: the removed continuation machinery took
    # `_prior_result_turn` with it — the prior observation is simply
    # the latest DELIA_RESULT turn (untrusted context, never authority).
    prior = next(
        (
            turn
            for turn in reversed(prior_turns)
            if getattr(turn, "kind", None) is TurnKind.DELIA_RESULT
        ),
        None,
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





_IDENTIFIER_ARG_KEY_RE = re.compile(
    r"(^id$|_id$|^code$|_code$|_reference$)", re.IGNORECASE
)
_IDENTIFIER_LITERAL_RE = re.compile(r"[A-Za-z]{2,}[-_]\d{3,}|\d{5,}")


def _workspace_identifier_literals(
    workspace_context: "WorkspaceContext | None",
) -> str:
    """Space-joined entity identifiers the workspace declares.

    Untrusted client context consulted only to decide whether an
    identifier-typed requirement is *resolvable* this turn — it
    never authorizes an action and never becomes an argument value
    on its own; the model still selects the candidate and binds the
    field.
    """
    if workspace_context is None:
        return ""
    refs = getattr(workspace_context, "entity_refs", ()) or ()
    return " ".join(
        str(ref.entity_id)
        for ref in refs
        if getattr(ref, "entity_id", None)
    )


def _resolvable_identifier_literals(
    workspace_context: "WorkspaceContext | None",
    prior_turns: tuple[ConversationContextTurn, ...] = (),
) -> str:
    """Workspace entity ids plus prior-observation excerpt text.

    A referent the user binds to earlier DELIA output ("ele",
    "esses") resolves an identifier requirement exactly like a
    workspace literal: the untrusted excerpt never authorizes an
    action and never becomes an argument value on its own — it only
    proves the identifier is *available* for the model to bind.
    """
    literals = _workspace_identifier_literals(workspace_context)
    observation = _prior_observation_context(prior_turns)
    if observation:
        excerpt = str(observation.get("untrusted_excerpt") or "")
        if excerpt:
            literals = f"{literals} {excerpt}".strip()
    return literals


def _candidate_needs_missing_identifier(
    candidate: Mapping[str, Any],
    input_text: str,
    resolvable_literals: str = "",
) -> bool:
    """True when the candidate declares a required identifier-typed
    argument and the request supplies no identifier-like literal.

    Same dead-end rule the resolver stage applies: a candidate that
    cannot run without a missing identifier can never satisfy the
    turn, so it is excluded from the selection set — selection stays
    a model proposal over the executable remainder.
    """
    required = candidate.get("required_arguments")
    if not isinstance(required, (list, tuple)) or not required:
        return False
    if not any(
        _IDENTIFIER_ARG_KEY_RE.search(str(r)) for r in required
    ):
        return False
    haystack = (input_text or "") + " " + resolvable_literals
    return not _IDENTIFIER_LITERAL_RE.search(haystack)




















def _elide_unproven_optional_args(
    arguments: Mapping[str, Any],
    descriptor: ProviderCapability,
    input_text: str,
    workspace_context: WorkspaceContext | None,
) -> dict[str, Any]:
    """Elide OPTIONAL argument values the turn cannot support —
    never rewrite, never invent.

    The arguments contract forbids fabricated values; an optional
    field carrying an empty string, a literal "none"/"null" marker,
    or a value absent from every provenance source (user message,
    workspace context, owner-declared schema literals) is an invented
    constraint that would make the owner reject or mis-filter the
    call. Free-text search fields are exempt — reformulating the
    governed subject is their declared job. Required keys are
    untouched — an unsatisfiable required input stays a
    missing-input signal.
    """

    _, required = _schema_keys(descriptor)
    haystack_parts = [input_text or ""]
    if workspace_context is not None:
        haystack_parts.append(workspace_context.to_prompt_block())
    haystack_parts.append(_schema_declared_literals(descriptor))
    haystack = "\n".join(haystack_parts)
    cleaned: dict[str, Any] = {}
    for key, value in list(arguments.items())[:MAX_ARGUMENT_KEYS]:
        if str(key) in required:
            cleaned[key] = value
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in {"none", "null"}:
                continue
            if _TEMPORAL_ARG_KEY_RE.search(str(key)) and (
                parse_temporal_value(stripped) is not None
                or str(key).endswith("_field")
            ) and stripped not in haystack:
                # Invented temporal/period filter — no provenance.
                continue
        cleaned[key] = value
    return cleaned


_NULL_LITERAL_ARG_VALUES = frozenset({"none", "null"})

# Orchestration block field names the arguments payload itself
# projects (subject/declared-requirements/evidence context). A model
# that echoes one of these keys back inside "arguments" reproduced
# our own context field, not an owner-declared input — recognizable
# artifact, dropped only when the owner schema does not declare it.
_ORCHESTRATION_BLOCK_ARG_KEYS = frozenset(
    {
        "business_subject",
        "declared_requirements",
        "owner_vocabulary",
        "foreign_evidence",
        "relevance_feedback",
    }
)


def _drop_orchestration_field_args(
    arguments: Mapping[str, Any],
    schema: Mapping[str, Any] | None,
) -> dict[str, Any]:
    declared = (
        schema.get("properties") if isinstance(schema, Mapping) else None
    )
    declared = declared if isinstance(declared, Mapping) else {}
    return {
        key: value
        for key, value in list(arguments.items())[:MAX_ARGUMENT_KEYS]
        if key in declared
        or str(key) not in _ORCHESTRATION_BLOCK_ARG_KEYS
    }


def _drop_null_literal_args(
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    """Drop literal ``None``/``"None"``/``"null"`` markers from a
    proposal — model serialization artifacts, never business values.
    Applied before schema validation so a required key carrying the
    marker still surfaces as a missing input instead of reaching the
    owner."""
    return {
        key: value
        for key, value in list(arguments.items())[:MAX_ARGUMENT_KEYS]
        if value is not None
        and not (
            isinstance(value, str)
            and value.strip().lower() in _NULL_LITERAL_ARG_VALUES
        )
    }


_TEMPORAL_ARG_KEY_RE = re.compile(
    r"date|time|_from|^from|_to$|^to$|since|until|period|competencia"
    r"|year|month|day",
    re.IGNORECASE,
)


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




# Material obligation coverage states for agent investigation finalize
# (doc 233 rework). Mapped onto SubObjectiveTracker vocabulary when
# equivalent; kept as explicit labels for finalize projections.
OBLIGATION_REQUIRED = "REQUIRED"
OBLIGATION_SATISFIED = "SATISFIED"
OBLIGATION_UNSATISFIED = "UNSATISFIED"
OBLIGATION_UNAVAILABLE = "UNAVAILABLE"
OBLIGATION_INCONCLUSIVE = "INCONCLUSIVE"

_OBLIGATION_STATES = frozenset(
    {
        OBLIGATION_REQUIRED,
        OBLIGATION_SATISFIED,
        OBLIGATION_UNSATISFIED,
        OBLIGATION_UNAVAILABLE,
        OBLIGATION_INCONCLUSIVE,
    }
)


@dataclasses.dataclass(frozen=True, slots=True)
class SemanticInvestigationPlan:
    """Application-validated investigation plan from the Agent tool.

    Semantic proposal only — never authorization. Target identities and
    evidence_needed are the REF05/material-obligation contract for
    finalize; comparison_requested comes from the typed ``_TurnGoal``.
    """

    goal: "OperationalCapabilityOrchestrator._TurnGoal"
    target_identities: tuple[str, ...] = ()
    evidence_needed: tuple[str, ...] = ()


def _is_business_evidence_attempt(
    attempt: GovernedCapabilityAttempt,
) -> bool:
    if attempt.status is not GovernedCapabilityStatus.SUCCESS:
        return False
    if not (attempt.content or "").strip():
        return False
    if attempt.provenance is None or not attempt.provenance.is_complete:
        return False
    if "discovery_metadata_observation" in attempt.limitations:
        return False
    # An owner miss ("no records") is not a business fact. Joining
    # those texts must not become a grounded observation.
    content = (attempt.content or "").strip()
    if content == EMPTY_RESULT_TEXT or content.startswith(
        f"{EMPTY_RESULT_TEXT}\n"
    ):
        return False
    outcome = attempt.outcome
    if outcome is not None and not outcome.is_complete:
        return False
    return True


def _authoritative_structure_root(
    attempt: GovernedCapabilityAttempt,
) -> str | None:
    """REF05 oracle: unique min-depth structure root from owner records.

    Never derived from rendered content/Markdown/text mentions.
    Prefer an owner-declared ``data.root.code`` when present — child
    BOM rows alone must not redefine the product identity.
    """
    outcome = attempt.outcome
    if outcome is None or not outcome.is_complete:
        return None
    if attempt.provenance is None or not attempt.provenance.is_complete:
        return None
    if "discovery_metadata_observation" in attempt.limitations:
        return None
    structured = outcome.structured
    if isinstance(structured, Mapping):
        data = structured.get("data")
        if isinstance(data, Mapping):
            declared = data.get("root")
            if isinstance(declared, Mapping):
                code = declared.get("code")
                if isinstance(code, str) and code.strip():
                    return code.strip()
            elif isinstance(declared, str) and declared.strip():
                return declared.strip()
    records = _comparison_records(outcome)
    if not records:
        return None
    rows = _flatten_evidence_records(records)
    if not rows:
        return None
    min_depth = min(len(row["path"]) for row in rows)
    roots = [row for row in rows if len(row["path"]) == min_depth]
    if len(roots) != 1:
        return None
    code = roots[0].get("code")
    if not isinstance(code, str) or not code.strip():
        return None
    return code.strip()


def _bind_identifier_args_from_utterance(
    schema: Mapping[str, Any] | None,
    input_text: str,
) -> dict[str, Any] | None:
    """Schema-driven fallback when candidate arggen fails.

    Binds only when exactly one required identifier-shaped field is
    declared and the utterance contains identifier literals. Does not
    invent values beyond literals already present in the user text.
    """
    if not isinstance(schema, Mapping):
        return None
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, Mapping):
        return None
    required_names = (
        [str(name) for name in required]
        if isinstance(required, (list, tuple))
        else []
    )
    id_keys: list[str] = []
    for key in required_names:
        if not _IDENTIFIER_ARG_KEY_RE.search(key):
            continue
        node = properties.get(key)
        if not isinstance(node, Mapping):
            continue
        node_type = node.get("type")
        if node_type not in (None, "string"):
            continue
        id_keys.append(key)
    if len(id_keys) != 1:
        return None
    literals = _IDENTIFIER_LITERAL_RE.findall(input_text or "")
    unique = list(dict.fromkeys(str(item) for item in literals if item))
    if not unique:
        return None
    # Prefer the longest literal (more specific business codes).
    value = max(unique, key=len)
    return {id_keys[0]: value}


def _bind_attempt_to_target(
    attempt: GovernedCapabilityAttempt, target: str
) -> bool:
    """True only when authoritative root equals the requested identity."""
    needle = (target or "").strip()
    if not needle:
        return False
    root = _authoritative_structure_root(attempt)
    if root is None:
        return False
    return root.casefold() == needle.casefold()


def _normalize_identity_tuple(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        return ()
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        token = item.strip()
        if not token or len(token) > 64:
            continue
        out.append(token)
    # Preserve order, drop duplicates (case-insensitive).
    seen: set[str] = set()
    unique: list[str] = []
    for token in out[:16]:
        key = token.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(token)
    return tuple(unique)


def _attempt_satisfies_obligation(
    attempt: GovernedCapabilityAttempt, obligation: str
) -> bool:
    """Obligation match via owner-authoritative identity only.

    Satisfied when the obligation equals the authoritative structure
    root, or an owner-record code under a compatible root. Capability
    names, specialist ids and provenance source_id alone never prove
    that the requested business fact was acquired (doc 237 R-E2).
    Child codes under a *different* root never satisfy REF05.
    """
    needle = (obligation or "").strip()
    if not needle:
        return False
    key = needle.casefold()
    if not _is_business_evidence_attempt(attempt):
        return False
    root = _authoritative_structure_root(attempt)
    if root is not None and root.casefold() == key:
        return True
    outcome = attempt.outcome
    if outcome is None or not outcome.is_complete:
        return False
    records = _comparison_records(outcome)
    if not records:
        return False
    rows = _flatten_evidence_records(records)
    for row in rows:
        code = row.get("code")
        if not isinstance(code, str) or not code.strip():
            continue
        if code.strip().casefold() != key:
            continue
        # Wrong-root child mention is not the requested identity.
        if root is not None and root.casefold() != key:
            continue
        return True
    return False


def _evaluate_material_obligations(
    *,
    obligations: tuple[str, ...],
    business: tuple[GovernedCapabilityAttempt, ...],
) -> tuple[tuple[str, str], ...]:
    """Return ``(obligation_id, state)`` for each material obligation."""
    results: list[tuple[str, str]] = []
    used: set[int] = set()
    for obligation in obligations:
        matched = None
        for index, attempt in enumerate(business):
            if index in used:
                continue
            if not _attempt_satisfies_obligation(attempt, obligation):
                continue
            matched = attempt
            used.add(index)
            break
        if matched is None:
            unavailable = any(
                item.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
                for item in business
            )
            state = (
                OBLIGATION_UNAVAILABLE
                if unavailable
                else OBLIGATION_UNSATISFIED
            )
            results.append((obligation, state))
            continue
        if matched.provenance is None or not matched.provenance.is_complete:
            results.append((obligation, OBLIGATION_INCONCLUSIVE))
            continue
        results.append((obligation, OBLIGATION_SATISFIED))
    return tuple(results)


def _finalize_agent_collected_attempts(
    orchestrator: "OperationalCapabilityOrchestrator",
    *,
    input_text: str,
    collected: tuple[GovernedCapabilityAttempt, ...],
    correlation: str,
    workspace_context: WorkspaceContext | None,
    deadline: TurnDeadline,
    unbound_outcome: str | None,
    plan: SemanticInvestigationPlan | None = None,
    clarification_question: str | None = None,
    composed_attempt: GovernedCapabilityAttempt | None = None,
) -> GovernedCapabilityAttempt:
    """Goal-coverage finalizer for Pydantic AI tool observations.

    Native-first: clarification and optional agent-requested composition
    take precedence. Typed plan remains optional (not mandatory for
    simple READ). Never classifies intent via regex or binds REF05 via
    rendered text mentions.
    """
    if clarification_question:
        missing = _normalize_identity_tuple(
            plan.evidence_needed if plan is not None else ()
        ) or ("clarification",)
        content = (
            str(clarification_question).strip()[:MAX_RENDER_CONTENT_CHARS]
            or _clarification_content(missing)
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
            correlation_id=correlation,
            content=content,
            limitations=("agent_requested_clarification",),
            error_code="investigation_clarification_required",
            admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
        )

    business = tuple(
        item for item in collected if _is_business_evidence_attempt(item)
    )

    def _partial_coverage() -> GovernedCapabilityAttempt | None:
        pending = _uncovered_named_identifiers(input_text, business)
        if not pending:
            return None
        parts: list[str] = []
        for index, item in enumerate(business):
            body = (item.content or "").strip()
            if body:
                parts.append(f"[obs:{index}]\n{body}")
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id=correlation,
            content=(
                "\n\n---\n\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]
                or None
            ),
            limitations=tuple(
                ["identifier_coverage_incomplete"]
                + [f"uncovered_identifier:{item}" for item in pending[:8]]
            ),
            error_code="investigation_partial_coverage",
            admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
        )
    limitations: list[str] = []
    comparison = bool(
        plan is not None
        and (
            plan.goal.comparison_requested
            or plan.goal.goal_class == "compare"
        )
    )
    targets = plan.target_identities if plan is not None else ()
    obligations = (
        plan.evidence_needed
        if plan is not None and plan.evidence_needed
        else targets
    )

    # R-E1: agent-requested composition is partial observation — never
    # terminal SUCCESS while declared material obligations remain open.
    # Evaluated before the empty-collected gate so a verified compose
    # with satisfied (or undeclared) obligations remains usable.
    if (
        composed_attempt is not None
        and composed_attempt.status is GovernedCapabilityStatus.SUCCESS
        and composed_attempt.verified_composition is not None
    ):
        if obligations:
            coverage = _evaluate_material_obligations(
                obligations=obligations,
                business=business,
            )
            if any(state != OBLIGATION_SATISFIED for _, state in coverage):
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                    limitations=tuple(
                        [LIMITATION_INSUFFICIENT_EVIDENCE]
                        + ["material_obligations_incomplete"]
                        + [
                            f"obligation_{state.lower()}:{oid}"
                            for oid, state in coverage
                            if state != OBLIGATION_SATISFIED
                        ]
                        + ["composition_does_not_satisfy_goal"]
                    )[:24],
                    error_code="investigation_incomplete_coverage",
                    verified_composition=composed_attempt.verified_composition,
                )
        return composed_attempt

    if not collected:
        _logger.info(
            "orchestration stage=semantic_finalize "
            "decision=no_tool_observations correlation_id=%s",
            correlation,
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id=correlation,
            admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
            limitations=(LIMITATION_INSUFFICIENT_EVIDENCE,),
            error_code="investigation_no_tool_observations",
        )

    if comparison:
        if plan is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=(
                    LIMITATION_INSUFFICIENT_EVIDENCE,
                    "goal_plan_undeclared",
                ),
                error_code="investigation_goal_plan_required",
            )
        if len(targets) < 2:
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            limitations.append("comparison_targets_undeclared")
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_incomplete_coverage",
            )

        coverage = _evaluate_material_obligations(
            obligations=obligations or targets,
            business=business,
        )
        for obligation_id, state in coverage:
            if state != OBLIGATION_SATISFIED:
                limitations.append(f"obligation_{state.lower()}:{obligation_id}")
        if any(state != OBLIGATION_SATISFIED for _, state in coverage):
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            limitations.append("material_obligations_incomplete")
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_incomplete_coverage",
            )

        # Bind each declared target to a distinct authoritative root.
        sources: dict[str, tuple[Mapping[str, Any], ...]] = {}
        lineages: dict[str, tuple] = {}
        observations: list[str] = []
        bound_attempts: dict[str, GovernedCapabilityAttempt] = {}
        for target in targets:
            match = next(
                (
                    item
                    for item in business
                    if _bind_attempt_to_target(item, target)
                    and _authoritative_structure_root(item) is not None
                    and _authoritative_structure_root(item).casefold()
                    not in {
                        _authoritative_structure_root(prior).casefold()
                        for prior in bound_attempts.values()
                        if _authoritative_structure_root(prior) is not None
                    }
                ),
                None,
            )
            if match is None:
                limitations.append("ref05_target_unbound")
                limitations.append(f"ref05_missing_target:{target}")
                continue
            root = _authoritative_structure_root(match)
            assert root is not None
            if root.casefold() != target.casefold():
                limitations.append("ref05_target_unbound")
                limitations.append(f"ref05_missing_target:{target}")
                continue
            records = _comparison_records(match.outcome)  # type: ignore[arg-type]
            sources[root] = records
            lineages[root] = match.provenance.source_refs  # type: ignore[union-attr]
            observations.append(match.outcome.provenance.observed_at)  # type: ignore[union-attr]
            bound_attempts[target] = match

        if limitations:
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_target_binding_failed",
            )

        if len(sources) != len(targets) or len(sources) < 2:
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            limitations.append("comparison_source_missing")
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_incomplete_coverage",
            )

        # Compose uses the first two bound roots in target declaration
        # order (order of acquisition must not decide success).
        ordered_roots = tuple(
            _authoritative_structure_root(bound_attempts[t])  # type: ignore[arg-type]
            for t in targets
            if t in bound_attempts
        )
        if len(ordered_roots) < 2:
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_incomplete_coverage",
            )
        compose_sources = {
            ordered_roots[0]: sources[ordered_roots[0]],
            ordered_roots[1]: sources[ordered_roots[1]],
        }
        composed = orchestrator._compose_multi_evidence(
            compose_sources,
            # Pass-through empty — composition proposal uses owner
            # records only for verified facts (ADR 58).
            "",
            correlation=correlation,
            workspace_context=workspace_context,
            deadline=deadline,
        )
        if composed is None:
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_composition_unavailable",
            )
        content, comp_limitations, verdict = composed
        if verdict not in ("agreement", "differences_found"):
            limitations.extend(comp_limitations)
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                limitations=tuple(dict.fromkeys(limitations))[:24],
                error_code="investigation_composition_unverified",
            )
        verified = VerifiedCompositeEvidence(
            source_roots=(ordered_roots[0], ordered_roots[1]),
            source_lineage=(
                lineages[ordered_roots[0]],
                lineages[ordered_roots[1]],
            ),
            observed_at=max(observations),
            correlation_id=correlation,
            verdict=verdict,
        )
        _logger.info(
            "orchestration stage=semantic_finalize "
            "decision=verified_composition verdict=%s "
            "correlation_id=%s",
            verdict,
            correlation,
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            content=content,
            limitations=tuple(comp_limitations)[:24],
            verified_composition=verified,
        )

    # Non-compare: optional single-target REF05 via authoritative root.
    if len(business) == 1:
        if targets:
            if len(targets) != 1 or not _bind_attempt_to_target(
                business[0], targets[0]
            ):
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                    limitations=(
                        LIMITATION_INSUFFICIENT_EVIDENCE,
                        "ref05_target_unbound",
                        *(
                            f"ref05_missing_target:{token}"
                            for token in targets[:8]
                        ),
                    ),
                    error_code="investigation_target_binding_failed",
                )
        if obligations and obligations != targets:
            coverage = _evaluate_material_obligations(
                obligations=obligations,
                business=business,
            )
            if any(state != OBLIGATION_SATISFIED for _, state in coverage):
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                    limitations=tuple(
                        [LIMITATION_INSUFFICIENT_EVIDENCE]
                        + [
                            f"obligation_{state.lower()}:{oid}"
                            for oid, state in coverage
                            if state != OBLIGATION_SATISFIED
                        ]
                    )[:24],
                    error_code="investigation_incomplete_coverage",
                )
        partial = _partial_coverage()
        if partial is not None:
            return partial
        return business[0]

    if business:
        # R-E4: preserve every verified observation — do not drop all
        # but the last when no structure composition applies.
        if obligations:
            coverage = _evaluate_material_obligations(
                obligations=obligations,
                business=business,
            )
            if any(state != OBLIGATION_SATISFIED for _, state in coverage):
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                    limitations=tuple(
                        [LIMITATION_INSUFFICIENT_EVIDENCE]
                        + ["material_obligations_incomplete"]
                        + [
                            f"obligation_{state.lower()}:{oid}"
                            for oid, state in coverage
                            if state != OBLIGATION_SATISFIED
                        ]
                    )[:24],
                    error_code="investigation_incomplete_coverage",
                )
        partial = _partial_coverage()
        if partial is not None:
            return partial
        parts: list[str] = []
        for index, item in enumerate(business):
            body = (item.content or "").strip()
            if not body:
                continue
            handle = f"obs:{index}"
            parts.append(f"[{handle}]\n{body}")
        joined = "\n\n---\n\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]
        last = business[-1]
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            content=joined or last.content,
            limitations=tuple(
                list(last.limitations)
                + ["multiple_observations_without_compose"]
            )[:24],
            provenance=last.provenance,
            outcome=last.outcome,
            markdown_content=last.markdown_content,
        )

    last = collected[-1]
    _logger.info(
        "orchestration stage=semantic_finalize "
        "decision=no_business_evidence status=%s correlation_id=%s",
        last.status.value,
        correlation,
    )
    pending = _uncovered_named_identifiers(input_text, ())
    gap_limitations = list(last.limitations) + [
        LIMITATION_INSUFFICIENT_EVIDENCE
    ]
    if pending:
        gap_limitations.append("identifier_coverage_incomplete")
        gap_limitations.extend(
            f"uncovered_identifier:{item}" for item in pending[:8]
        )
    return GovernedCapabilityAttempt(
        status=last.status
        if last.status is not GovernedCapabilityStatus.SUCCESS
        else GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id=correlation,
        content=last.content,
        limitations=tuple(dict.fromkeys(gap_limitations))[:24],
        error_code=(
            last.error_code
            if last.error_code
            in {"authz_denied", "owner_query_miss", "catalog_owner_unavailable"}
            else "investigation_no_business_evidence"
        ),
        admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
        provenance=last.provenance,
        outcome=last.outcome,
    )


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









# Canonical sensitive credential concepts. Keys are normalized
def _json_block(block: Any) -> str:
    return json.dumps(block, ensure_ascii=False, default=str)


def _truncate_text_field(
    block: MutableMapping[str, Any], key: str, keep: int
) -> bool:
    """Structural reduction step: bound one text field in-place.

    Only applied to fields that are already bounded excerpts —
    never on required schema parts, identifiers, codes or record
    values.
    """
    value = block.get(key)
    if isinstance(value, str) and len(value) > keep:
        block[key] = value[:keep]
        return True
    return False




def _drop_block_fields(
    block: MutableMapping[str, Any], *keys: str
) -> bool:
    """Structural step: drop optional fields entirely."""
    changed = False
    for key in keys:
        if block.pop(key, None) is not None:
            changed = True
    return changed


def _omit_tail_entries(
    block: MutableMapping[str, Any], list_key: str, marker_key: str
) -> bool:
    """Structural step: drop one trailing entry, truthfully marked."""
    entries = block.get(list_key)
    if not isinstance(entries, list) or not entries:
        return False
    entries.pop()
    block[marker_key] = block.get(marker_key, 0) + 1
    return True


def _fit_json_block(
    block: Any,
    budget: int,
    *steps: Callable[[], bool],
) -> str:
    """Serialize ``block`` to JSON within ``budget`` — structure only.

    ``steps`` are ordered structural reductions; each mutates
    ``block`` and returns True while it still reduces. They run as a
    ladder — a step is applied until exhausted, then the next — until
    the payload fits or all are exhausted. The serialized result is
    always valid JSON, never a mid-document cut; when every step is
    exhausted the minimal valid document is emitted — ``budget`` is a
    compaction target, not a hard contract bound: the typed
    boundaries (MAX_INPUT_CHARS transport, CONTEXT_TOO_LARGE on a
    declared context window) remain the guards downstream. The
    over-target emission is logged so the event stays traceable.
    """
    payload = _json_block(block)
    if len(payload) <= budget:
        return payload
    while len(payload) > budget:
        if not any(step() for step in steps):
            _logger.warning(
                "projection fit exhausted: block %d chars exceeds "
                "compaction target %d — emitting whole valid JSON; "
                "typed transport/context bounds apply downstream",
                len(payload),
                budget,
            )
            return payload
        payload = _json_block(block)
    return payload


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

# Refactor R1 (plan 125 / M01): instruction *text* lives in the
# governed versioned resource config/orchestration_instructions
# .delpi.json, loaded fail-closed by composition and injected at
# construction — never a second copy inside this module. The
# instruction ids below remain the typed lineage contract; the fused
# capability+goal variant shares the selection instruction id and is
# keyed distinctly in the resource.
ORCHESTRATION_INSTRUCTION_KEYS = frozenset(
    {
        INTERACTION_ADMISSION_INSTRUCTION_ID,
        EVIDENCE_COMPOSITION_INSTRUCTION_ID,
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
_LAST_CATALOG_FAILURES: contextvars.ContextVar[tuple[str, ...]] = (
    contextvars.ContextVar("_LAST_CATALOG_FAILURES", default=())
)
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

# Canonical-designation retry (Task 21): at most ONE deterministic
# re-invoke per interaction — the rebound is contract application
# (governed subject, singularized), never a model proposal, so it
# does not consume the shared model recovery round.

# Sequencing-strategy ledger (H5 experiment, task
# DELIA-C3-SEQUENCING-RECOVERY-AB-01): an OPT-IN ambient carrier a
# sequencing engine may bind per attempt to observe established
# native_assessment decisions during the bounded recovery round.
# Unbound (default) = the runtime behaves exactly as if it did not
# exist — Engine A never binds it. The ledger records DECISIONS only
# (status string + target key + goal fingerprint); it never carries
# authorization, arguments, evidence payloads or chain-of-thought.












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

def _listing_failure_is_transient(code: str) -> bool:
    """Transport/timeout listing failures may be retried once.

    Authorization and contract rejections are definitive for the turn.
    """
    folded = str(code or "").casefold()
    if any(
        token in folded
        for token in ("denied", "forbidden", "unauthorized", "authz")
    ):
        return False
    return any(
        token in folded
        for token in ("timeout", "unavailable", "transport", "connection")
    )


def _uncovered_named_identifiers(
    input_text: str,
    business: tuple[GovernedCapabilityAttempt, ...]
    | list[GovernedCapabilityAttempt],
) -> list[str]:
    """User identifier literals with no authoritative owner root.

    Coverage uses owner records only. Rendered text and capability
    names do not satisfy an identifier.
    """
    found = list(
        dict.fromkeys(_IDENTIFIER_LITERAL_RE.findall(input_text or ""))
    )
    covered: set[str] = set()
    for attempt in business:
        root = _authoritative_structure_root(attempt)
        if isinstance(root, str) and root.strip():
            covered.add(root.strip().casefold())
    return [item for item in found if item.casefold() not in covered]


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
        # Governed presentation labels resolve field names in every
        # path (detail, list, comparison) — absent the fallback stays
        # neutral.
        self._field_labels = dict(field_labels or {})

    def _instruction(self, key: str) -> str:
        """Declarative instruction text by resource key — injected,
        never authored here; empty only in tests without the resource."""
        return self._instructions.get(key, "")


    def _run_governed_attempts(
        self,
        attempt_once: Callable[
            [str, TurnDeadline], GovernedCapabilityAttempt
        ],
        *,
        correlation_id: str | None,
        confirmation: Mapping[str, Any] | None,
        activity_sink: ActivityEventSink | None,
        cancel_check: Callable[[], bool] | None,
        turn_deadline: TurnDeadline | None,
    ) -> GovernedCapabilityAttempt:
        """Shared governed attempt runner: binds request-scoped
        context (activity sink, resume checkpoint, cancellation,
        relevance flag), anchors the monotonic interaction budget
        and drives the bounded attempt/resume loop around a caller-
        supplied single-attempt callable. Engine A passes
        self._attempt; alternative engines pass one graph
        invocation — the retry/budget/cancel controls stay shared
        and never re-implemented per engine (doc 194)."""
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
                    completed = attempt_once(correlation, deadline)
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



    def _compose_multi_evidence(
        self,
        sources: dict[str, tuple[Mapping[str, Any], ...]],
        input_text: str,
        *,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline | None,
    ) -> tuple[str, tuple[str, ...], str] | None:
        """Doc 222 E4 — governed multi-evidence composition.

        The model only proposes candidate correspondences between
        records of different authorized sources; the deterministic
        verifier computes every fact over the full projected
        coverage and rejects fabricated/out-of-range refs. Output
        is rendered verbatim from verified evidence — no model
        factual prose (ADR 58 / §6.145)."""
        instruction = self._instruction(EVIDENCE_COMPOSITION_INSTRUCTION_ID)
        if not instruction or len(sources) != 2:
            return None
        block = {
            sid: _flatten_evidence_records(records)
            for sid, records in sources.items()
        }
        proposal = self._propose(
            input_text,
            block_tag="evidence_sources",
            block_payload=_fit_json_block(block, MAX_SURFACE_CHARS),
            instruction_id=EVIDENCE_COMPOSITION_INSTRUCTION_ID,
            instruction=instruction,
            instruction_version=SELECTION_INSTRUCTION_VERSION,
            expected_fields=("proposed_pairs",),
            input_kind="evidence_composition",
            allowed_keys=frozenset({"proposed_pairs", "limitations"}),
            workspace_context=workspace_context,
            correlation=correlation,
            deadline=deadline,
        )
        result = _verify_evidence_composition(sources, proposal)
        _logger.info(
            "orchestration stage=evidence_composition decision=%s "
            "sources=%d correlation_id=%s",
            result["verdict"],
            len(sources),
            correlation,
        )
        return (_render_evidence_comparison(result),
                tuple(result["limitations"]), result["verdict"])






    _GOAL_CLASSES = frozenset(
        {"read", "analyze", "compare", "create_or_modify", "clarify"}
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
        # D5 evidence-intent correspondence (doc 124): True only when a
        # validated proposal declares the user asked about the published
        # contract/schema itself. Owner contract metadata composes an
        # answer only for declared contract subjects — absent means
        # unproven intent, never schema-dump-by-default.
        contract_subject: bool = False












    @dataclasses.dataclass(frozen=True, slots=True)
    class _ForeignResult:
        """Outcome of the bounded foreign non-mutating step."""

        outcome: SpecialistOutcome | None = None
        evidence: str | None = None
        missing_inputs: tuple[str, ...] = ()
        failed: bool = False




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


    # ---- CRI E3 — grounded conversational composition ------------


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
                # One bounded retry for a transient listing failure.
                # A timeout is not proof the owner has no capabilities.
                retried = False
                if (
                    deadline is not None
                    and deadline.remaining_seconds() > 15
                    and _listing_failure_is_transient(exc.code)
                ):
                    try:
                        surface = provider.list_groups(
                            correlation_id=correlation,
                            timeout_seconds=min(
                                15.0, deadline.remaining_seconds()
                            ),
                        )
                        retried = True
                    except CapabilityProviderError as retry_exc:
                        failures.append(exc.code)
                        failures.append(retry_exc.code)
                        continue
                if not retried:
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
                if (
                    instruction_id == INTERACTION_ADMISSION_INSTRUCTION_ID
                    and exc.code == TIMEOUT
                ):
                    # Admission is a classifier. A timeout already
                    # consumed its useful bound; repeating it delays
                    # the live catalog and the owner reads that must
                    # still fit in the same turn.
                    raise _StageDeadlineExceeded("model_timeout") from exc
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
        if interaction_class == "surface_inquiry" and requires:
            # Declared-invariant violation: the instruction defines
            # surface_inquiry as "requires stays false" — a true flag
            # in the same proposal makes the pair contradictory.
            # One bounded re-proposal (same malformed-output precedent
            # as the other stages); if the contradiction repeats, the
            # instruction's own asymmetry rule applies — a missed
            # owner path fabricates business facts — so it resolves
            # to the owner path, never the listing.
            _logger.info(
                "orchestration stage=interaction_admission "
                "decision=surface_inquiry_requires_contradiction "
                "correlation_id=%s",
                correlation,
            )
            try:
                retry = self._propose(
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
                    instruction=self._instruction(
                        INTERACTION_ADMISSION_INSTRUCTION_ID
                    ),
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
                retry = None
            if isinstance(retry, Mapping):
                r_raw = retry.get("requires_owner_surface")
                r_class = retry.get("interaction_class")
                if (
                    isinstance(r_class, str)
                    and r_class.strip().lower() == "surface_inquiry"
                    and r_raw is False
                ):
                    # The retry produced the coherent pair — the
                    # surface listing stands.
                    return "surface_inquiry", True
            # Persistent contradiction: the typed class is the
            # semantic statement — the deterministic surface listing
            # is bounded live metadata and never fabricates business
            # facts, so it is the fail-safe resolution.
            return "surface_inquiry", True
        if interaction_class == "surface_inquiry":
            # The typed class is the semantic statement: a surface
            # inquiry is answered by the deterministic live-surface
            # projection — bounded, read-only, never an invocation.
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

    def _project_semantic_tool_catalog(
        self,
        *,
        correlation: str,
        deadline: TurnDeadline,
        actor_user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Live READ/DISCOVERY/ANALYSIS catalog for Agent tools (doc 231).

        Write classes are omitted. Entries are untrusted metadata —
        never authorization. Schemas are size-bounded. Live Core AuthZ
        is applied by ``_groups`` (request-scoped identity); the actor
        id is logged for audit lineage only.
        """
        groups, failures = self._groups(correlation, deadline)
        catalog: list[dict[str, Any]] = []
        for group in groups.values():
            for cap in group.capabilities:
                if cap.operation_class in _WRITE_OPERATION_CLASSES:
                    continue
                if cap.operation_class not in {
                    SpecialistOperationClass.READ,
                    SpecialistOperationClass.DISCOVERY,
                    SpecialistOperationClass.ANALYSIS,
                }:
                    continue
                schema = cap.input_schema if isinstance(
                    cap.input_schema, Mapping
                ) else {}
                # Bound schema projection — property names + types only.
                props = schema.get("properties") if isinstance(
                    schema.get("properties"), Mapping
                ) else {}
                slim_props = {
                    str(name): {
                        "type": (
                            spec.get("type")
                            if isinstance(spec, Mapping)
                            else None
                        ),
                        "description": (
                            str(spec.get("description") or "")[:160]
                            if isinstance(spec, Mapping)
                            else None
                        ),
                    }
                    for name, spec in list(props.items())[:24]
                }
                catalog.append(
                    {
                        "capability_id": cap.capability_id,
                        "group_id": group.group_id,
                        "provider_id": group.provider_id,
                        "remote_name": cap.remote_name,
                        "owner": cap.owner,
                        "operation_class": cap.operation_class.value,
                        "description": (cap.description or "")[:320],
                        "input_schema": {
                            "type": "object",
                            "properties": slim_props,
                            "required": list(schema.get("required") or [])[
                                :24
                            ],
                        },
                    }
                )
        bounded = catalog[:80]
        by_owner: dict[str, int] = {}
        for entry in bounded:
            owner = str(entry.get("owner") or entry.get("provider_id") or "?")
            by_owner[owner] = by_owner.get(owner, 0) + 1
        _logger.info(
            "orchestration stage=semantic_tool_catalog "
            "decision=project actor=%s catalog_len=%d "
            "owners=%s failures=%s correlation_id=%s",
            (actor_user_id or "")[:64] or "-",
            len(bounded),
            ",".join(f"{k}:{v}" for k, v in sorted(by_owner.items())[:12])
            or "-",
            ",".join(str(item) for item in failures[:8]) or "-",
            correlation,
        )
        _LAST_CATALOG_FAILURES.set(
            tuple(str(item) for item in failures[:8])
        )
        return bounded

    def _governed_semantic_tool_invoke(
        self,
        *,
        capability_id: str,
        arguments: Mapping[str, Any],
        input_text: str,
        correlation: str,
        actor_user_id: str | None,
        session_id: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        prepare_only: bool,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt:
        """Single-capability Agent tool invoke under live gates (doc 231).

        Resolves ``capability_id`` on the fresh live surface, rejects
        write classes on this surface, validates arguments against the
        owner schema, and routes through ``_invoke_selected`` so
        discovery-first candidate binding stays Application-owned.

        AuthZ: live surface from ``_groups`` (Core identity already
        bound on the request). ``prepare_only`` cannot elevate writes —
        write classes are rejected on this tool surface. Actor/session
        are retained for audit lineage.
        """
        cap_id = (capability_id or "").strip()
        _logger.info(
            "orchestration stage=semantic_tool_invoke "
            "decision=start capability=%s actor=%s session=%s "
            "prepare_only=%s correlation_id=%s",
            cap_id[:120],
            (actor_user_id or "")[:64] or "-",
            (session_id or "")[:64] or "-",
            bool(prepare_only),
            correlation,
        )
        if not cap_id:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="capability_id_required",
            )
        groups, failures = self._groups(correlation, deadline)
        if not groups and failures:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                correlation_id=correlation,
                error_code=failures[0],
            )
        matched: tuple[str, CapabilityGroup, ProviderCapability] | None = None
        for group_key, group in groups.items():
            for cap in group.capabilities:
                if cap.capability_id == cap_id or (
                    f"{group.group_id}:{cap.remote_name}" == cap_id
                ):
                    matched = (group_key, group, cap)
                    break
            if matched is not None:
                break
        if matched is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="capability_not_on_surface",
            )
        group_key, group, descriptor = matched
        if descriptor.operation_class in _WRITE_OPERATION_CLASSES:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="write_capability_not_exposed_to_agent_tools",
            )
        # READ tool surface never executes prepare/act even when the
        # turn ceiling is prepare_only — writes stay on confirmation
        # chain. prepare_only is recorded for audit only.
        args = dict(arguments or {})
        # Generic schema binding: when the owner requires ``query`` and
        # the agent omitted it, bind the turn utterance. This does not
        # select a capability — the agent already chose the tool.
        args = _bind_missing_required_query(
            args,
            input_schema=descriptor.input_schema,
            input_text=input_text,
        )
        if descriptor.input_schema is not None:
            try:
                validated = _validate_instance(args, descriptor.input_schema)
            except Exception:
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    error_code="arguments_schema_rejected",
                )
            if validated is None:
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    error_code="arguments_schema_rejected",
                )
            args = dict(validated)
        try:
            invoked = self._invoke_selected(
                group_key,
                descriptor.remote_name,
                args,
                group,
                input_text,
                correlation,
                prior_turns=prior_turns,
                deadline=deadline,
                workspace_context=workspace_context,
            )
        except CapabilityProviderError as exc:
            return _error_attempt(correlation, exc)
        except (_StageDeadlineExceeded, TurnBudgetExhausted, _TurnCancelled):
            raise
        except Exception:
            _logger.exception(
                "orchestration stage=semantic_tool_invoke "
                "decision=error capability=%s correlation_id=%s",
                cap_id,
                correlation,
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
                correlation_id=correlation,
                error_code="semantic_tool_invoke_failed",
            )
        if invoked is None:
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id=correlation,
                error_code="owner_no_resolvable_candidate",
            )
        outcome, action_id, remote_used = invoked
        binding = GovernedCapabilityBinding(
            binding_id=f"{correlation}:{group.group_id}:{remote_used}",
            group_key=group_key,
            remote_capability=remote_used,
            action_id=str(action_id or remote_used),
            source=SourceRef(
                source_id=group.group_id,
                source_system=group.provider_id,
                provider_name=group.provider_id,
            ),
            provider_id=group.provider_id,
            capability_group_id=group.group_id,
        )

        def _render(out: SpecialistOutcome) -> RenderedSpecialistOutcome:
            return render_specialist_outcome_rich(
                out,
                input_text=input_text,
                invocation_arguments=args,
                field_labels=self._field_labels,
            )

        attempt = _success_attempt(
            correlation_id=correlation,
            binding=binding,
            outcome=outcome,
            render=_render,
        )
        # Tag pure discovery envelopes so finalize never treats catalog
        # / candidate lists as business facts (R2). When discovery-first
        # already chained to an owner READ (remote_used != discover
        # remote), the attempt IS business evidence — do not mask it.
        if descriptor.operation_class is SpecialistOperationClass.DISCOVERY:
            chained_owner_read = (
                str(remote_used or "").strip()
                and str(remote_used).strip() != str(descriptor.remote_name).strip()
            )
            if not chained_owner_read:
                limitations = tuple(attempt.limitations) + (
                    "discovery_metadata_observation",
                )
                return GovernedCapabilityAttempt(
                    status=attempt.status,
                    correlation_id=attempt.correlation_id,
                    content=attempt.content,
                    limitations=limitations,
                    error_code=attempt.error_code,
                    provenance=attempt.provenance,
                    outcome=attempt.outcome,
                    markdown_content=attempt.markdown_content,
                    admission_outcome=attempt.admission_outcome,
                    verified_composition=attempt.verified_composition,
                )
            _logger.info(
                "orchestration stage=semantic_tool_invoke "
                "decision=discovery_chained_read "
                "discover=%s read=%s action=%s correlation_id=%s",
                descriptor.remote_name,
                remote_used,
                action_id,
                correlation,
            )
        return attempt

    def _accept_semantic_investigation_plan(
        self,
        *,
        goal_class: str,
        comparison_requested: bool,
        target_identities: object,
        evidence_needed: object = (),
        business_subject: str | None = None,
        correlation: str,
    ) -> SemanticInvestigationPlan | None:
        """Validate Agent-declared investigation plan into typed contract.

        Reuses ``_TurnGoal`` vocabulary — no parallel goal model.
        """
        klass = (goal_class or "").strip()
        if klass not in self._GOAL_CLASSES:
            _logger.info(
                "orchestration stage=semantic_plan "
                "decision=invalid_class correlation_id=%s",
                correlation,
            )
            return None
        if klass == "compare":
            comparison_requested = True
        subject = (
            str(business_subject).strip()[:240] if business_subject else None
        ) or None
        goal = self._TurnGoal(
            goal_class=klass,
            comparison_requested=bool(comparison_requested),
            business_subject=subject,
            declared=True,
        )
        targets = _normalize_identity_tuple(target_identities)
        needed = _normalize_identity_tuple(evidence_needed) or targets
        return SemanticInvestigationPlan(
            goal=goal,
            target_identities=targets,
            evidence_needed=needed,
        )

    def _compose_observation_pair(
        self,
        *,
        left: GovernedCapabilityAttempt,
        right: GovernedCapabilityAttempt,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt | None:
        """Optional deterministic composition of two verified observations.

        Agent-requested analysis capability — not an intent router.
        Both sides must be business evidence with authoritative roots.
        """
        if not (
            _is_business_evidence_attempt(left)
            and _is_business_evidence_attempt(right)
        ):
            return None
        left_root = _authoritative_structure_root(left)
        right_root = _authoritative_structure_root(right)
        if (
            left_root is None
            or right_root is None
            or left_root.casefold() == right_root.casefold()
        ):
            return None
        left_records = _comparison_records(left.outcome)  # type: ignore[arg-type]
        right_records = _comparison_records(right.outcome)  # type: ignore[arg-type]
        composed = self._compose_multi_evidence(
            {left_root: left_records, right_root: right_records},
            "",
            correlation=correlation,
            workspace_context=workspace_context,
            deadline=deadline,
        )
        if composed is None:
            return None
        content, limitations, verdict = composed
        if verdict not in ("agreement", "differences_found"):
            return None
        verified = VerifiedCompositeEvidence(
            source_roots=(left_root, right_root),
            source_lineage=(
                left.provenance.source_refs,  # type: ignore[union-attr]
                right.provenance.source_refs,  # type: ignore[union-attr]
            ),
            observed_at=max(
                left.outcome.provenance.observed_at,  # type: ignore[union-attr]
                right.outcome.provenance.observed_at,  # type: ignore[union-attr]
            ),
            correlation_id=correlation,
            verdict=verdict,
        )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id=correlation,
            content=content,
            limitations=tuple(limitations)[:24],
            verified_composition=verified,
        )

    def _finalize_semantic_investigation(
        self,
        *,
        input_text: str,
        collected: tuple[GovernedCapabilityAttempt, ...],
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
        unbound_outcome: str | None,
        plan: SemanticInvestigationPlan | None = None,
        clarification_question: str | None = None,
        composed_attempt: GovernedCapabilityAttempt | None = None,
    ) -> GovernedCapabilityAttempt:
        """Conclude from typed coverage + authoritative evidence."""
        return _finalize_agent_collected_attempts(
            self,
            input_text=input_text,
            collected=collected,
            correlation=correlation,
            workspace_context=workspace_context,
            deadline=deadline,
            unbound_outcome=unbound_outcome,
            plan=plan,
            clarification_question=clarification_question,
            composed_attempt=composed_attempt,
        )









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
        workspace_context: WorkspaceContext | None = None,
    ) -> tuple[SpecialistOutcome, str, str] | None:
        """Invoke honoring the owner's flow shape — deterministic only.

        No second semantic controller lives here: the Agent already
        selected the capability and produced the arguments. Application
        validates, binds candidates deterministically and invokes the
        owner. Returns (outcome, action_id, remote_name_used), or None
        when the owner produced no resolvable candidate (truthful
        NOT_APPLICABLE — the agent may then call the owner discovery
        tool itself and retry with an explicit candidate_token).
        """
        capabilities = {
            cap.remote_name: cap for cap in group.capabilities
        }
        selected = capabilities[remote_name]

        if _is_candidate_bound(selected):
            token = arguments.get(CANDIDATE_TOKEN_FIELD)
            if isinstance(token, str) and token.strip():
                # Agent-supplied owner-issued candidate handle: opaque
                # untrusted data passed back to the owner verbatim —
                # never synthesized here, never an authorization.
                inner = arguments.get("arguments")
                merged = (
                    validate_untyped_arguments(inner)
                    if isinstance(inner, Mapping)
                    else ({} if inner is None else None)
                )
                if merged is None:
                    return None
                outcome = self._invoke(
                    group,
                    remote_name,
                    {
                        CANDIDATE_TOKEN_FIELD: token.strip(),
                        "arguments": merged,
                    },
                    correlation,
                    deadline,
                )
                return outcome, remote_name, remote_name
            found = self._discover_candidate(
                group,
                input_text,
                correlation,
                deadline,
                prior_turns,
            )
            if found is None:
                return None
            candidate, _discovery_outcome = found
            if candidate is None:
                return None
            inner = arguments.get("arguments")
            merged = self._candidate_arguments(
                candidate,
                inner if isinstance(inner, Mapping) else {},
                input_text,
                correlation=correlation,
            )
            if merged is None:
                return None
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
            # Owner discovery may return exactly one executable
            # candidate for a candidate-bound READ on the same
            # specialist — chain deterministically. Multiple usable
            # candidates are returned to the agent, never picked by a
            # second model stage; the agent selects via a follow-up
            # tool call carrying the chosen candidate_token.
            candidate = self._resolve_candidate(
                outcome.structured,
                input_text,
                prior_turns,
                workspace_context=workspace_context,
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
                        workspace_context=workspace_context,
                    )
                    if candidate is None and not (
                        self._candidates_present(retry.structured)
                    ):
                        outcome = retry
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
                    correlation=correlation,
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
            if self._candidates_present(outcome.structured):
                # Candidates visible to the agent through the bounded
                # tool projection — selection is the agent's next tool
                # call with the owner-issued token.
                return outcome, remote_name, remote_name
            # S2 (RQ-SA04 / D5): the DISCOVERY payload may itself
            # publish the answer — owner-authored catalog/guidance
            # sections projected deterministically; the search miss is
            # declared only when nothing projectable remains.
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
        the context-folded query. Returns the resolved candidate (or
        None) plus the discovery envelope outcome."""
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
            ),
            retry,
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
        workspace_context: "WorkspaceContext | None" = None,
    ) -> Mapping[str, Any] | None:
        """Resolve the owner candidate to chain — deterministic only.

        Exactly one live-token, non-dead-end candidate chains. Zero or
        ambiguous sets resolve to ``None`` — the candidates stay
        visible to the Agent through the discovery projection and the
        semantic pick happens as a native tool call carrying the
        owner-issued candidate_token, never as a second LLM selector.
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
        if not matching:
            return None
        literals = _resolvable_identifier_literals(
            workspace_context, prior_turns
        )
        usable = [
            c
            for c in matching
            if not _candidate_needs_missing_identifier(
                c, input_text, literals
            )
        ]
        if len(usable) == 1:
            return usable[0]
        return None

    def _candidate_arguments(
        self,
        candidate: Mapping[str, Any],
        proposed: Mapping[str, Any],
        input_text: str,
        correlation: str = "",
    ) -> dict[str, Any] | None:
        """Resolve inner args against the candidate's own schema.

        Deterministic validation only — the Agent already produced
        the arguments. When the proposal does not satisfy the owner
        schema, a single bounded utterance-identifier binding is the
        last deterministic resort; otherwise the call fails closed and
        the agent decides the retry.
        """
        schema = candidate.get("argument_schema")
        effective_schema: Mapping[str, Any] | None = None
        if isinstance(schema, Mapping):
            effective_schema = dict(schema)
        required_args = candidate.get("required_arguments")
        if isinstance(required_args, (list, tuple)) and required_args:
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
        fallback = _bind_identifier_args_from_utterance(
            effective_schema, input_text
        )
        if fallback is None:
            return None
        fallback_validated = (
            _validate_instance(fallback, effective_schema)
            if effective_schema is not None
            else fallback
        )
        if fallback_validated is None:
            return None
        _logger.info(
            "orchestration stage=candidate_arguments "
            "decision=utterance_identifier_bind keys=%s "
            "correlation_id=%s",
            ",".join(sorted(fallback_validated)),
            correlation,
        )
        return dict(fallback_validated)


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
