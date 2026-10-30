"""Semantic V3 MCP tools — thin adapter over the governed TÉO surface.

Six semantic tools (``get_context|read|analyze|knowledge|execute|delete``)
route to the SAME services, orchestrator and policies the legacy family
tools use. No new authority is created here:

- capability resolution → ``capability_registry`` + orchestrator enums;
- execution policy → ``confirmation_policy`` (auto_act/confirm_before_act);
- destructive classification → ``DESTRUCTIVE_DELETE_OPERATIONS``;
- AuthZ/validation/audit/read-back → canonical use cases, unchanged.

``execute`` performs the governed PREPARE→ACT chain in one call ONLY when
the sealed ``execution_policy`` is ``auto_act`` — exactly the semantics the
Actions transport implements via ``commit_now``. ``confirm_before_act``
returns a pending proposal; a second call carrying
``proposal_id``+``confirmation=true`` commits through the canonical
``commit_proposal`` path. ``delete`` never auto-executes.
"""

from __future__ import annotations

import inspect
from typing import Any

from mcp.types import CallToolResult

from tm_app.application.governed_writes.confirmation_policy import (
    AUTO_ACT,
    delete_operations,
    execution_policy_for_capability,
    is_destructive_delete,
)
from tm_app.application.governed_writes.errors import (
    OUTCOME_VERIFICATION_FAILED,
    PREPARE_PERSISTED_STATE_VIOLATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    COLLABORATION_ACTION_TO_CAPABILITY,
    COLLABORATION_READ_ACTIONS,
    GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
    INTERACTION_ROOM_ACTION_TO_CAPABILITY,
    MEETING_MINUTE_ACTION_TO_CAPABILITY,
    TASK_ACTION_TO_CAPABILITY,
    WRITE_CAPABILITIES,
    _actor,
)
from tm_app.application.helpdesk.helpdesk_write_capabilities import (
    HELPDESK_ACTION_TO_CAPABILITY,
)
from tm_app.application.governed_writes.diagnostic_capabilities import (
    MANAGE_ACTIONS as DIAGNOSTIC_MANAGE_ACTIONS,
)
from tm_app.application.governed_writes.proposal_store import (
    load_valid_proposal,
    resolve_proposal_handle,
)
from tm_app.application.gpt_actions.capability_descriptors import (
    OPERATION_TO_CAPABILITY,
    RECORD_OPERATIONS,
)
from tm_app.application.gpt_actions.entities import (
    GptEntity,
    entity_supports,
    parse_entity,
)
from tm_app.application.gpt_actions.parity_capabilities_service import (
    MEETING_MINUTE_READ_ACTION_VALUES,
)
from tm_app.interface.mcp import tool_bridge as _b


# ---------------------------------------------------------------------------
# V3 capability vocabulary — derived from the canonical maps, never invented.
# ``execute`` accepts the orchestrator capability name OR the canonical
# action vocabularies (collaboration / governed_operation / meeting-minute /
# helpdesk / diagnostic / task / room aliases) — both resolve to the same
# sealed capability.
# ---------------------------------------------------------------------------


def _action_capability_map() -> dict[str, str]:
    """Closed action-name → capability map (union of the family enums)."""
    merged: dict[str, str] = {}
    for table in (
        COLLABORATION_ACTION_TO_CAPABILITY,
        INTERACTION_ROOM_ACTION_TO_CAPABILITY,
        TASK_ACTION_TO_CAPABILITY,
        GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
        MEETING_MINUTE_ACTION_TO_CAPABILITY,
        HELPDESK_ACTION_TO_CAPABILITY,
    ):
        merged.update(table)
    return merged


_V3_EXECUTE_ACTIONS = _action_capability_map()


