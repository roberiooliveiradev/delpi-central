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
from decimal import Decimal, InvalidOperation
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
    TurnKind,
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
    InvestigationAnswer,
    InvestigationAnswerStatus,
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












# Goal stage proposals include typed sufficiency requirements — a
# hypothesis the runtime verifies against typed evidence at the
# outcome edge. Baseline instructions stay byte-identical.


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






_TEMPORAL_ARG_KEY_RE = re.compile(
    r"date|time|_from|^from|_to$|^to$|since|until|period|competencia"
    r"|year|month|day",
    re.IGNORECASE,
)






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


# Owner-operation vocabulary a declared obligation may require
# (SpecialistOperationClass values, casefolded — UNKNOWN excluded:
# an untyped capability never demonstrates a typed requirement).
_OBLIGATION_OPERATIONS = frozenset(
    {
        SpecialistOperationClass.DISCOVERY.value.casefold(),
        SpecialistOperationClass.READ.value.casefold(),
        SpecialistOperationClass.ANALYSIS.value.casefold(),
        SpecialistOperationClass.PREPARE.value.casefold(),
        SpecialistOperationClass.ACT.value.casefold(),
    }
)


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class MaterialObligation:
    """One typed material evidence obligation (RC5 anchors contract).

    ``description`` is the model-declared business obligation.
    ``evidence_source`` optionally anchors the obligation to the live
    owner vocabulary — an entity/action/capability token the owner
    echoes in structured results or that names a governed invocation
    selector. ``operation`` optionally requires a specific
    ``SpecialistOperationClass``. Both are verifiable proposals — the
    deterministic layer checks them against owner-echoed metadata and
    governed invocation records; they never grant authorization and
    are never a domain catalog.
    """

    description: str
    evidence_source: str | None = None
    operation: str | None = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MaterialObligation):
            return (
                self.description,
                self.evidence_source,
                self.operation,
            ) == (
                other.description,
                other.evidence_source,
                other.operation,
            )
        if isinstance(other, str):
            return (
                self.evidence_source is None
                and self.operation is None
                and self.description == other
            )
        return NotImplemented

    def __hash__(self) -> int:
        return hash(
            (self.description, self.evidence_source, self.operation)
        )

    def to_projection(self) -> dict:
        """Bounded observability projection of the declared anchors."""
        projected: dict[str, str] = {"description": self.description}
        if self.evidence_source is not None:
            projected["evidence_source"] = self.evidence_source
        if self.operation is not None:
            projected["operation"] = self.operation
        return projected


@dataclasses.dataclass(frozen=True, slots=True)
class SemanticInvestigationPlan:
    """Application-validated investigation plan from the Agent tool.

    Semantic proposal only — never authorization. Target identities and
    evidence_needed are the REF05/material-obligation contract for
    finalize; comparison_requested comes from the typed ``_TurnGoal``.
    ``evidence_needed`` items are ``MaterialObligation`` — a plain
    description (legacy string input) carries no verified anchor and
    can bind evidence but never demonstrate it.
    """

    goal: "OperationalCapabilityOrchestrator._TurnGoal"
    target_identities: tuple[str, ...] = ()
    evidence_needed: tuple[MaterialObligation, ...] = ()


def _structured_owner_incomplete(outcome: SpecialistOutcome | None) -> bool:
    """True when owner structured payload declares business incompleteness.

    Distinct from transport ``outcome.is_complete``: MCP adapters may
    mark the wire result complete while ``data.is_complete=false``
    (partial tree / truncated page). That owner flag must remain visible.
    """
    if outcome is None:
        return False
    structured = outcome.structured
    if not isinstance(structured, Mapping):
        return False
    if structured.get("is_complete") is False:
        return True
    data = structured.get("data")
    if isinstance(data, Mapping) and data.get("is_complete") is False:
        return True
    return False


def _owner_declares_guidance_only(
    structured: Mapping[str, Any] | None,
) -> bool:
    """True when the owner labels the payload as guidance, not domain truth.

    Reads the published ``authority`` / ``knowledge_kind`` fields only —
    never specialist names or user wording. GUIDANCE is not citable
    operational evidence for structure/inventory/registry objectives.
    """
    if not isinstance(structured, Mapping):
        return False
    nodes: list[Mapping[str, Any]] = [structured]
    data = structured.get("data")
    if isinstance(data, Mapping):
        nodes.append(data)
    for node in nodes:
        authority = node.get("authority")
        if isinstance(authority, str) and authority.strip() == (
            "GUIDANCE_NOT_DOMAIN_TRUTH"
        ):
            return True
        knowledge_kind = node.get("knowledge_kind")
        if (
            isinstance(knowledge_kind, str)
            and knowledge_kind.strip().upper() == "GUIDANCE"
        ):
            return True
    return False


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
    structured = outcome.structured if outcome is not None else None
    if _owner_declares_guidance_only(
        structured if isinstance(structured, Mapping) else None
    ):
        return False
    return True


# Investigation-side progress classes (INT-1). Signals for the Agent
# and finalize limitations — never a second Outcome authority.
INVESTIGATION_PROGRESS_NEW = "NEW_INFORMATION"
INVESTIGATION_PROGRESS_NONE = "NO_PROGRESS"
INVESTIGATION_PROGRESS_RELATED = "RELATED_INSUFFICIENT"
INVESTIGATION_PROGRESS_DISCOVERY = "DISCOVERY_ONLY"


def classify_investigation_progress(
    attempt: GovernedCapabilityAttempt,
    *,
    prior_content_fingerprints: frozenset[str] | set[str] = frozenset(),
    uncovered_after: Sequence[str] = (),
    plan: "SemanticInvestigationPlan | None" = None,
    operation_class: str | None = None,
) -> str:
    """Classify one observation's contribution to the user objective.

    Deterministic, contract-driven, owner-/tool-name agnostic. Discovery
    catalogs are never business progress. A SUCCESS that fails every
    declared material obligation, or that leaves named identifiers
    uncovered without an authoritative root, is related-but-insufficient.

    ``operation_class`` is accepted for projection compatibility but
    never decides sufficiency — the same ANALYSIS or READ capability
    may be adequate or inadequate depending on obligations and the
    observed evidence structure (INT-1 F2).
    """
    del operation_class  # never authority for relevance
    if "discovery_metadata_observation" in attempt.limitations:
        return INVESTIGATION_PROGRESS_DISCOVERY
    if attempt.status is not GovernedCapabilityStatus.SUCCESS:
        return INVESTIGATION_PROGRESS_NONE
    if not _is_business_evidence_attempt(attempt):
        return INVESTIGATION_PROGRESS_NONE
    body = (attempt.content or "").strip()
    content_fp = hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]
    if content_fp in prior_content_fingerprints:
        return INVESTIGATION_PROGRESS_NONE
    obligations = (
        plan.evidence_needed
        if plan is not None and plan.evidence_needed
        else ()
    )
    if obligations:
        if not any(
            _attempt_satisfies_obligation(attempt, obligation)
            for obligation in obligations
        ):
            return INVESTIGATION_PROGRESS_RELATED
    # Named identifiers remain open and this observation produced no
    # authoritative root — related text/docs without identity coverage.
    if uncovered_after and _authoritative_structure_root(attempt) is None:
        return INVESTIGATION_PROGRESS_RELATED
    # Without declared obligations, a new business observation is
    # progress information only — never a proven objective verdict
    # (finalize / INT-3 own sufficiency).
    return INVESTIGATION_PROGRESS_NEW


def observation_content_fingerprint(
    attempt: GovernedCapabilityAttempt,
) -> str | None:
    """Stable fingerprint of observation body for no-progress detection."""
    body = (attempt.content or "").strip()
    if not body:
        return None
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]


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


