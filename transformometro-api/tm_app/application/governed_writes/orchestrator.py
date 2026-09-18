"""Governed write orchestrator — PREPARE / ACT over existing GPT Actions services."""

from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import Request

from tm_app.application.governed_writes.errors import (
    BUSINESS_RULE,
    FORBIDDEN,
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
    PROPOSAL_MISMATCH,
    PROPOSAL_REQUIRED,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
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
    }
)

# meeting_minute_manage actions that are READ (no prepare)
MEETING_MANAGE_READ_ACTIONS = frozenset(
    {
        "pending_signatures",
        "audit",
        "versions",
        "participants",
        "signers",
    }
)

# generate_from_transcript = PREPARE-like analysis, no persist
MEETING_MANAGE_NON_ACT = frozenset({"generate_from_transcript"}) | MEETING_MANAGE_READ_ACTIONS


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
    ) -> None:
        self._dispatch = dispatch or GptActionsDispatchService()
        self._packages = packages or GuidedImprovementPackageService(self._dispatch)

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
        if capability == "meeting_minute_manage":
            return self._prep_minute_manage(request, args)
        raise GovernedWriteError(
            f"Prepare not implemented for '{capability}'.",
            code=VALIDATION,
            status_code=400,
        )

    def _prep_create(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        entity = str(args.get("entity") or "").strip()
        data = dict(args.get("data") or {})
        from tm_app.application.gpt_actions.entities import parse_entity
        from tm_app.interface.http.branch_access_http import (
            require_transformometro_view_access,
            require_unrestricted_catalog_admin,
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
            err = require_unrestricted_catalog_admin(request)
            if err is not None:
                raise GovernedWriteError(
                    "Sem permissão de catálogo admin para esta entidade.",
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
            "confirmation_requirement": {"explicit_user_confirmation": True},
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
        conf: dict[str, Any] = {"explicit_user_confirmation": True}
        if entity == "revision" and (
            "vigencia_inicio" in data or "vigencia_fim" in data or "data" in args
        ):
            conf["confirm_vigencia_change_may_be_required"] = True
        return {
            "resource_type": entity,
            "resource_id": record_id,
            "current_state_fingerprint": fingerprint(current),
            "exact_change": exact,
            "validation_result": {"ready": True},
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
            "confirmation_requirement": {"explicit_user_confirmation": True},
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
            "confirmation_requirement": {"explicit_user_confirmation": True},
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
            "confirmation_requirement": {"explicit_user_confirmation": True},
            "expected_postcondition": {
                "type": "revision_active",
                "revisao_id": revisao_id,
            },
        }

    def _prep_recalculate(self, request: Request, args: dict[str, Any]) -> dict[str, Any]:
        self._dispatch._require_dashboard_recalculate_access(request)
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
            "confirmation_requirement": {"explicit_user_confirmation": True},
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
            "validation_result": {"ready": True},
            "consequential_impact": {
                "persists": True,
                "operation": f"meeting_workflow_{action}",
            },
            "confirmation_requirement": {"explicit_user_confirmation": True},
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
        validation = self._packages.validate(request, body)
        ready = bool(validation.get("ready"))
        # Preflight refs when ready (AuthZ-sensitive lookups)
        if ready:
            try:
                self._packages._preflight_existing_refs(request, body)
            except GptActionsError as exc:
                _raise_gpt(exc)
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
                "explicit_user_confirmation": True,
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
        conf = {"explicit_user_confirmation": True}
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
            "confirmation_requirement": {"explicit_user_confirmation": True},
            "expected_postcondition": {"type": "cost_verified_flag"},
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
        conf: dict[str, Any] = {"explicit_user_confirmation": True}
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
        if cap == "meeting_minute_manage":
            mid = change.get("minute_id")
            if mid:
                return fingerprint(
                    self._dispatch.get_record(request, "meeting_minute", str(mid))
                )
            return fingerprint({"minute_id": None})
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
        if cap == "meeting_minute_manage":
            return self._dispatch.manage_meeting_minute(
                request,
                action=str(change["action"]),
                minute_id=change.get("minute_id"),
                payload=dict(change.get("data") or {}),
            )
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