def _resolve_capability(raw: str) -> str | None:
    """Fail-closed capability resolution for `execute`/`delete`.

    Accepts the orchestrator capability name directly or a canonical family
    action name. Diagnostic manage actions resolve to ``manage_diagnostic``
    (the action itself travels inside ``args``).
    """
    name = str(raw or "").strip()
    if not name:
        return None
    if name in WRITE_CAPABILITIES:
        return name
    if name in _V3_EXECUTE_ACTIONS:
        return _V3_EXECUTE_ACTIONS[name]
    if name in DIAGNOSTIC_MANAGE_ACTIONS:
        return "manage_diagnostic"
    if name == "create_diagnostic":
        return name
    return None


def _filtered_call(fn, params: dict[str, Any]) -> CallToolResult:
    """Call a legacy bridge tool with only the kwargs its signature accepts."""
    sig = inspect.signature(fn)
    allowed = {
        name
        for name, p in sig.parameters.items()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    }
    kwargs = {k: v for k, v in (params or {}).items() if k in allowed}
    return fn(**kwargs)


# --- get_context --------------------------------------------------------------

_V3_CONTEXT_SECTIONS = frozenset(
    {"overview", "self", "workspace", "catalog"}
)


def tool_get_context(
    section: str | None = None,
    entity: str | None = None,
) -> CallToolResult:
    """Semantic discovery: authenticated context, workspace, catalog.

    ``section`` selects the slice — ``overview`` (default: self + workspace
    hint), ``self``, ``workspace``, ``catalog`` (full discovery catalog,
    optionally filtered by ``entity``). Context is never authorization.
    """
    try:
        section_norm = str(section or "overview").strip().lower()
        if section_norm not in _V3_CONTEXT_SECTIONS:
            return _b._error_result(
                f"Unknown get_context section '{section_norm}'. "
                f"Allowed: {sorted(_V3_CONTEXT_SECTIONS)}.",
                status_code=400,
                error_code="validation",
            )
        if section_norm == "self":
            return _b.tool_get_my_context()
        if section_norm == "workspace":
            return _b.tool_get_workspace_context()
        if section_norm == "catalog":
            return _b.tool_get_catalog(entity=entity)

        request = _b.build_mcp_request()
        context = _b.require_mcp_context()
        if not context.authorization:
            raise PermissionError("Unauthorized")
        user = context.user
        email = getattr(user, "email", None)
        display_name = getattr(user, "name", None) or email
        self_ctx = _b._user_context.get_my_context(
            _b.AuthenticatedUserContext(
                display_name=str(display_name or ""),
                email=str(email or ""),
                authorization=context.authorization,
            )
        )
        workspace = _b._workspace_context.get_workspace_context(
            context.authorization
        )
        data = {
            "self": self_ctx,
            "workspace": workspace,
            "discovery_hint": (
                "get_context(section='catalog') for the full capability "
                "catalog (entities, workflows, write schemas, policies); "
                "entity=<name> filters a single entity contract."
            ),
        }
        return _b._ok_result(
            data, "Contexto semântico do TÉO (não é autorização)."
        )
    except Exception as exc:
        return _b.handle_tool_error(exc)


# --- read --------------------------------------------------------------------

# entity vocabulary → (bridge function, allowed action set)
_V3_READ_SPECIALIZED: dict[str, tuple[str, frozenset[str]]] = {
    "process_context": ("tool_get_process_context", frozenset({"get"})),
    "process_timeline": ("tool_get_process_timeline", frozenset({"get"})),
    "solution": (
        "tool_solution_read",
        frozenset({"catalog", "context"}),
    ),
    "helpdesk": (
        "tool_helpdesk_read",
        frozenset(
            {
                "session",
                "capabilities",
                "tickets",
                "ticket",
                "attachment",
                "catalog",
            }
        ),
    ),
    "meeting_minute": (
        "tool_meeting_minute_read",
        MEETING_MINUTE_READ_ACTION_VALUES,
    ),
    "evidence": ("tool_evidence_read", frozenset({"list"})),
    "task": (
        "tool_collaboration_read",
        frozenset({"my_tasks", "task", "process_tasks"}),
    ),
    "interaction_room": (
        "tool_collaboration_read",
        COLLABORATION_READ_ACTIONS
        - {"my_tasks", "task", "process_tasks"},
    ),
    "diagnostic": ("tool_diagnostic_read", frozenset({"get", "by_revision"})),
}