def _owner_scalar_field_values(
    value: Any,
    *,
    _depth: int = 0,
    _budget: tuple[int, ...] = (256,),
) -> set[str]:
    """Scalar values inside an owner structured payload.

    Bounded recursive walk — owner business records only. Strings are
    collected verbatim; ints become their decimal form (business codes
    such as ``code=90260147`` may serialize as JSON numbers). Rendered
    content text is never consulted — callers filter to identifier
    literals so a prose mention cannot close coverage.
    """
    if _depth > 8 or _budget[0] <= 0:
        return set()
    _budget = (_budget[0] - 1,)
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, bool):
        return set()
    if isinstance(value, int):
        return {str(value)}
    if isinstance(value, Mapping):
        found: set[str] = set()
        for item in list(value.values())[:64]:
            found |= _owner_scalar_field_values(
                item, _depth=_depth + 1, _budget=_budget
            )
            if _budget[0] <= 0:
                break
        return found
    if isinstance(value, (list, tuple)):
        found = set()
        for item in list(value)[:64]:
            found |= _owner_scalar_field_values(
                item, _depth=_depth + 1, _budget=_budget
            )
            if _budget[0] <= 0:
                break
        return found
    return set()


def _attempt_identifier_roots(
    attempt: GovernedCapabilityAttempt,
) -> frozenset[str]:
    """Authoritative identifier values attested by one business attempt.

    Union of the structure root (DAVI-style ``data.root.code`` /
    flattened min-depth record code) and scalar field values the owner
    returned that ARE identifier literals — ``codigo_processo=
    PROC-0034`` closes coverage for ``PROC-0034``; a prose field merely
    mentioning the code does not (fullmatch, never substring).
    Capability names and rendered text are never consulted.
    """
    values = _owner_scalar_field_values(
        attempt.outcome.structured
        if attempt.outcome is not None
        else None
    )
    roots = {
        item
        for item in values
        if _IDENTIFIER_LITERAL_RE.fullmatch(item)
    }
    root = _authoritative_structure_root(attempt)
    if isinstance(root, str) and root.strip():
        roots.add(root.strip())
    return frozenset(roots)


def _identifier_arg_keys(
    properties: Mapping[str, Any],
    names: list[str] | None,
) -> list[str]:
    """Identifier-shaped string fields among ``names`` (or all keys)."""
    keys: list[str] = []
    for key, node in properties.items():
        if names is not None and str(key) not in names:
            continue
        if not _IDENTIFIER_ARG_KEY_RE.search(str(key)):
            continue
        if not isinstance(node, Mapping):
            continue
        if node.get("type") not in (None, "string"):
            continue
        keys.append(str(key))
    return keys


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
    literals = _IDENTIFIER_LITERAL_RE.findall(input_text or "")
    unique = list(dict.fromkeys(str(item) for item in literals if item))
    if not unique:
        return None
    id_keys = _identifier_arg_keys(properties, required_names)
    if not id_keys:
        # Optional identifier fields (native MCP envelope path): the
        # owner's schema may declare ``code`` without marking it
        # required — the utterance literal still determines the value.
        id_keys = _identifier_arg_keys(properties, None)
        if len(id_keys) != 1:
            exact = [
                k
                for k in id_keys
                if re.fullmatch(r"(?i)code|id", str(k))
            ]
            id_keys = exact if len(exact) == 1 else []
    if len(id_keys) != 1:
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


def _obligation_item(obligation: object) -> MaterialObligation:
    """Coerce one declared obligation into ``MaterialObligation``.

    Accepts the contract forms: ``MaterialObligation``, a plain string
    (legacy — description only, no verified anchor) or a mapping
    (``description`` plus optional ``evidence_source``/``operation``).
    Unknown shapes collapse to an empty description — never satisfied.
    """
    if isinstance(obligation, MaterialObligation):
        return obligation
    if isinstance(obligation, str):
        return MaterialObligation(description=obligation.strip())
    if isinstance(obligation, Mapping):
        description = str(obligation.get("description") or "").strip()
        source = obligation.get("evidence_source")
        operation = obligation.get("operation")
        return MaterialObligation(
            description=description,
            evidence_source=(
                source.strip()
                if isinstance(source, str) and source.strip()
                else None
            ),
            operation=(
                operation.strip().casefold()
                if isinstance(operation, str) and operation.strip()
                else None
            ),
        )
    return MaterialObligation(description="")


