"""Governed write orchestrator — PREPARE / ACT over existing GPT Actions services."""

from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import Request

from tm_app.application.governed_writes.diagnostic_capabilities import (
    CREATE_CAPABILITY as _DIAG_CREATE,
    MANAGE_CAPABILITY as _DIAG_MANAGE,
    DiagnosticWriteStack,
    execute as _diag_execute,
    prepare_create as _diag_prepare_create,
    prepare_manage as _diag_prepare_manage,
    recompute_fingerprint as _diag_recompute_fingerprint,
    require_prepare_authz as _diag_prepare_authz,
    verify as _diag_verify,
)
from tm_app.application.governed_writes.errors import (
    BUSINESS_RULE,
    FORBIDDEN,
    INTERNAL,
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
    PROPOSAL_MISMATCH,
    PROPOSAL_REQUIRED,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.confirmation_policy import (
    CONFIRM_BEFORE_ACT,
    execution_policy_for_capability,
)
from tm_app.application.governed_writes.proposal import (
    create_proposal,
    fingerprint,
)
from tm_app.application.governed_writes.proposal_store import (
    get_proposal_store,
    load_valid_proposal,
)
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)
from tm_app.application.gpt_actions.parity_capabilities_service import (
    MEETING_MINUTE_READ_ACTION_VALUES,
)
from tm_app.core.auth_actor import actor_from_request

logger = logging.getLogger(__name__)

# Capabilities that require PREPARE → ACT
WRITE_CAPABILITIES = frozenset(
    {
        "create_record",
        "update_record",
        "delete_record",
        "duplicate_record",
        "activate_revision",
        "recalculate_dashboard",
        "meeting_minute_workflow",
        "commit_improvement_package",
        "manage_evidence",
        "adjust_shared_resource_cost",
        "meeting_minute_manage",
        _DIAG_CREATE,
        _DIAG_MANAGE,
        # Portal parity — Transformômetro tasks
        "create_task",
        "update_task",
        "complete_task",
        "cancel_task",
        # Portal parity — interaction room / messages
        "open_interaction_room",
        "post_interaction_message",
        "edit_interaction_message",
        "delete_interaction_message",
        "toggle_interaction_reaction",
        "pin_interaction_message",
        "unpin_interaction_message",
        "mark_interaction_read",
        # Portal parity — governed special operations (signature profile
        # metadata; BPMN XML macro-diagram import — text transport).
        "update_signature_profile",
        "import_diagram_bpmn_xml",
    }
)

# Transformômetro task capabilities (Portal parity — TaskCommandUseCases).
TASK_CAPABILITIES = frozenset(
    {"create_task", "update_task", "complete_task", "cancel_task"}
)

# Interaction room capabilities (Portal parity — InteractionRoomUseCases).
INTERACTION_ROOM_CAPABILITIES = frozenset(
    {
        "open_interaction_room",
        "post_interaction_message",
        "edit_interaction_message",
        "delete_interaction_message",
        "toggle_interaction_reaction",
        "pin_interaction_message",
        "unpin_interaction_message",
        "mark_interaction_read",
    }
)

# Tool/Actions ``action`` argument → orchestrator capability. The transport
# passes a coarse action; the semantic capability (which carries the
# canonical execution_policy) is resolved here — never by transport prose.
# Semantic family: collaboration (tasks + interaction rooms share the
# same governed PREPARE family; policy stays per-capability).
COLLABORATION_ACTION_TO_CAPABILITY = {
    "create_task": "create_task",
    "update_task": "update_task",
    "complete_task": "complete_task",
    "cancel_task": "cancel_task",
    "open_room": "open_interaction_room",
    "post_message": "post_interaction_message",
    "edit_message": "edit_interaction_message",
    "delete_message": "delete_interaction_message",
    "toggle_reaction": "toggle_interaction_reaction",
    "pin_message": "pin_interaction_message",
    "unpin_message": "unpin_interaction_message",
    "mark_room_read": "mark_interaction_read",
}

# Collaboration READ surface — shared by MCP + GPT Actions projections.
COLLABORATION_READ_ACTIONS = frozenset(
    {
        "my_tasks",
        "task",
        "process_tasks",
        "rooms",
        "room",
        "messages",
        "attachments",
    }
)

# Back-compat alias — legacy single-domain transports (task_read /
# prepare_task, interaction_room_read / prepare_interaction_room) kept
# for internal callers; resolves to the same canonical capabilities.
TASK_ACTION_TO_CAPABILITY = {
    "create": "create_task",
    "update": "update_task",
    "complete": "complete_task",
    "cancel": "cancel_task",
}

INTERACTION_ROOM_ACTION_TO_CAPABILITY = {
    "open": "open_interaction_room",
    "post_message": "post_interaction_message",
    "edit_message": "edit_interaction_message",
    "delete_message": "delete_interaction_message",
    "reaction": "toggle_interaction_reaction",
    "pin": "pin_interaction_message",
    "unpin": "unpin_interaction_message",
    "mark_read": "mark_interaction_read",
}

# Semantic family: special governed operations — one-shot domain writes
# that are neither records nor collaboration (revision lifecycle,
# dashboard recompute, improvement package, shared-resource cost).
GOVERNED_OPERATION_ACTION_TO_CAPABILITY = {
    "activate_revision": "activate_revision",
    "recalculate_dashboard": "recalculate_dashboard",
    "commit_improvement_package": "commit_improvement_package",
    "adjust_shared_resource_cost": "adjust_shared_resource_cost",
    "update_signature_profile": "update_signature_profile",
    "import_diagram_bpmn_xml": "import_diagram_bpmn_xml",
}