def tool_read(
    entity: str,
    action: str | None = None,
    params: dict[str, Any] | None = None,
) -> CallToolResult:
    """Canonical semantic read: ``entity`` + typed ``action`` + ``params``.

    Domain entities use ``action=search|get`` (same contract as
    ``record_read``); specialized entities carry their own closed action
    vocabularies. READ only — it can never produce a write.
    """
    try:
        entity_norm = str(entity or "").strip()
        action_norm = str(action or "").strip() or "get"
        body = dict(params or {})

        if entity_norm in _V3_READ_SPECIALIZED:
            fn_name, allowed = _V3_READ_SPECIALIZED[entity_norm]
            if action_norm not in allowed:
                return _b._error_result(
                    f"Unknown read action '{action_norm}' for entity "
                    f"'{entity_norm}'. Allowed: {sorted(allowed)}.",
                    status_code=400,
                    error_code="validation",
                )
            fn = getattr(_b, fn_name)
            kwargs = _sig_kwargs(fn, body)
            if "action" in inspect.signature(fn).parameters:
                kwargs["action"] = action_norm
            return fn(**kwargs)

        try:
            parse_entity(entity_norm)
        except ValueError:
            allowed = sorted(_V3_READ_SPECIALIZED) + [
                e.value for e in GptEntity
            ]
            return _b._error_result(
                f"Unknown read entity '{entity_norm}'. Allowed: {allowed}.",
                status_code=400,
                error_code="validation",
            )
        if action_norm not in {"search", "get"}:
            return _b._error_result(
                f"Unknown read action '{action_norm}' for entity "
                f"'{entity_norm}'. Allowed: ['get', 'search'].",
                status_code=400,
                error_code="validation",
            )
        body.setdefault("entity", entity_norm)
        return _b.tool_record_read(
            action=action_norm, **_sig_kwargs(_b.tool_record_read, body)
        )
    except Exception as exc:
        return _b.handle_tool_error(exc)


def _sig_kwargs(fn, params: dict[str, Any]) -> dict[str, Any]:
    sig = inspect.signature(fn)
    allowed = {
        name
        for name, p in sig.parameters.items()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    } - {"action"}
    return {k: v for k, v in (params or {}).items() if k in allowed}


# --- analyze ------------------------------------------------------------------

_V3_ANALYZE_TRANSCRIPT_VIEW = "meeting_minute_transcript"


def tool_analyze(
    view: str,
    params: dict[str, Any] | None = None,
) -> CallToolResult:
    """Structured analysis — non-persisting computations only.

    ``view`` is the canonical analysis vocabulary (dashboard views,
    process/revision comparisons, validations, matrices) plus
    ``meeting_minute_transcript`` for the non-persisting transcript
    analysis. OBSERVED/CALCULATED/INFERRED stay separated inside each
    view's payload — nothing here persists state.
    """
    try:
        view_norm = str(view or "").strip()
        body = dict(params or {})
        if view_norm == _V3_ANALYZE_TRANSCRIPT_VIEW:
            return _b.tool_meeting_minute_read(
                action="generate_from_transcript",
                minute_id=body.get("minute_id"),
                data=body.get("data"),
            )
        body.setdefault("view", view_norm)
        return _b.tool_analyze(**_sig_kwargs(_b.tool_analyze, body))
    except Exception as exc:
        return _b.handle_tool_error(exc)


# --- knowledge -----------------------------------------------------------------

_V3_KNOWLEDGE_SOURCES: dict[str, str] = {
    "methodology": "tool_get_methodology_guide",
    "product_guide": "tool_get_product_guide",
}