def _normalize_obligation_tuple(
    raw: object,
) -> tuple[MaterialObligation, ...] | None:
    """Normalize declared evidence obligations; None on invalid vocab.

    Each item may be a plain string (legacy subject/identity scope) or
    a mapping ``{description, evidence_source?, operation?}`` — the
    typed RC5 anchor form. An ``operation`` outside the owner
    operation vocabulary rejects the whole plan so the model receives
    bounded vocabulary feedback instead of a silently dropped field.
    """
    if not isinstance(raw, (list, tuple)):
        return ()
    normalized: list[MaterialObligation] = []
    for item in raw:
        obligation = _obligation_item(item)
        if not obligation.description or len(obligation.description) > 200:
            continue
        if (
            obligation.operation is not None
            and obligation.operation not in _OBLIGATION_OPERATIONS
        ):
            return None
        if (
            obligation.evidence_source is not None
            and "." in obligation.evidence_source
        ):
            # A dotted identifier is the governed transport surface
            # (``{specialist}.{remote}``), never an owner evidence
            # kind — reject the plan so the model receives bounded
            # feedback and can re-declare the owner vocabulary token
            # in the same turn (RC5-R1). Surface-level anchors can
            # bind but never demonstrate, so keeping them silently
            # would lock the obligation into INCONCLUSIVE.
            return None
        normalized.append(obligation)
    seen: set[tuple[str, str | None, str | None]] = set()
    unique: list[MaterialObligation] = []
    for obligation in normalized[:16]:
        key = (
            obligation.description.casefold(),
            (
                obligation.evidence_source.casefold()
                if obligation.evidence_source
                else None
            ),
            obligation.operation,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(obligation)
    return tuple(unique)


def _obligation_descriptions(
    obligations: "tuple[MaterialObligation | str, ...]",
) -> tuple[str, ...]:
    return tuple(
        _obligation_item(item).description
        for item in obligations
        if _obligation_item(item).description
    )


def _obligation_identity_keys(needle: str) -> set[str]:
    """Strict identity literals declared inside an obligation text."""
    keys: set[str] = set()
    for item in _IDENTIFIER_LITERAL_RE.findall(needle):
        item = item.strip()
        if not item:
            continue
        keys.add(item.casefold())
        # A prefixed literal embeds the authoritative numeric code the
        # owner actually records ("product_90260921" → "90260921";
        # "PROC-0105" → "0105") — same identity, distinct formatting.
        core = re.search(r"\d{3,}", item)
        if core and core.group(0) != item:
            keys.add(core.group(0).casefold())
    return keys


def _attempt_matches_identity_keys(
    attempt: GovernedCapabilityAttempt, keys: set[str]
) -> bool:
    """Strict identity matching against owner-authoritative evidence."""
    if not _is_business_evidence_attempt(attempt):
        return False
    root = _authoritative_structure_root(attempt)
    if root is not None and root.casefold() in keys:
        return True
    outcome = attempt.outcome
    if outcome is None or not outcome.is_complete:
        return False
    if root is None:
        # Identifier-shaped scalars the owner attested in the
        # structured payload (field-name agnostic — e.g. TÉO
        # ``codigo_processo``) close the identity. A resolved root
        # outside the keys keeps wrong-root protection active (REF05).
        if keys & {
            item.casefold()
            for item in _attempt_identifier_roots(attempt)
        }:
            return True
    records = _comparison_records(outcome)
    if not records:
        return False
    rows = _flatten_evidence_records(records)
    for row in rows:
        code = row.get("code")
        if not isinstance(code, str) or not code.strip():
            continue
        if code.strip().casefold() not in keys:
            continue
        # Wrong-root child mention is not the requested identity.
        if root is not None and root.casefold() not in keys:
            continue
        return True
    return False


# Owner-echoed metadata keys that carry the evidence anchor vocabulary.
_ANCHOR_ECHO_KEYS = frozenset(
    {
        "entity",
        "entity_kind",
        "action_id",
        "capability",
        "action",
        "view",
        "kind",
        "shape",
        "subject",
    }
)

# Top-level invocation argument keys that carry owner vocabulary
# selectors (envelope vocabulary — never user data values like codes
# or params payloads). Recorded as governed invocation context so
# obligation anchors remain verifiable for owners whose structured
# results do not echo entity/action metadata (RC5 namespace).
_INVOCATION_VOCABULARY_KEYS = frozenset(
    {
        "entity",
        "entity_kind",
        "action",
        "action_id",
        "capability",
        "view",
        "kind",
        "operation",
        "subject",
    }
)


def _invocation_vocabulary(args: object) -> tuple[str, ...]:
    """Bounded owner-vocabulary selector tokens of one invocation.

    Only top-level arguments whose key names owner-vocabulary
    selectors are captured — exact token values, never nested payload
    content. Naming a selector grants nothing; it records which owner
    kind of evidence was invoked.
    """
    if not isinstance(args, Mapping):
        return ()
    tokens: list[str] = []
    for key in _INVOCATION_VOCABULARY_KEYS:
        value = args.get(key)
        if not isinstance(value, str):
            continue
        token = value.strip()
        if not token or len(token) > 64:
            continue
        if token.casefold() in {item.casefold() for item in tokens}:
            continue
        tokens.append(token)
    return tuple(tokens[:8])


def _invocation_identity(args: object) -> tuple[str, ...]:
    """Bounded identifier literals the invocation queried.

    Only top-level arguments whose key names an identifier slot
    (``_IDENTIFIER_ARG_KEY_RE``) and whose value is itself an
    identifier literal (``_IDENTIFIER_LITERAL_RE`` fullmatch) are
    captured — the governed record of WHICH identity the owner was
    asked about. Never nested payload, never free text, never
    authorization.
    """
    if not isinstance(args, Mapping):
        return ()
    # Scan top-level selector slots and, when an envelope nests the
    # owner payload under a single Mapping argument (e.g. ``arguments``
    # in ``{capability, arguments}``), one level inside it. Never
    # deeper — payload trees are not selector surface.
    scopes: list[Mapping] = [args]
    for value in args.values():
        if isinstance(value, Mapping):
            scopes.append(value)
    tokens: list[str] = []
    for scope in scopes:
        for key, value in scope.items():
            if not _IDENTIFIER_ARG_KEY_RE.search(str(key)):
                continue
            if not isinstance(value, str):
                continue
            token = value.strip()
            if not token or len(token) > 64:
                continue
            if not _IDENTIFIER_LITERAL_RE.fullmatch(token):
                continue
            if token.casefold() in {item.casefold() for item in tokens}:
                continue
            tokens.append(token)
    return tuple(tokens[:8])


# Owner structured keys whose emptiness/zeroness attests absence.
_ABSENCE_COLLECTION_KEYS = frozenset(
    {"items", "results", "rows", "records", "entries", "children"}
)
_ABSENCE_TOTAL_KEYS = frozenset({"total", "total_count", "count"})


def _attempt_anchor_tokens(
    attempt: GovernedCapabilityAttempt,
) -> frozenset[str]:
    """Owner-declared anchor vocabulary bound to one attempt.

    Candidates are exact casefolded tokens: owner echoes in the
    structured result (``entity``/``action_id``/``capability``/``shape``
    family) and the bounded owner-vocabulary selectors recorded as
    governed invocation context (e.g. envelope ``entity``/``action``
    arguments). The proxy envelope names (``remote_capability`` /
    ``action_id`` of the DÉLIA tool surface) are NOT owner evidence
    vocabulary — they name the transport surface, not the business
    kind. Never substring matching over free text, never
    model-declared text.
    """
    tokens: set[str] = set()
    provenance = attempt.provenance
    if provenance is not None:
        for token in provenance.invocation_vocabulary or ():
            if isinstance(token, str) and token.strip():
                tokens.add(token.strip().casefold())
    outcome = attempt.outcome
    structured = outcome.structured if outcome is not None else None
    if isinstance(structured, Mapping):
        for key in _ANCHOR_ECHO_KEYS:
            value = structured.get(key)
            if isinstance(value, str) and value.strip():
                tokens.add(value.strip().casefold())
        action = structured.get("action")
        if isinstance(action, Mapping):
            for key in ("id", "action_id", "entity", "name"):
                value = action.get(key)
                if isinstance(value, str) and value.strip():
                    tokens.add(value.strip().casefold())
    return frozenset(tokens)


def _attempt_surface_anchor_match(
    attempt: GovernedCapabilityAttempt, source: str
) -> bool:
    """Declared anchor equals the invoked governed-surface identity.

    ``remote_capability``/``action_id`` and the composite
    ``specialist_id.remote_capability`` are DÉLIA-side provenance
    (which envelope was invoked), never owner evidence kind — a match
    binds the attempt to the obligation but cannot demonstrate it.
    """
    provenance = attempt.provenance
    if provenance is None:
        return False
    candidates = [
        provenance.remote_capability,
        provenance.action_id,
        f"{provenance.specialist_id}.{provenance.remote_capability}",
    ]
    for token in candidates:
        if (
            isinstance(token, str)
            and token.strip()
            and token.strip().casefold() == source
        ):
            return True
    return False


def _attempt_operation_class(
    attempt: GovernedCapabilityAttempt,
) -> str | None:
    """Owner-typed operation class recorded at the governed boundary."""
    provenance = attempt.provenance
    if provenance is None:
        return None
    value = getattr(provenance, "operation_class", None)
    if isinstance(value, str) and value.strip():
        return value.strip().casefold()
    return None


def _attempt_invocation_identity_keys(
    attempt: GovernedCapabilityAttempt,
) -> frozenset[str]:
    """Casefolded identity literals the attempt's invocation queried.

    Mirrors ``_obligation_identity_keys`` normalization — a prefixed
    literal's numeric core is added so the same identity in different
    formatting still binds (``PROC-0034`` ↔ ``0034``).
    """
    provenance = attempt.provenance
    if provenance is None:
        return frozenset()
    keys: set[str] = set()
    for token in provenance.invocation_identity or ():
        if not isinstance(token, str) or not token.strip():
            continue
        token = token.strip().casefold()
        keys.add(token)
        core = re.search(r"\d{3,}", token)
        if core and core.group(0) != token:
            keys.add(core.group(0))
    return frozenset(keys)


def _attempt_declares_authoritative_absence(
    attempt: GovernedCapabilityAttempt,
) -> bool:
    """Complete owner response declaring absence inside its scope.

    Authoritative absence requires: SUCCESS, complete provenance, a
    complete outcome, no truncation/incompleteness flags, and either
    an owner structured payload whose collections are empty (with no
    contradicting positive totals), or the canonical empty-result
    rendering. A partial or truncated empty page demonstrates nothing.
    """
    if attempt.status is not GovernedCapabilityStatus.SUCCESS:
        return False
    if attempt.provenance is None or not attempt.provenance.is_complete:
        return False
    outcome = attempt.outcome
    if outcome is None or not outcome.is_complete:
        return False
    structured = outcome.structured
    if isinstance(structured, Mapping):
        inner = structured.get("data")
        data = inner if isinstance(inner, Mapping) else structured
        for envelope in (structured, data):
            if envelope.get("is_complete") is False:
                return False
            if envelope.get("truncated") is True:
                return False
        collections = [
            data[key]
            for key in _ABSENCE_COLLECTION_KEYS
            if isinstance(data.get(key), (list, tuple))
        ]
        totals = [
            data[key]
            for key in _ABSENCE_TOTAL_KEYS
            if isinstance(data.get(key), (int, float))
            and not isinstance(data.get(key), bool)
        ]
        if collections and all(len(entry) == 0 for entry in collections):
            return not totals or all(value == 0 for value in totals)
        if totals and all(value == 0 for value in totals):
            return True
        return False
    content = (attempt.content or "").strip()
    return content == EMPTY_RESULT_TEXT or content.startswith(
        f"{EMPTY_RESULT_TEXT}\n"
    )


def _attempt_postcondition_demonstrated(
    attempt: GovernedCapabilityAttempt,
) -> bool:
    """Owner-attested write postcondition via the canonical verifier.

    Reuses ``project_write_outcome`` — the governed-write boundary
    already defines the authoritative postcondition contract: only an
    explicit owner ``verified`` echo projects VERIFIED; technical
    success (``success: true``) is EXECUTION_REPORTED, never a
    demonstrated business outcome (RC5-R4). No parallel verifier.
    """
    if attempt.status is not GovernedCapabilityStatus.SUCCESS:
        return False
    if attempt.provenance is None or not attempt.provenance.is_complete:
        return False
    outcome = attempt.outcome
    if outcome is None or not outcome.is_complete:
        return False
    structured = outcome.structured
    if not isinstance(structured, Mapping):
        return False
    projection = project_write_outcome(
        capability_ref=(
            f"{attempt.provenance.specialist_id}."
            f"{attempt.provenance.remote_capability}"
        ),
        remote_capability=attempt.provenance.remote_capability,
        owner_payload=structured,
        specialist_id=attempt.provenance.specialist_id,
        correlation_id=attempt.correlation_id,
        occurred_at=attempt.provenance.observed_at,
        limitations=attempt.limitations,
    )
    return projection.status is WriteOutcomeStatus.VERIFIED


def _plan_delivery_mode(plan) -> str | None:
    """Typed plan delivery kind — ``None`` for legacy/fake plans
    without the goal envelope (backward-compatible extension)."""
    if plan is None:
        return None
    return getattr(getattr(plan, "goal", None), "output_mode", None)


def _attempt_collection_partially_retrieved(
    attempt: GovernedCapabilityAttempt,
) -> bool:
    """Owner declares the bound collection window is incomplete.

    Three owner-declared signals only — never inferred from record
    content: ``is_complete`` is false, ``truncated`` is true, or a
    declared numeric total exceeds the delivered collection size
    (e.g. ``total: 109`` with 20 items — page 1 of 6). A collection
    without completeness markers proves neither completeness nor
    incompleteness.
    """
    outcome = attempt.outcome
    if outcome is None:
        return False
    structured = outcome.structured
    if not isinstance(structured, Mapping):
        return False
    inner = structured.get("data")
    nodes = [
        node
        for node in (structured, inner)
        if isinstance(node, Mapping)
    ]
    for node in nodes:
        if node.get("is_complete") is False:
            return True
        if node.get("truncated") is True:
            return True
    data = inner if isinstance(inner, Mapping) else structured
    totals = [
        data[key]
        for key in _ABSENCE_TOTAL_KEYS
        if isinstance(data.get(key), (int, float))
        and not isinstance(data.get(key), bool)
    ]
    collections = [
        data[key]
        for key in _ABSENCE_COLLECTION_KEYS
        if isinstance(data.get(key), (list, tuple))
    ]
    if totals and collections:
        delivered = max(len(entry) for entry in collections)
        if any(total > delivered for total in totals):
            return True
    return False


def _attempt_collection_proven_complete(
    attempt: GovernedCapabilityAttempt,
) -> bool:
    """Positive proof the bound collection covers its declared scope.

    UNKNOWN_COMPLETENESS != PROVEN_COMPLETE: a collection is
    demonstrably complete only when the owner declares it — a
    numeric ``total``/``total_count``/``count`` at or below the
    delivered size, or an explicit ``is_complete`` marker with no
    truncation flag. The absence of incompleteness indicators is not
    evidence of completeness: an unmarked collection stays
    unverifiable (INCONCLUSIVE), and non-collection evidence cannot
    demonstrate an enumeration at all.
    """
    outcome = attempt.outcome
    if outcome is None:
        return False
    structured = outcome.structured
    if not isinstance(structured, Mapping):
        return False
    inner = structured.get("data")
    nodes = [
        node
        for node in (structured, inner)
        if isinstance(node, Mapping)
    ]
    data = inner if isinstance(inner, Mapping) else structured
    collections = [
        data[key]
        for key in _ABSENCE_COLLECTION_KEYS
        if isinstance(data.get(key), (list, tuple))
    ]
    if not collections:
        return False
    for node in nodes:
        if node.get("is_complete") is False:
            return False
        if node.get("truncated") is True:
            return False
    delivered = max(len(entry) for entry in collections)
    totals = [
        data[key]
        for key in _ABSENCE_TOTAL_KEYS
        if isinstance(data.get(key), (int, float))
        and not isinstance(data.get(key), bool)
    ]
    if totals:
        return delivered >= max(totals)
    return any(node.get("is_complete") is True for node in nodes)


def _attempt_declares_aggregate_metric(
    attempt: GovernedCapabilityAttempt,
) -> bool:
    """Owner-declared aggregate deliverable for ``aggregation``.

    SATISFIED-by-metric requires an authoritative numeric aggregate
    field (``total``/``total_count``/``count``) in a non-truncated,
    non-incomplete payload — a partial items window does not
    invalidate the owner-declared count. A provably complete
    collection also yields a mechanically derivable count. An
    unverifiable or partial window cannot be turned into a total.
    """
    if _attempt_collection_partially_retrieved(attempt):
        # The owner itself flagged incompleteness: only an explicit
        # aggregate field remains authoritative (it is delivered
        # independently of the item window).
        outcome = attempt.outcome
        structured = outcome.structured if outcome else None
        if not isinstance(structured, Mapping):
            return False
        inner = structured.get("data")
        data = inner if isinstance(inner, Mapping) else structured
        return any(
            isinstance(data.get(key), (int, float))
            and not isinstance(data.get(key), bool)
            for key in _ABSENCE_TOTAL_KEYS
        )
    outcome = attempt.outcome
    structured = outcome.structured if outcome else None
    if not isinstance(structured, Mapping):
        return False
    inner = structured.get("data")
    data = inner if isinstance(inner, Mapping) else structured
    if any(
        isinstance(data.get(key), (int, float))
        and not isinstance(data.get(key), bool)
        for key in _ABSENCE_TOTAL_KEYS
    ):
        return True
    collections = [
        data[key]
        for key in _ABSENCE_COLLECTION_KEYS
        if isinstance(data.get(key), (list, tuple))
    ]
    if collections:
        # No aggregate field: derivable only when the owner declares
        # the collection complete — otherwise the count is invented.
        return any(
            node.get("is_complete") is True
            for node in (structured, inner)
            if isinstance(node, Mapping)
        )
    return False


def _attempt_demonstrates_anchored(
    attempt: GovernedCapabilityAttempt,
    obligation: MaterialObligation,
    delivery: str | None = None,
) -> bool:
    """Anchored obligation demonstration via mechanical echo matching.

    An anchored obligation is demonstrated only when the bound attempt
    echoes the declared anchor vocabulary AND the declared operation
    class AND carries the evidence of the declared kind — business
    evidence for ordinary obligations, authoritative absence for
    complete-empty owner answers, and an owner-attested postcondition
    for ``operation=act``. READ never demonstrates ACT.

    ``delivery`` (the typed plan's ``goal.output_mode``) scopes
    completeness: an ``enumeration`` obligation is not demonstrated by
    a provably partial collection window (pertinent but incomplete
    acquisition → bound/INCONCLUSIVE); an ``aggregation`` obligation
    requires an authoritative metric or provably complete collection
    — never a count invented from an unverifiable window.
    """
    if attempt.status is not GovernedCapabilityStatus.SUCCESS:
        return False
    if attempt.provenance is None or not attempt.provenance.is_complete:
        return False
    if "discovery_metadata_observation" in attempt.limitations:
        return False
    if obligation.evidence_source is not None:
        if (
            obligation.evidence_source.casefold()
            not in _attempt_anchor_tokens(attempt)
        ):
            return False
    if obligation.operation is not None:
        if _attempt_operation_class(attempt) != obligation.operation:
            return False
        if obligation.operation == (
            SpecialistOperationClass.ACT.value.casefold()
        ):
            return _attempt_postcondition_demonstrated(attempt)
    keys = _obligation_identity_keys(obligation.description)
    if keys:
        if _attempt_matches_identity_keys(attempt, keys):
            return True
        # Authoritative absence demonstrates only inside the queried
        # scope: the obligated identity must be bound to THIS attempt —
        # an empty-complete answer for product A never proves absence
        # for product B (RC5-R3). The invoked identity (governed args)
        # is the query-scope proof; owner-echoed roots are the
        # result-scope proof.
        if not _attempt_declares_authoritative_absence(attempt):
            return False
        return bool(
            keys & _attempt_invocation_identity_keys(attempt)
            or keys
            & {
                item.casefold()
                for item in _attempt_identifier_roots(attempt)
            }
        )
    if _is_business_evidence_attempt(attempt):
        if delivery == "enumeration" and (
            not _attempt_collection_proven_complete(attempt)
        ):
            # Pertinent but unproven coverage — partial windows and
            # unknown-completeness collections alike stay bound, never
            # demonstrated (UNKNOWN_COMPLETENESS != PROVEN_COMPLETE).
            return False
        if delivery == "aggregation" and (
            not _attempt_declares_aggregate_metric(attempt)
        ):
            return False
        return True
    return _attempt_declares_authoritative_absence(attempt)


def _attempt_satisfies_obligation(
    attempt: GovernedCapabilityAttempt,
    obligation: "MaterialObligation | str | Mapping",
    delivery: str | None = None,
) -> bool:
    """Obligation DEMONSTRATED check via owner-authoritative evidence.

    RC5 (doc 327): satisfaction requires demonstrated evidence, not
    mere binding. Identifier-literal obligations keep strict identity
    matching. Anchored obligations (``evidence_source``/``operation``)
    require mechanical echo/operation verification against
    owner-declared metadata. A non-identifier obligation WITHOUT
    anchors declares subject scope: bound evidence marks it
    INCONCLUSIVE (see ``_attempt_binds_obligation``) — semantic
    pertinence is not deterministically verifiable and must never be
    presumed demonstrated. Capability names alone never prove that
    the requested business fact was acquired (doc 237 R-E2).
    """
    item = _obligation_item(obligation)
    needle = item.description
    if not needle:
        return False
    if item.evidence_source is not None:
        return _attempt_demonstrates_anchored(
            attempt, item, delivery=delivery
        )
    if item.operation is not None:
        # ``operation`` alone is a restriction, never a pertinence
        # proof (RC5-R2): a matching op-class cannot demonstrate the
        # business subject. It gates identity matching below; a
        # recorded contradiction disproves outright.
        operation_class = _attempt_operation_class(attempt)
        if (
            operation_class is not None
            and operation_class != item.operation
        ):
            return False
    keys = _obligation_identity_keys(needle)
    if not keys:
        if " " in needle or "\t" in needle:
            # Subject/collection/metric scope without a declared anchor
            # binds governed business evidence but never demonstrates it
            # — semantic pertinence is not mechanically verifiable.
            return False
        # Single-token obligation may be an exact owner code the
        # identifier grammar does not cover — keep strict equality.
        keys = {needle.casefold()}
    return _attempt_matches_identity_keys(attempt, keys)


def _attempt_binds_obligation(
    attempt: GovernedCapabilityAttempt,
    obligation: "MaterialObligation | str | Mapping",
) -> bool:
    """BOUND-not-demonstrated check (RC5 EVIDENCE_BOUND state).

    True when a governed, complete, fully-provenant observation is
    bound to the obligation's declared scope/kind but demonstration is
    unverifiable: unanchored subject scope with business evidence, an
    anchored attempt whose echo cannot be checked (absent metadata) or
    whose demonstration failed on completeness/postcondition. An
    echoed DIFFERENT kind or operation disproves the bind outright.
    """
    item = _obligation_item(obligation)
    if not item.description:
        return False
    if attempt.status is not GovernedCapabilityStatus.SUCCESS:
        return False
    if not (attempt.content or "").strip():
        return False
    if attempt.provenance is None or not attempt.provenance.is_complete:
        return False
    if "discovery_metadata_observation" in attempt.limitations:
        return False
    anchored = item.evidence_source is not None
    if anchored:
        tokens = _attempt_anchor_tokens(attempt)
        source = item.evidence_source.casefold()
        if source not in tokens:
            if _attempt_surface_anchor_match(attempt, source):
                # Envelope-surface match: bound only — a generic
                # envelope name never demonstrates evidence kind.
                pass
            elif tokens:
                # Owner echoed/invoked a different kind — disproven.
                return False
            # else: nothing verifiable — bound, unproven.
        if item.operation is not None:
            operation_class = _attempt_operation_class(attempt)
            if (
                operation_class is not None
                and operation_class != item.operation
            ):
                # Operation class recorded and contradicts — disproven.
                return False
        keys = _obligation_identity_keys(item.description)
        if keys:
            invoked = _attempt_invocation_identity_keys(attempt)
            if invoked and not (keys & invoked):
                # The invocation provably queried a different identity
                # — the bound evidence cannot speak for the obligated
                # scope (RC5-R3); the bind is disproven.
                return False
        return True
    if item.operation is not None:
        # Operation-only declaration: the restriction can disprove
        # the bind but never carries pertinence (RC5-R2) — fall
        # through to subject/identity binding below.
        operation_class = _attempt_operation_class(attempt)
        if (
            operation_class is not None
            and operation_class != item.operation
        ):
            return False
    keys = _obligation_identity_keys(item.description)
    if keys:
        # Identity obligations are strict-only; no weak binding.
        return False
    needle = item.description
    if " " in needle or "\t" in needle:
        return _is_business_evidence_attempt(attempt)
    return False


def _joint_collection_coverage(
    obligation: MaterialObligation,
    business: tuple[GovernedCapabilityAttempt, ...],
) -> bool:
    """Anchored pages of the same scope jointly covering the owner
    total — bounded multipage completeness (WS-4).

    All contributing attempts must (a) succeed with complete
    provenance and outcome, (b) echo the declared anchor, (c) share
    the identical queried-identity scope, and (d) declare the SAME
    numeric total. Distinct delivered items are fingerprinted by
    canonical content; the union must equal or exceed that total —
    a union larger than the declared total proves the pages were not
    one set (different scope/dupes masked) and demonstrates nothing.
    Raw page-count arithmetic (``40+40+29``) is never accepted.
    """
    import json as _json

    source = obligation.evidence_source.casefold()
    candidates: list[GovernedCapabilityAttempt] = []
    identities: set[tuple] = set()
    totals: set[float] = set()
    for attempt in business:
        if attempt.status is not GovernedCapabilityStatus.SUCCESS:
            continue
        prov = attempt.provenance
        if prov is None or not prov.is_complete:
            continue
        outcome = attempt.outcome
        if outcome is None or not outcome.is_complete:
            continue
        if source not in _attempt_anchor_tokens(attempt):
            continue
        structured = outcome.structured
        if not isinstance(structured, Mapping):
            continue
        inner = structured.get("data")
        data = inner if isinstance(inner, Mapping) else structured
        data_total = [
            data[key]
            for key in _ABSENCE_TOTAL_KEYS
            if isinstance(data.get(key), (int, float))
            and not isinstance(data.get(key), bool)
        ]
        if not data_total:
            continue
        candidates.append((attempt, data))
        identities.add(tuple(prov.invocation_identity or ()))
        totals.add(max(data_total))
    if len(candidates) < 2 or len(identities) > 1 or len(totals) > 1:
        return False
    total = totals.pop()
    seen: set[str] = set()
    for _, data in candidates:
        for key in _ABSENCE_COLLECTION_KEYS:
            items = data.get(key)
            if not isinstance(items, (list, tuple)):
                continue
            for item in items:
                try:
                    seen.add(
                        _json.dumps(
                            item, sort_keys=True, default=str
                        )
                    )
                except (TypeError, ValueError):
                    continue
    return bool(seen) and len(seen) == int(total)


def _evaluate_material_obligations(
    *,
    obligations: tuple[MaterialObligation, ...] | tuple[str, ...],
    business: tuple[GovernedCapabilityAttempt, ...],
    delivery: str | None = None,
) -> tuple[tuple[str, str], ...]:
    """Return ``(obligation_description, state)`` per obligation.

    State semantics (RC5): ``SATISFIED`` = demonstrated by
    owner-authoritative evidence (strict identity, verified anchor, or
    authoritative absence); ``INCONCLUSIVE`` = governed evidence is
    bound but pertinence/kind/postcondition is not demonstrable;
    ``UNSATISFIED`` = no bound evidence or a provably wrong kind/scope;
    ``UNAVAILABLE`` = the authoritative source could not be reached.
    One satisfied attempt binds at most one obligation (1:1); bound-
    but-unverified attempts may corroborate several obligations since
    INCONCLUSIVE claims nothing about sufficiency.
    """
    results: list[tuple[str, str]] = []
    used: set[int] = set()
    for raw_obligation in obligations:
        obligation = _obligation_item(raw_obligation)
        matched = None
        for index, attempt in enumerate(business):
            if index in used:
                continue
            if not _attempt_satisfies_obligation(
                attempt, obligation, delivery=delivery
            ):
                continue
            matched = attempt
            used.add(index)
            break
        if matched is not None:
            results.append(
                (obligation.description, OBLIGATION_SATISFIED)
            )
            continue
        if (
            delivery == "enumeration"
            and obligation.evidence_source is not None
            and _joint_collection_coverage(
                obligation, business
            )
        ):
            # Multi-page acquisition: no single window proved complete,
            # but anchored pages of the same scope jointly cover the
            # owner-declared total — continuity + set identity proven.
            results.append(
                (obligation.description, OBLIGATION_SATISFIED)
            )
            continue
        bound = any(
            _attempt_binds_obligation(attempt, obligation)
            for attempt in business
        )
        if bound:
            results.append(
                (obligation.description, OBLIGATION_INCONCLUSIVE)
            )
            continue
        unavailable = any(
            item.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
            for item in business
        )
        state = (
            OBLIGATION_UNAVAILABLE if unavailable else OBLIGATION_UNSATISFIED
        )
        results.append((obligation.description, state))
    return tuple(results)


# Concrete-value tokens in synthesized prose — numeric literals that
# must be traceable verbatim to bound evidence before the model's
# prose may be presented (doc 256 G1 prose-is-proposal contract).
_CONCRETE_VALUE_TOKENS = re.compile(r"\d[\d.,/:%-]*")
_BR_DATE_TOKEN = re.compile(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})")
_ISO_DATE_TOKEN = re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})")