# Semantic family: meeting minutes — workflow transitions and minute
# manage writes share one PREPARE surface; READ actions stay on the
# meeting_minute_read tool. Policy stays per-capability.
MEETING_MINUTE_ACTION_TO_CAPABILITY = {
    "send": "meeting_minute_workflow",
    "finalize": "meeting_minute_workflow",
    "cancel": "meeting_minute_workflow",
    "refuse": "meeting_minute_workflow",
    "resend": "meeting_minute_manage",
    "create_version": "meeting_minute_manage",
    "set_participants": "meeting_minute_manage",
    "set_signers": "meeting_minute_manage",
}

# Canonical meeting_minute_read surface — READ actions plus the
# non-persisting transcript analysis. Single source:
# parity_capabilities_service.MEETING_MINUTE_READ_ACTION_VALUES
# (domain vocabulary owner); shared by MCP + GPT Actions.
MEETING_MINUTE_READ_ACTIONS = MEETING_MINUTE_READ_ACTION_VALUES

# meeting_minute_manage actions that are READ (no prepare) — derived
# from the canonical set; transcript generation is analysis-only.
MEETING_MANAGE_READ_ACTIONS = MEETING_MINUTE_READ_ACTIONS - {
    "generate_from_transcript"
}
MEETING_MANAGE_NON_ACT = MEETING_MINUTE_READ_ACTIONS


def _actor(request: Request) -> tuple[str, str | None]:
    user_id, email, _name = actor_from_request(request)
    if not user_id:
        user = getattr(request.state, "user", None)
        user_id = str(getattr(user, "id", None) or "") or None
        email = email or getattr(user, "email", None)
    if not user_id:
        raise GovernedWriteError(
            "Authentication required.",
            code="unauthenticated",
            status_code=401,
        )
    return str(user_id), str(email) if email else None


def _raise_gpt(exc: GptActionsError) -> None:
    code = VALIDATION
    if exc.status_code == 403:
        code = FORBIDDEN
    elif exc.status_code == 404:
        code = NOT_FOUND
    elif exc.status_code == 409:
        code = BUSINESS_RULE
    raise GovernedWriteError(
        exc.message,
        code=code,
        status_code=exc.status_code,
        data=dict(exc.data or {}),
    ) from exc