def tool_knowledge(
    source: str,
    params: dict[str, Any] | None = None,
) -> CallToolResult:
    """Versioned knowledge: methodology playbooks and product guides.

    Guidance — never domain truth, AuthZ or execution policy. Live
    contracts stay in ``get_context(section='catalog')``.
    """
    try:
        source_norm = str(source or "").strip().lower()
        fn_name = _V3_KNOWLEDGE_SOURCES.get(source_norm)
        if fn_name is None:
            return _b._error_result(
                f"Unknown knowledge source '{source_norm}'. Allowed: "
                f"{sorted(_V3_KNOWLEDGE_SOURCES)}.",
                status_code=400,
                error_code="validation",
            )
        fn = getattr(_b, fn_name)
        return fn(**_sig_kwargs(fn, params or {}))
    except Exception as exc:
        return _b.handle_tool_error(exc)


# --- governed write helpers ----------------------------------------------------


def _resolve_write_target(
    *,
    capability: str | None,
    entity: str | None,
    operation: str | None,
    record_id: str | None,
    changes: dict[str, Any] | None,
    args: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]] | CallToolResult:
    """Resolve (capability, args) for `execute`/`delete` — fail closed."""
    body = dict(args or {})
    if entity is not None or operation is not None:
        op = str(operation or "").strip().lower()
        if op not in RECORD_OPERATIONS:
            return _b._error_result(
                f"Invalid operation '{operation}'. Allowed: "
                f"{sorted(RECORD_OPERATIONS)}.",
                status_code=400,
                error_code="validation",
            )
        try:
            parsed = parse_entity(str(entity or ""))
        except ValueError as exc:
            return _b._error_result(
                str(exc), status_code=400, error_code="validation"
            )
        if not entity_supports(parsed, op):
            return _b._error_result(
                f"Entity '{entity}' does not support operation '{op}'.",
                status_code=400,
                error_code="validation",
            )
        resolved = OPERATION_TO_CAPABILITY[op]
        data = dict(changes or body.pop("changes", {}) or {})
        resolved_args: dict[str, Any] = {"entity": parsed.value, "data": data}
        if op != "create":
            rid = str(record_id or body.pop("id", "") or "").strip()
            if not rid:
                return _b._error_result(
                    "record_id is required for update/delete/duplicate.",
                    status_code=400,
                    error_code="validation",
                )
            resolved_args["id"] = rid
        resolved_args.update(body)
        return resolved, resolved_args

    resolved = _resolve_capability(str(capability or ""))
    if resolved is None:
        return _b._error_result(
            f"Unknown write capability or action '{capability}'. "
            "Allowed: classified write capabilities and canonical family "
            "actions — see get_context(section='catalog').",
            status_code=400,
            error_code="validation",
        )
    # Family action vocabularies travel inside args for action-scoped
    # capabilities (diagnostic manage, meeting-minute manage/workflow,
    # evidence, collaboration, helpdesk) — the caller's `capability`
    # argument already resolves the sealed capability; the raw action is
    # preserved in args when the canonical prep expects it.
    if resolved != str(capability or "").strip():
        body.setdefault("action", str(capability).strip())
    return resolved, body


def _prepare_public(
    request, capability: str, args: dict[str, Any]
) -> dict[str, Any]:
    return _b._orchestrator.prepare(request, capability=capability, args=args)


def _proposal_envelope(capability: str, public: dict[str, Any]) -> dict[str, Any]:
    exact = public.get("exact_change") or {}
    return {
        "handle": public.get("proposal_handle"),
        "proposal_id": public.get("proposal_id"),
        "capability": public.get("capability") or capability,
        "resource_type": public.get("resource_type"),
        "resource_id": public.get("resource_id"),
        "summary": " · ".join(
            str(x)
            for x in (
                public.get("capability"),
                public.get("resource_type"),
                public.get("resource_id"),
            )
            if x
        ),
        "exact_change": exact,
        "execution_policy": public.get("execution_policy"),
        "confirmation_requirement": public.get("confirmation_requirement"),
        "expected_postcondition": public.get("expected_postcondition"),
        "expires_at": public.get("expires_at"),
        "act_allowed": public.get("act_allowed", True),
        "ready": public.get("ready", True),
    }