def _numeric_canonical(text: str) -> "Decimal | None":
    """Canonical numeric value of one separator-formatted literal.

    pt-BR/en-US ambiguity is resolved structurally: when both ``,`` and
    ``.`` appear, the LAST separator is the decimal mark and earlier
    ones are thousands; with a single separator kind, every group after
    the first must be exactly three digits to read as thousands —
    otherwise the separator is decimal. ``None`` when not numeric.
    """
    if "," in text and "." in text:
        last = max(text.rfind(","), text.rfind("."))
        text = text[:last].replace(",", "").replace(".", "") + (
            "." + text[last + 1 :]
        )
    else:
        for sep in (",", "."):
            if sep in text:
                parts = text.split(sep)
                text = (
                    "".join(parts)
                    if len(parts) > 1
                    and all(len(group) == 3 for group in parts[1:])
                    else text.replace(sep, ".")
                )
                break
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _concrete_value_canonical(token: str) -> frozenset:
    """Canonical comparison forms of one concrete token — set-based.

    Token-level canonical equality replaces substring matching:
    ``175,0`` must equal ``175.0`` but never ``1175.0``; ``31/10/2003``
    must equal ``2003-10-31`` but never ``30/10/2003``; ``50220013:``
    must equal ``50220013`` but never ``502200130``. Dates canonically
    map to ISO day; numbers compare as ``Decimal``; anything else
    compares as its stripped literal.
    """
    stripped = token.strip(".,/:%-")
    if not stripped:
        return frozenset()
    out: set = set()
    match = _BR_DATE_TOKEN.fullmatch(stripped)
    if match:
        day, month, year = match.groups()
        out.add(("date", f"{year}-{int(month):02d}-{int(day):02d}"))
    match = _ISO_DATE_TOKEN.fullmatch(stripped)
    if match:
        year, month, day = match.groups()
        out.add(("date", f"{year}-{int(month):02d}-{int(day):02d}"))
    number = _numeric_canonical(stripped)
    if number is not None:
        out.add(("num", number))
    out.add(("str", stripped))
    return frozenset(out)