class GovernedWriteOrchestrator:
    def __init__(
        self,
        dispatch: GptActionsDispatchService | None = None,
        packages: GuidedImprovementPackageService | None = None,
        diagnostic_stack: DiagnosticWriteStack | None = None,
    ) -> None:
        self._dispatch = dispatch or GptActionsDispatchService()
        self._packages = packages or GuidedImprovementPackageService(self._dispatch)
        # Canonical Diagnostic write path — composed at the interface layer
        # (application never instantiates infrastructure).
        self._diagnostic_stack = diagnostic_stack

    # ------------------------------------------------------------------ prepare

    def prepare(
        self,
        request: Request,
        *,
        capability: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        if capability not in WRITE_CAPABILITIES:
            raise GovernedWriteError(
                f"Unknown write capability '{capability}'.",
                code=VALIDATION,
                status_code=400,
            )
        actor_id, actor_email = _actor(request)
        try:
            prepared = self._prepare_exact(request, capability=capability, args=args)
        except GptActionsError as exc:
            _raise_gpt(exc)

        # Canonical write-execution policy (TEO-CANONICAL-WRITE-EXECUTION-
        # POLICY-04): NON_DESTRUCTIVE = auto_act, DESTRUCTIVE =
        # confirm_before_act. The explicit-confirmation flag is sealed
        # from the canonical policy — never hardcoded per transport.
        execution_policy = execution_policy_for_capability(capability)
        requirement = dict(prepared.get("confirmation_requirement") or {})
        requirement["explicit_user_confirmation"] = (
            execution_policy == CONFIRM_BEFORE_ACT
        )
        prepared["confirmation_requirement"] = requirement

        proposal = create_proposal(
            capability=capability,
            actor_id=actor_id,
            actor_email=actor_email,
            resource_type=prepared["resource_type"],
            resource_id=prepared.get("resource_id"),
            current_state_fingerprint=prepared["current_state_fingerprint"],
            exact_change=prepared["exact_change"],
            validation_result=prepared["validation_result"],
            consequential_impact=prepared["consequential_impact"],
            confirmation_requirement=prepared["confirmation_requirement"],
            expected_postcondition=prepared["expected_postcondition"],
            execution_policy=execution_policy,
            meta=prepared.get("meta") or {},
        )
        handle = get_proposal_store().put(proposal)
        public = proposal.to_public_dict()
        public["proposal_handle"] = handle
        public["ready"] = bool(prepared["validation_result"].get("ready", True))
        if not public["ready"]:
            # Incomplete package: do not allow ACT; keep handle for transparency but mark
            public["act_allowed"] = False
        else:
            public["act_allowed"] = True
        return public

    def _prepare_exact(
        self, request: Request, *, capability: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        if capability == "create_record":
            return self._prep_create(request, args)
        if capability == "update_record":
            return self._prep_update(request, args)
        if capability == "delete_record":
            return self._prep_delete(request, args)
        if capability == "duplicate_record":
            return self._prep_duplicate(request, args)
        if capability == "activate_revision":
            return self._prep_activate(request, args)
        if capability == "recalculate_dashboard":
            return self._prep_recalculate(request, args)
        if capability == "meeting_minute_workflow":
            return self._prep_minute_workflow(request, args)
        if capability == "commit_improvement_package":
            return self._prep_package(request, args)
        if capability == "manage_evidence":
            return self._prep_evidence(request, args)
        if capability == "adjust_shared_resource_cost":
            return self._prep_cost(request, args)
        if capability == "update_signature_profile":
            return self._prep_signature_profile(request, args)
        if capability == "import_diagram_bpmn_xml":
            return self._prep_bpmn_import(request, args)
        if capability == "meeting_minute_manage":
            return self._prep_minute_manage(request, args)
        if capability in (_DIAG_CREATE, _DIAG_MANAGE):
            stack = self._require_diag_stack()
            _diag_prepare_authz(request)
            if capability == _DIAG_CREATE:
                return _diag_prepare_create(stack, args)
            return _diag_prepare_manage(stack, args)
        if capability in TASK_CAPABILITIES:
            return self._prep_task(request, capability=capability, args=args)
        if capability in INTERACTION_ROOM_CAPABILITIES:
            return self._prep_interaction_room(
                request, capability=capability, args=args
            )
        raise GovernedWriteError(
            f"Prepare not implemented for '{capability}'.",
            code=VALIDATION,
            status_code=400,
        )

    def _require_diag_stack(self) -> DiagnosticWriteStack:
        if self._diagnostic_stack is None:
            raise GovernedWriteError(
                "Diagnostic write stack not configured.",
                code=INTERNAL,
                status_code=500,
            )
        return self._diagnostic_stack

    # --- Portal parity: tasks / interaction room ---------------------------
    # PREPARE only reads current state and seals the exact change — the
    # canonical use cases (TaskCommandUseCases / InteractionRoomUseCases)
    # execute the write at ACT and re-validate AuthZ + domain rules.

    def _prep_task(
        self, request: Request, *, capability: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        self._dispatch._require_access(request)
        action = str(args.get("action") or "").strip()
        task_id = str(args.get("task_id") or "").strip()
        missing: list[str] = []
        if capability == "create_task":
            if not str(args.get("title") or "").strip():
                missing.append("title")
            current_fp = fingerprint(
                {"resource": "transformometro_task", "exists": False}
            )
            resource_id = None
        else:
            if not task_id:
                missing.append("task_id")
                current_fp = fingerprint({"task_id": None})
                resource_id = None
            else:
                current = self._dispatch.get_task(request, task_id)
                current_fp = fingerprint(current)
                resource_id = task_id
        if capability == "update_task" and not str(
            args.get("title") or ""
        ).strip():
            missing.append("title")
        exact = {
            "action": action,
            "task_id": task_id or None,
            "title": args.get("title"),
            "description": args.get("description"),
            "assignee_user_id": args.get("assignee_user_id"),
            "due_date": args.get("due_date"),
            "source_interaction_message_id": args.get(
                "source_interaction_message_id"
            ),
        }
        return {
            "resource_type": "transformometro_task",
            "resource_id": resource_id,
            "current_state_fingerprint": current_fp,
            "exact_change": exact,
            "validation_result": {
                "ready": not missing,
                "missing": missing,
                "checks": ["authz_probe", "current_state_read"],
            },
            "consequential_impact": {
                "persists": True,
                "operation": capability,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "task_state",
                "action": action,
                "task_id": resource_id,
            },
        }

    def _prep_interaction_room(
        self, request: Request, *, capability: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        self._dispatch._require_access(request)
        action = str(args.get("action") or "").strip()
        room_id = str(args.get("room_id") or "").strip()
        message_id = str(args.get("message_id") or "").strip()
        missing: list[str] = []
        resource_id = None
        if capability == "open_interaction_room":
            processo_id = str(args.get("processo_id") or "").strip()
            if not processo_id:
                missing.append("processo_id")
            current_fp = fingerprint(
                {"interaction_room": "get_or_create", "processo_id": processo_id}
            )
        elif capability in {"post_interaction_message", "mark_interaction_read"}:
            if not room_id:
                missing.append("room_id")
                current_fp = fingerprint({"room_id": None})
            else:
                current_fp = fingerprint(
                    self._dispatch.get_room(request, room_id)
                )
                resource_id = room_id
            if capability == "post_interaction_message" and not str(
                args.get("content") or ""
            ).strip():
                missing.append("content")
        else:
            for field, value in (("room_id", room_id), ("message_id", message_id)):
                if not value:
                    missing.append(field)
            if missing:
                current_fp = fingerprint({"room_id": room_id or None})
            else:
                current_fp = fingerprint(
                    self._dispatch.get_room_message(request, room_id, message_id)
                )
                resource_id = message_id
            if capability in {
                "edit_interaction_message",
            } and not str(args.get("content") or "").strip():
                missing.append("content")
            if capability == "toggle_interaction_reaction" and not str(
                args.get("reaction") or ""
            ).strip():
                missing.append("reaction")
        exact = {
            "action": action,
            "processo_id": args.get("processo_id"),
            "room_id": room_id or None,
            "message_id": message_id or None,
            "content": args.get("content"),
            "parent_id": args.get("parent_id"),
            "mentions": args.get("mentions"),
            "reaction": args.get("reaction"),
        }
        return {
            "resource_type": "interaction_room",
            "resource_id": resource_id,
            "current_state_fingerprint": current_fp,
            "exact_change": exact,
            "validation_result": {
                "ready": not missing,
                "missing": missing,
                "checks": ["authz_probe", "current_state_read"],
            },
            "consequential_impact": {
                "persists": True,
                "operation": capability,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "interaction_room_state",
                "action": action,
                "room_id": room_id or None,
                "message_id": message_id or None,
            },
        }

    def _prep_create(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        entity = str(args.get("entity") or "").strip()
        data = dict(args.get("data") or {})
        from tm_app.application.gpt_actions.entities import parse_entity
        from tm_app.interface.http.branch_access_http import (
            require_transformometro_view_access,
        )

        parsed = parse_entity(entity)
        err = require_transformometro_view_access(request)
        if err is not None:
            raise GovernedWriteError(
                "Sem permissão transformometro.access.",
                code=FORBIDDEN,
                status_code=403,
            )
        if entity in {"branch", "shared_resource", "resource_cost"}:
            from tm_app.interface.http.branch_access_http import require_portal_manage

            err = require_portal_manage(request)
            if err is not None:
                raise GovernedWriteError(
                    "Sem permissão transformometro.manage.",
                    code=FORBIDDEN,
                    status_code=403,
                )
        # Capability matrix (support) — AuthZ still revalidated on ACT.
        self._dispatch._require_capability(parsed, "create")
        exact = {"entity": entity, "data": data}
        return {
            "resource_type": entity,
            "resource_id": None,
            "current_state_fingerprint": fingerprint({"entity": entity, "exists": False}),
            "exact_change": exact,
            "validation_result": {"ready": True, "checks": ["entity_known", "authz_probe"]},
            "consequential_impact": {"persists": True, "operation": "create"},
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "resource_exists",
                "entity": entity,
            },
        }

    def _prep_update(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        entity = str(args.get("entity") or "").strip()
        record_id = str(args.get("id") or "").strip()
        data = dict(args.get("data") or {})
        current = self._dispatch.get_record(request, entity, record_id)
        exact = {"entity": entity, "id": record_id, "data": data}
        conf: dict[str, Any] = {}
        if entity == "revision" and (
            "vigencia_inicio" in data or "vigencia_fim" in data or "data" in args
        ):
            conf["confirm_vigencia_change_may_be_required"] = True
        validation: dict[str, Any] = {"ready": True}
        if entity == "instance" and "contexto" in data:
            from tm_app.domain.decomposition.decomposition_tree_v1 import (
                DecompositionValidationError,
                validate_instancia_contexto_v1,
            )

            try:
                validate_instancia_contexto_v1(data["contexto"])
            except DecompositionValidationError as exc:
                validation = {"ready": False, "errors": [str(exc)]}
        return {
            "resource_type": entity,
            "resource_id": record_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": exact,
            "validation_result": validation,
            "consequential_impact": {"persists": True, "operation": "update"},
            "confirmation_requirement": conf,
            "expected_postcondition": {
                "type": "resource_matches_change",
                "entity": entity,
                "id": record_id,
            },
        }

    def _prep_delete(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        entity = str(args.get("entity") or "").strip()
        record_id = str(args.get("id") or "").strip()
        current = self._dispatch.get_record(request, entity, record_id)
        return {
            "resource_type": entity,
            "resource_id": record_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": {"entity": entity, "id": record_id, "operation": "delete"},
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": "soft_delete",
                "destructive": True,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "resource_soft_deleted_or_absent",
                "entity": entity,
                "id": record_id,
            },
        }

    def _prep_duplicate(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        entity = str(args.get("entity") or "").strip()
        record_id = str(args.get("id") or "").strip()
        data = dict(args.get("data") or {}) if args.get("data") else {}
        current = self._dispatch.get_record(request, entity, record_id)
        return {
            "resource_type": entity,
            "resource_id": record_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": {
                "entity": entity,
                "id": record_id,
                "data": data,
                "operation": "duplicate",
            },
            "validation_result": {"ready": True},
            "consequential_impact": {"persists": True, "operation": "duplicate"},
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "duplicate_exists",
                "source_id": record_id,
                "entity": entity,
            },
        }

    def _prep_activate(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        revisao_id = str(args.get("id") or args.get("revisao_id") or "").strip()
        current = self._dispatch.get_record(request, "revision", revisao_id)
        # AuthZ gate during prepare
        self._dispatch._require_revisao_manage_access(request, revisao_id)
        return {
            "resource_type": "revision",
            "resource_id": revisao_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": {"revisao_id": revisao_id, "operation": "activate"},
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": "activate_revision",
                "overwrites_current": True,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "revision_active",
                "revisao_id": revisao_id,
            },
        }

    def _prep_recalculate(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        self._dispatch._require_access(request)
        exact = {
            "revisao_id": args.get("revisao_id"),
            "processo_id": args.get("processo_id"),
            "competencia_inicio": args.get("competencia_inicio"),
            "competencia_fim": args.get("competencia_fim"),
            "operation": "recalculate_dashboard",
        }
        return {
            "resource_type": "dashboard_cache",
            "resource_id": str(args.get("processo_id") or args.get("revisao_id") or "global"),
            "current_state_fingerprint": fingerprint({"scope": exact}),
            "exact_change": exact,
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": "recalculate",
                "note": "Updates materialised dashboard cache; GET dashboard may use live engine.",
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "recalculate_result_present",
                "fields": ["mode"],
            },
        }

    def _prep_minute_workflow(
        self, request: Request, args: dict[str, Any]
    ) -> dict[str, Any]:
        minute_id = str(args.get("id") or args.get("minute_id") or "").strip()
        action = str(args.get("action") or "").strip()
        reason = args.get("reason")
        # AuthZ at PREPARE (same manage gate as ACT send/finalize/cancel).
        try:
            self._dispatch._minutes._load(request.state.user, "manage", minute_id)
        except PermissionError as exc:
            raise GptActionsError(str(exc), 403) from exc
        except LookupError as exc:
            raise GptActionsError(str(exc), 404) from exc
        from tm_app.application.gpt_actions.entities import GptMeetingMinuteWorkflow

        try:
            GptMeetingMinuteWorkflow(action)
        except ValueError as exc:
            raise GptActionsError(
                f"Invalid action '{action}'. Allowed: {[a.value for a in GptMeetingMinuteWorkflow]}",
                400,
            ) from exc
        validation = {"ready": True}
        if action == GptMeetingMinuteWorkflow.REFUSE.value and not str(reason or "").strip():
            validation = {"ready": False, "missing": ["reason"]}
        current = self._dispatch.get_record(request, "meeting_minute", minute_id)
        return {
            "resource_type": "meeting_minute",
            "resource_id": minute_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": {
                "minute_id": minute_id,
                "action": action,
                "reason": reason,
            },
            "validation_result": validation,
            "consequential_impact": {
                "persists": True,
                "operation": f"meeting_workflow_{action}",
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "meeting_minute_workflow_state",
                "minute_id": minute_id,
                "action": action,
            },
        }

    def _prep_package(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        # AuthZ: require authenticated actor with transformometro view at minimum;
        # writes revalidated on commit via create paths.
        from tm_app.interface.http.branch_access_http import (
            require_transformometro_view_access,
        )

        err = require_transformometro_view_access(request)
        if err is not None:
            raise GovernedWriteError(
                "Sem permissão transformometro.access.",
                code=FORBIDDEN,
                status_code=403,
            )
        body = {
            "process": args.get("process") or {},
            "instance": args.get("instance") or {},
            "baseline": args.get("baseline"),
            "scenario": args.get("scenario"),
            "activate_scenario": bool(args.get("activate_scenario", False)),
            "recalculate": bool(args.get("recalculate", False)),
        }
        # Structural checklist only at PREPARE. Referential preflight runs on ACT/commit.
        validation = self._packages.validate(request, body)
        ready = bool(validation.get("ready"))
        return {
            "resource_type": "improvement_package",
            "resource_id": str(
                (body.get("process") or {}).get("id")
                or (body.get("process") or {}).get("processo_id")
                or ""
            )
            or None,
            "current_state_fingerprint": fingerprint(
                {
                    "process": body["process"],
                    "instance": body["instance"],
                    "baseline": body.get("baseline"),
                    "scenario": body.get("scenario"),
                }
            ),
            "exact_change": body,
            "validation_result": {
                "ready": ready,
                "missing": validation.get("missing") or [],
                "checklist": validation.get("checklist"),
            },
            "consequential_impact": {
                "persists": ready,
                "operation": "commit_improvement_package",
                "activate_scenario": body["activate_scenario"],
                "recalculate": body["recalculate"],
            },
            "confirmation_requirement": {
                "requires_ready": True,
            },
            "expected_postcondition": {
                "type": "package_ids_present",
                "require_keys": ["processo_id", "instancia_id"],
            },
        }

    def _prep_evidence(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        exact = {
            "scope": args.get("scope"),
            "operation": args.get("operation"),
            "parent_id": args.get("parent_id"),
            "evidence_id": args.get("evidence_id"),
            "url_externa": args.get("url_externa"),
            "descricao": args.get("descricao"),
            "confirm_delete": bool(args.get("confirm_delete", False)),
        }
        if exact["operation"] == "delete" and not exact["confirm_delete"]:
            raise GovernedWriteError(
                "confirm_delete=true is required for evidence delete.",
                code=VALIDATION,
                status_code=400,
            )
        listed = self._dispatch.list_evidence(
            request, scope=str(exact["scope"]), parent_id=str(exact["parent_id"])
        )
        conf = {}
        if exact["operation"] == "delete":
            conf["confirm_delete"] = True
        return {
            "resource_type": "evidence",
            "resource_id": str(exact.get("evidence_id") or exact["parent_id"]),
            "current_state_fingerprint": fingerprint(listed),
            "exact_change": exact,
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": f"evidence_{exact['operation']}",
                "destructive": exact["operation"] == "delete",
            },
            "confirmation_requirement": conf,
            "expected_postcondition": {
                "type": "evidence_verified_flag",
            },
        }

    def _prep_cost(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        exact = {
            "recurso_compartilhado_id": args.get("recurso_compartilhado_id"),
            "valor_mensal": args.get("valor_mensal"),
            "vigente_desde": args.get("vigente_desde"),
            "observacoes": args.get("observacoes"),
        }
        current = self._dispatch.get_record(
            request, "shared_resource", str(exact["recurso_compartilhado_id"])
        )
        return {
            "resource_type": "shared_resource_cost",
            "resource_id": str(exact["recurso_compartilhado_id"]),
            "current_state_fingerprint": fingerprint(current),
            "exact_change": exact,
            "validation_result": {"ready": True},
            "consequential_impact": {"persists": True, "operation": "adjust_cost"},
            "confirmation_requirement": {},
            "expected_postcondition": {"type": "cost_verified_flag"},
        }

    def _prep_signature_profile(
        self, request: Request, args: dict[str, Any]
    ) -> dict[str, Any]:
        display_name = str(args.get("display_name") or "").strip()
        if not display_name:
            raise GptActionsError("display_name is required.", 400)
        # AuthZ probe at PREPARE: read current profile as the caller (the
        # canonical service enforces authentication again at ACT).
        current = self._dispatch.get_my_signature_profile(request)
        return {
            "resource_type": "user_signature_profile",
            "resource_id": "me",
            "current_state_fingerprint": fingerprint(current),
            "exact_change": {"display_name": display_name},
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": "update_signature_profile",
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "signature_profile_display_name",
                "display_name": display_name,
            },
        }

    def _prep_bpmn_import(
        self, request: Request, args: dict[str, Any]
    ) -> dict[str, Any]:
        processo_id = str(
            args.get("processo_id") or args.get("id") or ""
        ).strip()
        xml = str(args.get("xml") or "")
        # PREPARE: manage-scope AuthZ + existence + dry XML parse.
        validation = self._dispatch.validate_bpmn_import(
            request, processo_id=processo_id, xml=xml
        )
        return {
            "resource_type": "process_diagram",
            "resource_id": processo_id,
            "current_state_fingerprint": fingerprint(
                validation["current_diagram"]
            ),
            "exact_change": {"processo_id": processo_id, "xml": xml},
            "validation_result": {
                "ready": True,
                "parsed_nodes": validation["parsed_nodes"],
                "parsed_edges": validation["parsed_edges"],
            },
            "consequential_impact": {
                "persists": True,
                "operation": "import_diagram_bpmn_xml",
                "overwrites_macro_diagram": True,
            },
            "confirmation_requirement": {},
            "expected_postcondition": {
                "type": "diagram_bpmn_imported",
                "processo_id": processo_id,
            },
        }

    def _prep_minute_manage(
        self, request: Request, args: dict[str, Any]
    ) -> dict[str, Any]:
        action = str(args.get("action") or "").strip()
        if action in MEETING_MANAGE_NON_ACT:
            raise GovernedWriteError(
                f"Action '{action}' is not an ACT write. Use the READ/analysis tool.",
                code=VALIDATION,
                status_code=400,
            )
        minute_id = str(args.get("minute_id") or "").strip() or None
        data = dict(args.get("data") or {})
        current = (
            self._dispatch.get_record(request, "meeting_minute", minute_id)
            if minute_id
            else {"minute_id": None}
        )
        conf: dict[str, Any] = {}
        if action == "resend":
            conf["confirm_resend"] = True
        return {
            "resource_type": "meeting_minute",
            "resource_id": minute_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": {
                "action": action,
                "minute_id": minute_id,
                "data": data,
            },
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": f"meeting_manage_{action}",
            },
            "confirmation_requirement": conf,
            "expected_postcondition": {
                "type": "meeting_manage_result",
                "action": action,
            },
        }

    # ------------------------------------------------------------------ act

    def act(
        self,
        request: Request,
        *,
        capability: str,
        proposal_handle: str | None,
        fingerprint_recompute: Callable[[Request, dict[str, Any]], str] | None = None,
    ) -> dict[str, Any]:
        if not proposal_handle:
            raise GovernedWriteError(
                "proposal_handle is required for ACT.",
                code=PROPOSAL_REQUIRED,
                status_code=400,
            )
        actor_id, _email = _actor(request)
        proposal = load_valid_proposal(
            proposal_handle=proposal_handle,
            actor_id=actor_id,
            expected_capability=capability,
        )
        if not proposal.validation_result.get("ready", True):
            raise GovernedWriteError(
                "Proposal is not ready for ACT (validation failed / incomplete).",
                code=BUSINESS_RULE,
                status_code=400,
                data={"missing": proposal.validation_result.get("missing")},
            )

        # Re-read current state fingerprint
        try:
            current_fp = self._recompute_fingerprint(request, proposal)
        except GptActionsError as exc:
            _raise_gpt(exc)
        if current_fp != proposal.current_state_fingerprint:
            raise GovernedWriteError(
                "Current state changed since PREPARE. Prepare again.",
                code=PROPOSAL_STALE,
                status_code=409,
                data={
                    "expected_fingerprint": proposal.current_state_fingerprint,
                    "actual_fingerprint": current_fp,
                },
            )

        # Revalidate AuthZ + execute canonical write
        try:
            write_result = self._execute(request, proposal)
        except GptActionsError as exc:
            _raise_gpt(exc)

        get_proposal_store().consume(proposal.proposal_id)

        # Authoritative read-back / postcondition
        try:
            verified_payload = self._verify(request, proposal, write_result)
        except GovernedWriteError:
            raise
        except Exception as exc:
            logger.exception("governed_write_verify_failed capability=%s", capability)
            raise GovernedWriteError(
                "Write may have occurred but outcome could not be verified. "
                "Do not retry blindly; read current state first.",
                code=OUTCOME_VERIFICATION_FAILED,
                status_code=409,
                data={
                    "capability": capability,
                    "write_result_present": write_result is not None,
                    "error_type": type(exc).__name__,
                },
            ) from exc

        return {
            "verified": True,
            "capability": capability,
            "proposal_id": proposal.proposal_id,
            "data": verified_payload,
        }

    def _recompute_fingerprint(
        self, request: Request, proposal
    ) -> str:
        change = proposal.exact_change
        cap = proposal.capability
        if cap == "create_record":
            return fingerprint(
                {"entity": change.get("entity"), "exists": False}
            )
        if cap in {"update_record", "delete_record", "duplicate_record"}:
            current = self._dispatch.get_record(
                request, str(change["entity"]), str(change["id"])
            )
            return fingerprint(current)
        if cap == "activate_revision":
            return fingerprint(
                self._dispatch.get_record(
                    request, "revision", str(change["revisao_id"])
                )
            )
        if cap == "recalculate_dashboard":
            return fingerprint({"scope": {k: change.get(k) for k in (
                "revisao_id", "processo_id", "competencia_inicio", "competencia_fim",
                "operation",
            )}})
        if cap == "meeting_minute_workflow":
            return fingerprint(
                self._dispatch.get_record(
                    request, "meeting_minute", str(change["minute_id"])
                )
            )
        if cap == "commit_improvement_package":
            return fingerprint(
                {
                    "process": change.get("process"),
                    "instance": change.get("instance"),
                    "baseline": change.get("baseline"),
                    "scenario": change.get("scenario"),
                }
            )
        if cap == "manage_evidence":
            listed = self._dispatch.list_evidence(
                request,
                scope=str(change["scope"]),
                parent_id=str(change["parent_id"]),
            )
            return fingerprint(listed)
        if cap == "adjust_shared_resource_cost":
            return fingerprint(
                self._dispatch.get_record(
                    request,
                    "shared_resource",
                    str(change["recurso_compartilhado_id"]),
                )
            )
        if cap == "update_signature_profile":
            return fingerprint(
                self._dispatch.get_my_signature_profile(request)
            )
        if cap == "import_diagram_bpmn_xml":
            return fingerprint(
                self._dispatch.read_process_diagram(
                    request, str(change["processo_id"])
                )
            )
        if cap == "meeting_minute_manage":
            mid = change.get("minute_id")
            if mid:
                return fingerprint(
                    self._dispatch.get_record(request, "meeting_minute", str(mid))
                )
            return fingerprint({"minute_id": None})
        if cap in (_DIAG_CREATE, _DIAG_MANAGE):
            return _diag_recompute_fingerprint(
                self._require_diag_stack(), cap, change
            )
        if cap == "create_task":
            return fingerprint(
                {"resource": "transformometro_task", "exists": False}
            )
        if cap in TASK_CAPABILITIES:
            return fingerprint(
                self._dispatch.get_task(request, str(change["task_id"]))
            )
        if cap == "open_interaction_room":
            return fingerprint(
                {
                    "interaction_room": "get_or_create",
                    "processo_id": change.get("processo_id"),
                }
            )
        if cap in {"post_interaction_message", "mark_interaction_read"}:
            return fingerprint(
                self._dispatch.get_room(request, str(change["room_id"]))
            )
        if cap in INTERACTION_ROOM_CAPABILITIES:
            return fingerprint(
                self._dispatch.get_room_message(
                    request, str(change["room_id"]), str(change["message_id"])
                )
            )
        raise GovernedWriteError(
            "Fingerprint recompute unsupported.",
            code=VALIDATION,
            status_code=500,
        )

    def _execute(self, request: Request, proposal) -> Any:
        change = proposal.exact_change
        cap = proposal.capability
        if cap == "create_record":
            data, _msg, _status = self._dispatch.create_record(
                request, change["entity"], {"data": change.get("data") or {}}
            )
            return data
        if cap == "update_record":
            data, _msg = self._dispatch.update_record(
                request,
                change["entity"],
                change["id"],
                {"data": change.get("data") or {}},
            )
            return data
        if cap == "delete_record":
            data, _msg = self._dispatch.delete_record(
                request, change["entity"], change["id"]
            )
            return data
        if cap == "duplicate_record":
            data, _msg, _status = self._dispatch.duplicate_record(
                request,
                change["entity"],
                change["id"],
                {"data": change.get("data") or {}} if change.get("data") else None,
            )
            return data
        if cap == "activate_revision":
            return self._dispatch.activate_revision(request, change["revisao_id"])
        if cap == "recalculate_dashboard":
            return self._dispatch.recalculate_dashboard(
                request,
                revisao_id=change.get("revisao_id"),
                processo_id=change.get("processo_id"),
                competencia_inicio=change.get("competencia_inicio"),
                competencia_fim=change.get("competencia_fim"),
            )
        if cap == "meeting_minute_workflow":
            return self._dispatch.meeting_minute_workflow(
                request,
                change["minute_id"],
                action=change["action"],
                reason=change.get("reason"),
            )
        if cap == "commit_improvement_package":
            # Force non-dry_run ACT of the exact prepared package
            body = dict(change)
            body["dry_run"] = False
            return self._packages.commit(request, body)
        if cap == "manage_evidence":
            return self._dispatch.manage_evidence(
                request,
                scope=str(change["scope"]),
                operation=str(change["operation"]),
                parent_id=str(change["parent_id"]),
                evidence_id=change.get("evidence_id"),
                url_externa=change.get("url_externa"),
                descricao=change.get("descricao"),
                confirm_delete=bool(change.get("confirm_delete", False)),
            )
        if cap == "adjust_shared_resource_cost":
            return self._dispatch.adjust_shared_resource_cost(
                request,
                recurso_compartilhado_id=str(change["recurso_compartilhado_id"]),
                valor_mensal=float(change["valor_mensal"]),
                vigente_desde=str(change["vigente_desde"]),
                observacoes=change.get("observacoes"),
            )
        if cap == "update_signature_profile":
            return self._dispatch.update_signature_profile(
                request, display_name=str(change["display_name"])
            )
        if cap == "import_diagram_bpmn_xml":
            return self._dispatch.import_diagram_bpmn_xml(
                request,
                processo_id=str(change["processo_id"]),
                xml=str(change["xml"]),
            )
        if cap in TASK_CAPABILITIES:
            return self._dispatch.task_write(
                request, str(change["action"]), change
            )
        if cap in INTERACTION_ROOM_CAPABILITIES:
            return self._dispatch.room_write(
                request, str(change["action"]), change
            )
        if cap == "meeting_minute_manage":
            return self._dispatch.manage_meeting_minute(
                request,
                action=str(change["action"]),
                minute_id=change.get("minute_id"),
                payload=dict(change.get("data") or {}),
            )
        if cap in (_DIAG_CREATE, _DIAG_MANAGE):
            return _diag_execute(self._require_diag_stack(), change)
        raise GovernedWriteError(
            f"ACT not implemented for '{cap}'.",
            code=VALIDATION,
            status_code=500,
        )

    def _verify(self, request: Request, proposal, write_result: Any) -> dict[str, Any]:
        change = proposal.exact_change
        cap = proposal.capability
        expected = proposal.expected_postcondition or {}

        if cap == "create_record":
            entity = change["entity"]
            rid = self._extract_id(entity, write_result)
            if not rid:
                raise GovernedWriteError(
                    "Create returned no id for read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            read = self._dispatch.get_record(request, entity, rid)
            return {"resource": read, "id": rid}

        if cap == "update_record":
            read = self._dispatch.get_record(
                request, change["entity"], change["id"]
            )
            return {"resource": read}

        if cap == "delete_record":
            try:
                self._dispatch.get_record(request, change["entity"], change["id"])
                # soft-delete may still return row with status — accept write_result
                return {"deleted_id": change["id"], "write_result": write_result}
            except GptActionsError as exc:
                if exc.status_code == 404:
                    return {"deleted_id": change["id"], "absent": True}
                raise

        if cap == "duplicate_record":
            entity = change["entity"]
            rid = self._extract_id(entity, write_result)
            if not rid:
                raise GovernedWriteError(
                    "Duplicate returned no id for read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            read = self._dispatch.get_record(request, entity, rid)
            return {"resource": read, "id": rid, "source_id": change["id"]}

        if cap == "activate_revision":
            read = self._dispatch.get_record(
                request, "revision", change["revisao_id"]
            )
            active = bool(
                read.get("ativa")
                or read.get("is_active")
                or read.get("atual")
                or write_result
            )
            if not active and not write_result:
                raise GovernedWriteError(
                    "Activation not confirmed by read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"revision": read, "write_result": write_result}

        if cap == "recalculate_dashboard":
            if not isinstance(write_result, dict) or "mode" not in write_result:
                raise GovernedWriteError(
                    "Recalculate did not return expected mode.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"recalculate": write_result}

        if cap == "meeting_minute_workflow":
            read = self._dispatch.get_record(
                request, "meeting_minute", change["minute_id"]
            )
            return {"minute": read, "workflow_result": write_result}

        if cap == "commit_improvement_package":
            ids = (write_result or {}).get("ids") or {}
            if not ids.get("processo_id") or not ids.get("instancia_id"):
                raise GovernedWriteError(
                    "Package commit missing authoritative ids.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            processo = self._dispatch.get_record(
                request, "process", str(ids["processo_id"])
            )
            instancia = self._dispatch.get_record(
                request, "instance", str(ids["instancia_id"])
            )
            return {
                "ids": ids,
                "process": processo,
                "instance": instancia,
                "commit": write_result,
            }

        if cap == "manage_evidence":
            if not isinstance(write_result, dict) or not write_result.get("verified"):
                raise GovernedWriteError(
                    "Evidence write not verified by authoritative read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                    data={"write_result": write_result},
                )
            return write_result

        if cap == "adjust_shared_resource_cost":
            if not isinstance(write_result, dict) or not write_result.get("verified"):
                raise GovernedWriteError(
                    "Cost adjustment not verified.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                    data={"write_result": write_result},
                )
            return write_result

        if cap == "update_signature_profile":
            read = self._dispatch.get_my_signature_profile(request)
            expected_name = str(
                expected.get("display_name") or change.get("display_name") or ""
            )
            if str(read.get("display_name") or "") != expected_name:
                raise GovernedWriteError(
                    "Signature profile update not confirmed by read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"signature_profile": read, "write_result": write_result}

        if cap == "import_diagram_bpmn_xml":
            if not isinstance(write_result, dict) or not write_result.get(
                "verified"
            ):
                raise GovernedWriteError(
                    "BPMN import not verified by authoritative read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                    data={"write_result": write_result},
                )
            read = self._dispatch.read_process_diagram(
                request, str(change["processo_id"])
            )
            return {"diagram": read, "write_result": write_result}

        if cap in TASK_CAPABILITIES:
            # Use cases already verify read-back; assert the authoritative
            # state matches the sealed postcondition.
            tid = str(change.get("task_id") or (write_result or {}).get("id") or "")
            read = self._dispatch.get_task(request, tid)
            if cap == "complete_task" and read.get("status") != "completed":
                raise GovernedWriteError(
                    "Task completion not confirmed by read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            if cap == "cancel_task" and read.get("status") != "cancelled":
                raise GovernedWriteError(
                    "Task cancellation not confirmed by read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                )
            return {"task": read, "write_result": write_result}

        if cap in INTERACTION_ROOM_CAPABILITIES:
            if not isinstance(write_result, dict) or not write_result.get("id"):
                raise GovernedWriteError(
                    "Interaction-room write not confirmed by read-back.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                    data={"write_result": write_result},
                )
            return {"interaction_room": write_result}

        if cap == "meeting_minute_manage":
            if isinstance(write_result, dict) and write_result.get("verified") is False:
                raise GovernedWriteError(
                    "Meeting manage action not verified.",
                    code=OUTCOME_VERIFICATION_FAILED,
                    status_code=409,
                    data={"write_result": write_result},
                )
            mid = change.get("minute_id")
            read = None
            if mid:
                try:
                    read = self._dispatch.get_record(
                        request, "meeting_minute", str(mid)
                    )
                except GptActionsError:
                    read = None
            return {"result": write_result, "minute": read}

        if cap in (_DIAG_CREATE, _DIAG_MANAGE):
            # write_result is the authoritative DiagnosticReadView returned
            # by the canonical use case — verify it matches the sealed change.
            return _diag_verify(change, write_result)

        return {"write_result": write_result, "expected": expected}

    @staticmethod
    def _extract_id(entity: str, row: Any) -> str | None:
        if not isinstance(row, dict):
            return None
        candidates = [
            "id",
            f"{entity}_id",
            "filial_id",
            "setor_id",
            "processo_id",
            "instancia_id",
            "revisao_id",
            "medicao_id",
            "investimento_id",
            "recurso_id",
            "recurso_custo_id",
            "vinculo_id",
            "ata_id",
            "meeting_minute_id",
        ]
        for key in candidates:
            val = row.get(key)
            if val:
                return str(val)
        # nested
        for nest in ("revisao", "processo", "instancia", "minute"):
            nested = row.get(nest)
            if isinstance(nested, dict):
                for key in candidates:
                    val = nested.get(key)
                    if val:
                        return str(val)
        return None