def _act_and_verify(
    request, capability: str, proposal_handle: str
) -> dict[str, Any] | CallToolResult:
    result = _b._orchestrator.act(
        request, capability=capability, proposal_handle=proposal_handle
    )
    if not result.get("verified"):
        return _b._error_result(
            "Write may have occurred but outcome was not verified.",
            status_code=409,
            error_code=OUTCOME_VERIFICATION_FAILED,
            data={"capability": capability, "result": result},
        )
    return result


def _execute_one(
    request,
    op: dict[str, Any],
) -> dict[str, Any] | CallToolResult:
    """One governed op: prepare → policy gate → (auto)act → verify."""
    resolved = _resolve_write_target(
        capability=op.get("capability"),
        entity=op.get("entity"),
        operation=op.get("operation"),
        record_id=op.get("record_id"),
        changes=op.get("changes"),
        args=op.get("args"),
    )
    if isinstance(resolved, CallToolResult):
        return resolved
    capability, args = resolved
    public = _prepare_public(request, capability, args)
    proposal = _proposal_envelope(capability, public)
    if public.get("persisted"):
        raise GovernedWriteError(
            "MCP PREPARE contract violation: prepare reported "
            "persisted=true — business outcome NOT declared.",
            code=PREPARE_PERSISTED_STATE_VIOLATION,
            status_code=500,
        )
    if not public.get("ready", True) or not public.get("act_allowed", True):
        return {
            "outcome": "prepared_invalid",
            "capability": capability,
            "proposal": proposal,
            "validation_result": public.get("validation_result"),
        }
    if execution_policy_for_capability(capability) == AUTO_ACT:
        acted = _act_and_verify(
            request, capability, str(public.get("proposal_handle") or "")
        )
        if isinstance(acted, CallToolResult):
            return acted
        return {
            "outcome": "executed_verified",
            "capability": capability,
            "proposal_id": acted.get("proposal_id"),
            "data": acted.get("data"),
            "postcondition": {"verified": True},
        }
    return {
        "outcome": "proposal_pending_confirmation",
        "capability": capability,
        "proposal": proposal,
        "next_step": (
            "Show the exact_change to the user; on ONE explicit "
            "confirmation call execute(proposal_id=..., confirmation=true)."
        ),
    }


# --- $ops.N.path reference resolution (multi-action dependent args) -----------

_REF_PREFIX = "$ops."


def _resolve_refs(value: Any, results: list[dict[str, Any]]) -> Any:
    """Resolve ``$ops.<index>.<path...>`` string refs from earlier results.

    Only previously EXECUTED op results are addressable — the model can
    never invent ids: a ref to a missing/failed op fails typed.
    """
    if isinstance(value, dict):
        return {k: _resolve_refs(v, results) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(v, results) for v in value]
    if not isinstance(value, str) or not value.startswith(_REF_PREFIX):
        return value
    rest = value[len(_REF_PREFIX):]
    parts = rest.split(".")
    try:
        idx = int(parts[0])
        node: Any = results[idx]
    except (ValueError, IndexError):
        raise GovernedWriteError(
            f"Invalid result reference '{value}'.",
            code="validation",
            status_code=400,
        )
    for part in parts[1:]:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            raise GovernedWriteError(
                f"Result reference '{value}' does not resolve — "
                f"missing path segment '{part}'.",
                code="validation",
                status_code=400,
            )
    return node


# --- execute -------------------------------------------------------------------