def _apply_declared_answer(
    *,
    terminal: GovernedCapabilityAttempt,
    declared_answer: InvestigationAnswer | None,
    collected: tuple[GovernedCapabilityAttempt, ...],
    plan: "SemanticInvestigationPlan | None",
    correlation: str,
    unbound_outcome: str | None,
) -> GovernedCapabilityAttempt:
    """Bind the Agent's native typed output to verified evidence.

    The declaration is a proposal, never authority (doc 256 G1):
    every ``evidence_refs`` index must point to an actual collected
    business-evidence attempt; a ``COMPLETE`` claim holds only when
    declared material obligations are satisfied by real owner evidence;
    declared unmet obligations/limitations merge into the terminal
    honestly. Out-of-range or non-evidence refs are dropped and
    reported — never silently trusted.
    """
    if declared_answer is None:
        return terminal

    # Schema identity is validated explicitly (doc 258 §3): an
    # unknown version is rejected whole — never partially trusted.
    if declared_answer.schema_version != "1":
        return dataclasses.replace(
            terminal,
            limitations=tuple(terminal.limitations)
            + ("declared_schema_rejected",)[:24],
        )

    business = tuple(
        item for item in collected if _is_business_evidence_attempt(item)
    )

    # Declared clarification may only fill a real gap: it never discards
    # a terminal already carrying verified business evidence (doc 258
    # §5). With verified evidence *and* still-unmet material
    # obligations, partial evidence alone does not satisfy the goal —
    # the bounded clarification applies while the verified evidence is
    # preserved (doc 259 §25).
    if (
        declared_answer.status
        is InvestigationAnswerStatus.NEEDS_CLARIFICATION
        and declared_answer.clarification_question
    ):
        unmet_obligations = False
        if (
            terminal.status is GovernedCapabilityStatus.SUCCESS
            and business
            and plan is not None
            and plan.evidence_needed
        ):
            coverage = _evaluate_material_obligations(
                obligations=plan.evidence_needed,
                business=business,
                delivery=_plan_delivery_mode(plan),
            )
            unmet_obligations = any(
                state != OBLIGATION_SATISFIED for _, state in coverage
            )
        if (
            terminal.status is GovernedCapabilityStatus.SUCCESS
            and business
            and not unmet_obligations
        ):
            return dataclasses.replace(
                terminal,
                limitations=tuple(terminal.limitations)
                + ("declared_clarification_ignored",)[:24],
            )
        partial_evidence = bool(business)
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
            correlation_id=correlation,
            content=declared_answer.clarification_question[
                :MAX_RENDER_CONTENT_CHARS
            ],
            limitations=(
                ("agent_requested_clarification",)
                + (
                    ("verified_evidence_preserved",)
                    if partial_evidence
                    else ()
                )
            ),
            error_code="investigation_clarification_required",
            admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
            outcome=terminal.outcome if partial_evidence else None,
            provenance=(
                terminal.provenance if partial_evidence else None
            ),
        )

    collected_count = len(collected)

    # Bind declared refs to real collected attempts. A valid index
    # proves the *observation's* provenance — never the truth of any
    # sentence the model generated.
    accepted_refs = 0
    dropped_refs: list[str] = []
    for index in declared_answer.evidence_refs:
        if (
            0 <= index < collected_count
            and _is_business_evidence_attempt(collected[index])
        ):
            accepted_refs += 1
        else:
            dropped_refs.append(f"evidence_ref_unbound:{index}")

    # Declared unmet obligations are model self-report — untrusted.
    # When the typed plan exists and deterministic coverage proves
    # every material obligation SATISFIED, a declared unmet item
    # contradicts verified evidence and must not surface as a
    # limitation; it is recorded once as an overridden declaration.
    declared_complete_answer = (
        declared_answer.status is InvestigationAnswerStatus.COMPLETE
    )
    declared_unmet_overridden = False
    if declared_answer.unmet_obligations and business:
        if plan is not None and plan.evidence_needed:
            coverage = _evaluate_material_obligations(
                obligations=plan.evidence_needed,
                business=business,
                delivery=_plan_delivery_mode(plan),
            )
            declared_unmet_overridden = all(
                state == OBLIGATION_SATISFIED
                for _, state in coverage
            )
        elif declared_complete_answer and not dropped_refs:
            # COMPLETE + every declared ref bound to verified business
            # evidence is self-contradictory with an unmet obligation —
            # overridden, never relayed as a real limitation.
            declared_unmet_overridden = True

    extra_limitations = list(dropped_refs)
    if declared_unmet_overridden:
        extra_limitations.append("declared_unmet_overridden")
    else:
        extra_limitations.extend(
            f"declared_unmet_obligation:{item}"
            for item in declared_answer.unmet_obligations[:8]
        )
    extra_limitations.extend(
        f"declared_limitation:{item}"[:200]
        for item in declared_answer.limitations[:8]
    )

    declared_complete = (
        declared_answer.status is InvestigationAnswerStatus.COMPLETE
    )
    declared_consistent = False
    coverage_unknown = False
    if declared_complete:
        # A COMPLETE declaration is consistent only when EVERY declared
        # ref binds to real business evidence, at least one does, and
        # material obligations are demonstrably satisfied or undeclared.
        # ``plan=None`` means coverage is unknown — the claim can never
        # be proven and is honestly reported as such.
        if dropped_refs or accepted_refs == 0:
            extra_limitations.append("declared_status_overridden")
        elif plan is None or not plan.evidence_needed:
            declared_consistent = True
            coverage_unknown = True
        else:
            coverage = _evaluate_material_obligations(
                obligations=plan.evidence_needed,
                business=business,
                delivery=_plan_delivery_mode(plan),
            )
            if all(
                state == OBLIGATION_SATISFIED for _, state in coverage
            ):
                declared_consistent = True
            else:
                extra_limitations.append("declared_status_overridden")
    elif declared_answer.status in (
        InvestigationAnswerStatus.PARTIAL,
        InvestigationAnswerStatus.INSUFFICIENT,
    ):
        # A PARTIAL/INSUFFICIENT label is model self-report, never the
        # coverage verdict: when declared refs bind to real evidence
        # the grounded portion may still be presented — never promoted
        # to complete. With a typed plan the verdict is evaluated
        # against material obligations; only without one does coverage
        # stay honestly unknown.
        if dropped_refs or accepted_refs == 0:
            extra_limitations.append("declared_status_overridden")
        else:
            declared_consistent = True
            if plan is None or not plan.evidence_needed:
                coverage_unknown = True
            else:
                coverage = _evaluate_material_obligations(
                    obligations=plan.evidence_needed,
                    business=business,
                    delivery=_plan_delivery_mode(plan),
                )
                if not all(
                    state == OBLIGATION_SATISFIED for _, state in coverage
                ):
                    extra_limitations.append(
                        "declared_status_overridden"
                    )

    # Intent-aware synthesis: a consistent declaration's ``answer`` is
    # the model's intent-aware composition over verified evidence —
    # present it instead of the deterministic field dump. Evidence and
    # provenance stay bound via the attempt's provenance/outcome; the
    # answer already passed the output validator's marker strip and the
    # evidence_refs binding above. When coverage is unknown (no plan)
    # it is honestly declared — never hidden by the accepted prose.
    #
    # Bounded hallucination guard: every concrete numeric token in the
    # synthesized prose must appear verbatim in the bound evidence
    # text — an invented value (e.g. a fabricated price) rejects the
    # prose and keeps the deterministic evidence. Semantic expansions
    # and labels the model legitimately composes ("PI — produto
    # intermediário") carry no numeric tokens and pass.
    if declared_consistent:
        answer_text = declared_answer.answer.strip()
        if answer_text:
            evidence_text = "\n".join(
                (item.content or "") for item in business
            )
            evidence_values: set = set()
            for evidence_token in _CONCRETE_VALUE_TOKENS.findall(
                evidence_text
            ):
                evidence_values.update(
                    _concrete_value_canonical(evidence_token)
                )
            # Owner-declared structured scalars (e.g. an authoritative
            # ``total``/``total_count`` in the evidence payload) are
            # bound evidence too — citing them is grounded, never
            # invented. Field-name agnostic; rendered text alone was
            # insufficient for totals exposed only as metadata.
            for item in business:
                for scalar in _owner_scalar_field_values(
                    item.outcome.structured
                    if item.outcome is not None
                    else None
                ):
                    evidence_values.update(
                        _concrete_value_canonical(scalar)
                    )
            unverified = [
                token
                for token in _CONCRETE_VALUE_TOKENS.findall(answer_text)
                if not (
                    _concrete_value_canonical(token) & evidence_values
                )
            ]
            if unverified:
                extra_limitations.append(
                    "declared_status_overridden"
                )
                extra_limitations.append(
                    f"declared_answer_unverified_values:"
                    f"{','.join(unverified[:8])}"[:200]
                )
            else:
                if coverage_unknown:
                    # Prose is presented, but the COMPLETE claim stays
                    # honestly marked unproven without a typed plan.
                    extra_limitations.append(
                        "declared_status_overridden"
                    )
                    extra_limitations.append("coverage_unknown")
                owner_incomplete = any(
                    _structured_owner_incomplete(item.outcome)
                    or "owner_result_incomplete" in item.limitations
                    for item in business
                )
                if owner_incomplete:
                    extra_limitations.append("owner_result_incomplete")
                synthesized = answer_text[:MAX_RENDER_CONTENT_CHARS]
                if owner_incomplete:
                    marker = "is_complete: false"
                    lowered = synthesized.casefold()
                    if (
                        marker not in lowered
                        and "is_complete=false" not in lowered
                        and "parcial" not in lowered
                        and "incompleta" not in lowered
                    ):
                        notice = (
                            "\n\nNota: a fonte declarou resultado "
                            "parcial (is_complete=false)."
                        )
                        room = MAX_RENDER_CONTENT_CHARS - len(notice)
                        synthesized = (
                            synthesized[: max(0, room)] + notice
                        )
                return dataclasses.replace(
                    terminal,
                    content=synthesized,
                    markdown_content=synthesized,
                    limitations=tuple(
                        dict.fromkeys(
                            tuple(terminal.limitations)
                            + tuple(extra_limitations)
                        )
                    )[:24],
                )

    if extra_limitations:
        return dataclasses.replace(
            terminal,
            limitations=tuple(
                dict.fromkeys(
                    tuple(terminal.limitations)
                    + tuple(extra_limitations)
                )
            )[:24],
        )
    return terminal