def _commit_flow(
    request,
    *,
    proposal_handle: str | None,
    proposal_id: str | None,
    confirmation: bool | None,
    require_delete_class: bool,
) -> CallToolResult:
    """Canonical commit path shared by execute/delete second calls."""
    handle = resolve_proposal_handle(
        proposal_handle=proposal_handle, proposal_id=proposal_id
    )
    actor_id, _email = _actor(request)
    proposal = load_valid_proposal(
        proposal_handle=handle, actor_id=actor_id, expected_capability=None
    )
    if require_delete_class and not _capability_is_delete_class(proposal):
        return _b._error_result(
            f"Proposal capability '{proposal.capability}' is not a "
            "destructive-delete operation — use execute for this commit.",
            status_code=400,
            error_code="validation",
        )
    policy = getattr(proposal, "execution_policy", "") or "confirm_before_act"
    if policy == "confirm_before_act" and not confirmation:
        return _b._error_result(
            "confirmation=true is required to commit this proposal. "
            "Conversational confirmation is not AuthZ; backend still "
            "revalidates.",
            status_code=400,
            error_code="validation",
            data={"error_code": "CONFIRMATION_REQUIRED"},
        )
    acted = _act_and_verify(
        request, proposal.capability, handle
    )
    if isinstance(acted, CallToolResult):
        return acted
    return _b._ok_result(
        {
            "outcome": "executed_verified",
            "capability": acted.get("capability"),
            "proposal_id": acted.get("proposal_id"),
            "data": acted.get("data"),
            "postcondition": {"verified": True},
        },
        "Write verified against authoritative read-back.",
    )


def _capability_is_delete_class(proposal: Any) -> bool:
    exact = getattr(proposal, "exact_change", None) or {}
    action = exact.get("action") or exact.get("operation")
    return is_destructive_delete(proposal.capability, action)


def tool_execute(
    capability: str | None = None,
    args: dict[str, Any] | None = None,
    entity: str | None = None,
    operation: str | None = None,
    record_id: str | None = None,
    changes: dict[str, Any] | None = None,
    ops: list[dict[str, Any]] | None = None,
    proposal_handle: str | None = None,
    proposal_id: str | None = None,
    confirmation: bool | None = None,
) -> CallToolResult:
    """Governed writes: PREPARE→(policy gate)→ACT→authoritative read-back.

    ``auto_act`` capabilities execute in this same call — the user request
    is the intent. ``confirm_before_act`` returns
    ``proposal_pending_confirmation``; commit with
    ``proposal_id``+``confirmation=true``. ``ops`` runs a typed multi-action
    sequence: refs ``$ops.N.<path>`` consume earlier read-backs; the chain
    stops on the first failure or pending-confirmation op.
    """
    try:
        request = _b.build_mcp_request()
        if proposal_handle or proposal_id:
            return _commit_flow(
                request,
                proposal_handle=proposal_handle,
                proposal_id=proposal_id,
                confirmation=confirmation,
                require_delete_class=False,
            )
        if ops:
            if not isinstance(ops, list) or not all(
                isinstance(o, dict) for o in ops
            ):
                return _b._error_result(
                    "ops must be a list of typed operation objects.",
                    status_code=400,
                    error_code="validation",
                )
            results: list[dict[str, Any]] = []
            for index, op in enumerate(ops):
                resolved_op = dict(op)
                for key in ("args", "changes"):
                    if isinstance(resolved_op.get(key), dict):
                        resolved_op[key] = _resolve_refs(
                            resolved_op[key], results
                        )
                outcome = _execute_one(request, resolved_op)
                if isinstance(outcome, CallToolResult):
                    error_detail = getattr(
                        outcome, "structuredContent", None
                    ) or getattr(outcome, "structured_content", None)
                    results.append(
                        {"index": index, "outcome": "error", "op": op}
                    )
                    return _b._ok_result(
                        {
                            "status": "partial_failed",
                            "completed": results[:-1],
                            "failed": {
                                "index": index,
                                "op": op,
                                "error": error_detail,
                            },
                            "remaining": ops[index + 1 :],
                        },
                        "Multi-action stopped at failure — earlier ops "
                        "executed; downstream ops were not attempted.",
                    )
                results.append({"index": index, **outcome})
                if outcome.get("outcome") != "executed_verified":
                    return _b._ok_result(
                        {
                            "status": "pending_confirmation"
                            if outcome.get("outcome")
                            == "proposal_pending_confirmation"
                            else "prepared_invalid",
                            "completed": results[:-1],
                            "current": results[-1],
                            "remaining": ops[index + 1 :],
                        },
                        "Multi-action paused — confirm the current "
                        "proposal, then re-run the remaining ops.",
                    )
            return _b._ok_result(
                {"status": "completed", "results": results},
                "All operations executed and verified.",
            )

        outcome = _execute_one(
            request,
            {
                "capability": capability,
                "entity": entity,
                "operation": operation,
                "record_id": record_id,
                "changes": changes,
                "args": args,
            },
        )
        if isinstance(outcome, CallToolResult):
            return outcome
        message = {
            "executed_verified": "Write verified against authoritative "
            "read-back.",
            "proposal_pending_confirmation": "Governed proposal prepared "
            "— show the exact change; one explicit user confirmation is "
            "required before commit.",
            "prepared_invalid": "Proposal prepared but not ready for "
            "commit (see validation_result).",
        }.get(str(outcome.get("outcome")), "ok")
        return _b._ok_result(outcome, message)
    except Exception as exc:
        return _b.handle_tool_error(exc)


# --- delete --------------------------------------------------------------------


def tool_delete(
    capability: str | None = None,
    args: dict[str, Any] | None = None,
    entity: str | None = None,
    record_id: str | None = None,
    proposal_handle: str | None = None,
    proposal_id: str | None = None,
    confirmation: bool | None = None,
) -> CallToolResult:
    """Destructive deletes only — exact proposal + explicit confirmation.

    Restricted to the canonical ``DESTRUCTIVE_DELETE_OPERATIONS`` set.
    Always two calls: first prepares the exact proposal; the second
    (``proposal_id``+``confirmation=true``) commits. Never auto-executes;
    a bare ``confirmation=true`` without a valid bound proposal is not
    authorization.
    """
    try:
        request = _b.build_mcp_request()
        if proposal_handle or proposal_id:
            return _commit_flow(
                request,
                proposal_handle=proposal_handle,
                proposal_id=proposal_id,
                confirmation=confirmation,
                require_delete_class=True,
            )
        body = dict(args or {})
        action = body.get("action") or body.get("operation")
        if entity is not None:
            resolved = _resolve_write_target(
                capability=None,
                entity=entity,
                operation="delete",
                record_id=record_id,
                changes=None,
                args=body,
            )
        else:
            resolved = _resolve_write_target(
                capability=capability,
                entity=None,
                operation=None,
                record_id=record_id,
                changes=None,
                args=body,
            )
            if not isinstance(resolved, CallToolResult):
                resolved_cap, resolved_args = resolved
                action = resolved_args.get("action") or resolved_args.get(
                    "operation"
                )
                if not is_destructive_delete(resolved_cap, action):
                    return _b._error_result(
                        f"Capability '{resolved_cap}' (action "
                        f"'{action}') is not a destructive-delete "
                        "operation — use execute. Allowed delete "
                        f"operations: {sorted(c for c, _ in delete_operations())}.",
                        status_code=400,
                        error_code="validation",
                    )
        if isinstance(resolved, CallToolResult):
            return resolved
        resolved_cap, resolved_args = resolved
        public = _prepare_public(request, resolved_cap, resolved_args)
        if public.get("persisted"):
            raise GovernedWriteError(
                "MCP PREPARE contract violation: prepare reported "
                "persisted=true — business outcome NOT declared.",
                code=PREPARE_PERSISTED_STATE_VIOLATION,
                status_code=500,
            )
        return _b._ok_result(
            {
                "outcome": "proposal_pending_confirmation",
                "capability": resolved_cap,
                "proposal": _proposal_envelope(resolved_cap, public),
                "validation_result": public.get("validation_result"),
                "next_step": (
                    "Show the exact_change to the user; on ONE explicit "
                    "confirmation call delete(proposal_id=..., "
                    "confirmation=true)."
                ),
            },
            "Destructive proposal prepared — explicit confirmation "
            "required.",
        )
    except Exception as exc:
        return _b.handle_tool_error(exc)


__all__ = [
    "tool_get_context",
    "tool_read",
    "tool_analyze",
    "tool_knowledge",
    "tool_execute",
    "tool_delete",
]