def _collected_has_authorization_denial(
    collected: tuple[GovernedCapabilityAttempt, ...] | Sequence[GovernedCapabilityAttempt],
) -> bool:
    """True when any observation is a governing authorization denial."""
    return any(
        item.status is GovernedCapabilityStatus.AUTHZ_DENIED
        or item.error_code
        in {"authz_denied", "mcp_authorization_denied"}
        for item in collected
    )


def _preserve_authorized_with_denial(
    attempt: GovernedCapabilityAttempt,
    *,
    collected: tuple[GovernedCapabilityAttempt, ...] | Sequence[GovernedCapabilityAttempt],
) -> GovernedCapabilityAttempt:
    """Keep authorized business evidence while marking a partial denial.

    A later or parallel AUTHORIZATION_DENIED must not erase legitimate
    observations, invent a not-found, or widen access. The limitation
    ``authorization_denied_partial`` is the contract signal for
    user-facing communication.
    """
    if not _collected_has_authorization_denial(collected):
        return attempt
    limits = list(attempt.limitations) + ["authorization_denied_partial"]
    return dataclasses.replace(
        attempt,
        limitations=tuple(dict.fromkeys(limits))[:24],
    )


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
        missing = _obligation_descriptions(
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
        seen_bodies: set[str] = set()
        for item in business:
            body = (item.content or "").strip()
            if body and body not in seen_bodies:
                seen_bodies.add(body)
                parts.append(body)
        partial_limits = [
            "identifier_coverage_incomplete",
            *[f"uncovered_identifier:{item}" for item in pending[:8]],
        ]
        if _collected_has_authorization_denial(collected):
            # Authorized evidence may remain; denied evidence must not
            # be disclosed or recovered by alternate-owner bypass.
            partial_limits.append("authorization_denied_partial")
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id=correlation,
            content=(
                "\n\n---\n\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]
                or None
            ),
            limitations=tuple(partial_limits),
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
                delivery=_plan_delivery_mode(plan),
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
        return _preserve_authorized_with_denial(
            composed_attempt, collected=collected
        )

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
            delivery=_plan_delivery_mode(plan),
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
                        "related_observations_insufficient",
                        "ref05_target_unbound",
                        *(
                            f"ref05_missing_target:{token}"
                            for token in targets[:8]
                        ),
                    ),
                    error_code="investigation_target_binding_failed",
                    content=business[0].content,
                    provenance=business[0].provenance,
                    outcome=business[0].outcome,
                )
        if obligations and obligations != targets:
            coverage = _evaluate_material_obligations(
                obligations=obligations,
                business=business,
                delivery=_plan_delivery_mode(plan),
            )
            if any(state != OBLIGATION_SATISFIED for _, state in coverage):
                related = ("related_observations_insufficient",) if business else ()
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                    limitations=tuple(
                        [LIMITATION_INSUFFICIENT_EVIDENCE]
                        + list(related)
                        + [
                            f"obligation_{state.lower()}:{oid}"
                            for oid, state in coverage
                            if state != OBLIGATION_SATISFIED
                        ]
                    )[:24],
                    error_code="investigation_incomplete_coverage",
                    content=business[0].content if business else None,
                    provenance=(
                        business[0].provenance if business else None
                    ),
                    outcome=business[0].outcome if business else None,
                )
        partial = _partial_coverage()
        if partial is not None:
            return partial
        # F4: plan/obligations absent → evidence may still be returned on
        # the fast path, but coverage of the user objective is unproven.
        if not obligations:
            return _preserve_authorized_with_denial(
                dataclasses.replace(
                    business[0],
                    limitations=tuple(
                        dict.fromkeys(
                            list(business[0].limitations)
                            + ["coverage_unknown"]
                        )
                    )[:24],
                ),
                collected=collected,
            )
        return _preserve_authorized_with_denial(
            business[0], collected=collected
        )

    if business:
        # R-E4: preserve every verified observation — do not drop all
        # but the last when no structure composition applies.
        if obligations:
            coverage = _evaluate_material_obligations(
                obligations=obligations,
                business=business,
                delivery=_plan_delivery_mode(plan),
            )
            if any(state != OBLIGATION_SATISFIED for _, state in coverage):
                return GovernedCapabilityAttempt(
                    status=GovernedCapabilityStatus.NOT_APPLICABLE,
                    correlation_id=correlation,
                    admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
                    limitations=tuple(
                        [LIMITATION_INSUFFICIENT_EVIDENCE]
                        + ["material_obligations_incomplete"]
                        + ["related_observations_insufficient"]
                        + [
                            f"obligation_{state.lower()}:{oid}"
                            for oid, state in coverage
                            if state != OBLIGATION_SATISFIED
                        ]
                    )[:24],
                    error_code="investigation_incomplete_coverage",
                    content=(
                        "\n\n---\n\n".join(
                            (item.content or "").strip()
                            for item in business
                            if (item.content or "").strip()
                        )[:MAX_RENDER_CONTENT_CHARS]
                        or None
                    ),
                    provenance=business[-1].provenance,
                    outcome=business[-1].outcome,
                )
        partial = _partial_coverage()
        if partial is not None:
            return partial
        parts: list[str] = []
        seen_bodies: set[str] = set()
        for item in business:
            body = (item.content or "").strip()
            if not body or body in seen_bodies:
                continue
            seen_bodies.add(body)
            parts.append(body)
        joined = "\n\n---\n\n".join(parts)[:MAX_RENDER_CONTENT_CHARS]
        last = business[-1]
        provenance = last.provenance
        if provenance is not None and len(business) > 1:
            # Dedup removes visual blocks, never lineage: every bound
            # observation keeps its SourceRef in the final provenance.
            merged_refs = tuple(
                dict.fromkeys(
                    ref
                    for item in business
                    if item.provenance is not None
                    for ref in item.provenance.source_refs
                )
            )
            provenance = dataclasses.replace(
                provenance, source_refs=merged_refs
            )
        multi_limits = list(last.limitations) + [
            "multiple_observations_without_compose"
        ]
        if not obligations:
            multi_limits.append("coverage_unknown")
        return _preserve_authorized_with_denial(
            GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SUCCESS,
                correlation_id=correlation,
                content=joined or last.content,
                limitations=tuple(dict.fromkeys(multi_limits))[:24],
                provenance=provenance,
                outcome=last.outcome,
                markdown_content=last.markdown_content,
            ),
            collected=collected,
        )

    last = collected[-1]
    denied = next(
        (
            item
            for item in reversed(collected)
            if item.status is GovernedCapabilityStatus.AUTHZ_DENIED
            or item.error_code
            in {"authz_denied", "mcp_authorization_denied"}
        ),
        None,
    )
    terminal = denied if denied is not None else last
    _logger.info(
        "orchestration stage=semantic_finalize "
        "decision=no_business_evidence status=%s correlation_id=%s",
        terminal.status.value,
        correlation,
    )
    pending = _uncovered_named_identifiers(input_text, ())
    gap_limitations = list(terminal.limitations) + [
        LIMITATION_INSUFFICIENT_EVIDENCE
    ]
    if denied is not None:
        gap_limitations.append("authorization_denied")
    if pending:
        gap_limitations.append("identifier_coverage_incomplete")
        gap_limitations.extend(
            f"uncovered_identifier:{item}" for item in pending[:8]
        )
    preserved_codes = {
        "authz_denied",
        "mcp_authorization_denied",
        "owner_query_miss",
        "catalog_owner_unavailable",
    }
    if denied is not None:
        status = GovernedCapabilityStatus.AUTHZ_DENIED
        error_code = (
            denied.error_code
            if denied.error_code in preserved_codes
            else "mcp_authorization_denied"
        )
    else:
        status = (
            last.status
            if last.status is not GovernedCapabilityStatus.SUCCESS
            else GovernedCapabilityStatus.NOT_APPLICABLE
        )
        error_code = (
            last.error_code
            if last.error_code in preserved_codes
            else "investigation_no_business_evidence"
        )
    return GovernedCapabilityAttempt(
        status=status,
        correlation_id=correlation,
        content=terminal.content,
        limitations=tuple(dict.fromkeys(gap_limitations))[:24],
        error_code=error_code,
        admission_outcome=unbound_outcome or OWNER_PATH_UNBOUND,
        provenance=terminal.provenance,
        outcome=terminal.outcome,
        owner_hint=getattr(terminal, "owner_hint", None),
    )











# Canonical sensitive credential concepts. Keys are normalized
def _json_block(block: Any) -> str:
    return json.dumps(block, ensure_ascii=False, default=str)










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
        covered.update(
            item.casefold() for item in _attempt_identifier_roots(attempt)
        )
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

