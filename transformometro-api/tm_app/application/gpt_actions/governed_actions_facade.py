"""GPT Actions façade over GovernedWriteOrchestrator (shared with MCP)."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from tm_app.application.governed_writes.confirmation_policy import (
    allows_commit_now_for_capability,
    allows_commit_now_for_entity_operation,
)
from tm_app.application.governed_writes.errors import (
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.idempotency_store import (
    get_cached,
    put_cached,
)
from tm_app.application.governed_writes.orchestrator import (
    GovernedWriteOrchestrator,
    _actor,
)
from tm_app.application.gpt_actions.capability_descriptors import (
    OPERATION_TO_CAPABILITY,
    RECORD_OPERATIONS,
    SERVER_OWNED_FIELDS,
)
from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tm_app.application.gpt_actions.entities import entity_supports, parse_entity
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)


class GovernedActionsFacade:
    """Maps GPT Action HTTP bodies → shared PREPARE/ACT orchestrator."""

    def __init__(
        self,
        orchestrator: GovernedWriteOrchestrator | None = None,
        dispatch: GptActionsDispatchService | None = None,
    ) -> None:
        self._dispatch = dispatch or GptActionsDispatchService()
        self._packages = GuidedImprovementPackageService(self._dispatch)
        self._orchestrator = orchestrator or GovernedWriteOrchestrator(
            self._dispatch, self._packages
        )

    @property
    def orchestrator(self) -> GovernedWriteOrchestrator:
        return self._orchestrator

    def prepare_record_change(
        self,
        request: Request,
        *,
        entity: str,
        operation: str,
        record_id: str | None = None,
        changes: dict[str, Any] | None = None,
        commit_now: bool = False,
        confirmation: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        op = str(operation or "").strip().lower()
        if op not in RECORD_OPERATIONS:
            raise GovernedWriteError(
                f"Invalid operation '{operation}'. Allowed: {sorted(RECORD_OPERATIONS)}.",
                code=VALIDATION,
                status_code=400,
            )
        parsed = parse_entity(entity)
        cap_name = {
            "create": "create",
            "update": "update",
            "delete": "delete",
            "duplicate": "duplicate",
        }[op]
        if not entity_supports(parsed, cap_name):
            raise GovernedWriteError(
                f"Entity '{entity}' does not support operation '{op}'.",
                code=VALIDATION,
                status_code=400,
            )
        data = dict(changes or {})
        self._reject_server_owned_fields(entity, data)
        capability = OPERATION_TO_CAPABILITY[op]
        args: dict[str, Any] = {"entity": entity, "data": data}
        if op != "create":
            rid = str(record_id or "").strip()
            if not rid:
                raise GovernedWriteError(
                    "record_id is required for update/delete/duplicate.",
                    code=VALIDATION,
                    status_code=400,
                )
            args["id"] = rid
        public = self._orchestrator.prepare(
            request, capability=capability, args=args
        )
        envelope = self._proposal_envelope(
            operation=f"prepare_record_change:{op}",
            public=public,
        )
        return self._maybe_commit_now(
            request,
            envelope=envelope,
            capability=capability,
            public=public,
            commit_now=commit_now,
            confirmation=confirmation,
            idempotency_key=idempotency_key,
            policy_allows=allows_commit_now_for_entity_operation(op),
        )

    def prepare_capability(
        self,
        request: Request,
        *,
        capability: str,
        args: dict[str, Any],
        operation_label: str,
        commit_now: bool = False,
        confirmation: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        public = self._orchestrator.prepare(
            request, capability=capability, args=args
        )
        envelope = self._proposal_envelope(operation=operation_label, public=public)
        # Flatten validation fields for GPT readability (package PREPARE = dry-run).
        vr = envelope.get("validation_result")
        if isinstance(vr, dict) and "ready" in vr:
            envelope["ready"] = bool(vr.get("ready"))
            envelope["missing"] = list(vr.get("missing") or [])
            if "checklist" in vr:
                envelope["checklist"] = vr.get("checklist")
            envelope["dry_run"] = True
            envelope["hints"] = {
                "activate_scenario": False,
                "recalculate": False,
                "note": (
                    "Write flags are ignored on PREPARE-only; "
                    "commit_now=true may ACT when policy allows and ready=true."
                ),
            }
        return self._maybe_commit_now(
            request,
            envelope=envelope,
            capability=capability,
            public=public,
            commit_now=commit_now,
            confirmation=confirmation,
            idempotency_key=idempotency_key,
            policy_allows=allows_commit_now_for_capability(capability),
        )

    def commit_proposal(
        self,
        request: Request,
        *,
        proposal_handle: str,
        confirmation: bool,
    ) -> dict[str, Any]:
        if not confirmation:
            raise GovernedWriteError(
                "confirmation=true is required to commit a proposal. "
                "Conversational confirmation is not AuthZ; backend still revalidates.",
                code=VALIDATION,
                status_code=400,
                data={"error_code": "CONFIRMATION_REQUIRED"},
            )
        from tm_app.application.governed_writes.proposal_store import (
            load_valid_proposal,
        )

        actor_id, _email = _actor(request)
        proposal = load_valid_proposal(
            proposal_handle=proposal_handle,
            actor_id=actor_id,
            expected_capability=None,
        )
        result = self._orchestrator.act(
            request,
            capability=proposal.capability,
            proposal_handle=proposal_handle,
        )
        return {
            "status": "ok",
            "operation": "commit_proposal",
            "capability": result.get("capability"),
            "proposal_id": result.get("proposal_id"),
            "data": result.get("data"),
            "read_back": result.get("data"),
            "postcondition": {"verified": bool(result.get("verified"))},
            "persisted": True,
            "warnings": [],
        }

    def _maybe_commit_now(
        self,
        request: Request,
        *,
        envelope: dict[str, Any],
        capability: str,
        public: dict[str, Any],
        commit_now: bool,
        confirmation: bool,
        idempotency_key: str | None,
        policy_allows: bool,
    ) -> dict[str, Any]:
        envelope = dict(envelope)
        envelope["persisted"] = False
        envelope["commit_now_applied"] = False
        if not commit_now:
            return envelope

        if not policy_allows:
            envelope["message"] = (
                "commit_now ignored: this capability requires explicit "
                "user confirmation and a separate commit_proposal."
            )
            return envelope

        if not public.get("act_allowed", True) or not public.get("ready", True):
            envelope["message"] = (
                "commit_now ignored: proposal is not ready for ACT "
                "(see validation_result)."
            )
            return envelope

        if not confirmation:
            raise GovernedWriteError(
                "commit_now=true requires confirmation=true "
                "(policy additive). Nothing was persisted.",
                code=VALIDATION,
                status_code=400,
                data={"error_code": "CONFIRMATION_REQUIRED"},
            )

        key = str(idempotency_key or "").strip()
        if not key:
            raise GovernedWriteError(
                "commit_now=true requires Idempotency-Key header or "
                "idempotency_key in the body.",
                code=VALIDATION,
                status_code=422,
                data={"error_code": "IDEMPOTENCY_KEY_REQUIRED"},
            )

        actor_id, _email = _actor(request)
        cached = get_cached(actor_id, key)
        if cached is not None:
            return cached

        handle = str(public.get("proposal_handle") or "").strip()
        result = self._orchestrator.act(
            request,
            capability=capability,
            proposal_handle=handle,
        )
        outcome = {
            **envelope,
            "status": "ok",
            "persisted": True,
            "commit_now_applied": True,
            "capability": result.get("capability"),
            "proposal_id": result.get("proposal_id"),
            "data": result.get("data"),
            "read_back": result.get("data"),
            "postcondition": {"verified": bool(result.get("verified"))},
        }
        put_cached(actor_id, key, outcome)
        return outcome

    def _reject_server_owned_fields(self, entity: str, data: dict[str, Any]) -> None:
        owned = SERVER_OWNED_FIELDS.get(entity) or frozenset()
        if not owned:
            owned = frozenset(
                {
                    "created_by_user_id",
                    "updated_by_user_id",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                }
            )
        bad = sorted(k for k in data.keys() if k in owned)
        if bad:
            raise GovernedWriteError(
                f"Disallowed server-owned fields: {', '.join(bad)}.",
                code=VALIDATION,
                status_code=400,
                data={"error_code": "INVALID_FIELD", "fields": bad},
            )

    @staticmethod
    def _proposal_envelope(*, operation: str, public: dict[str, Any]) -> dict[str, Any]:
        exact = public.get("exact_change") or {}
        summary_bits = [
            str(public.get("capability") or ""),
            str(public.get("resource_type") or ""),
            str(public.get("resource_id") or ""),
        ]
        summary = " · ".join(b for b in summary_bits if b)
        return {
            "status": "proposal_ready",
            "operation": operation,
            "proposal": {
                "handle": public.get("proposal_handle"),
                "proposal_id": public.get("proposal_id"),
                "capability": public.get("capability"),
                "resource_type": public.get("resource_type"),
                "resource_id": public.get("resource_id"),
                "summary": summary,
                "exact_change": exact,
                "confirmation_requirement": public.get("confirmation_requirement"),
                "expected_postcondition": public.get("expected_postcondition"),
                "expires_at": public.get("expires_at"),
                "act_allowed": public.get("act_allowed", True),
                "ready": public.get("ready", True),
            },
            "validation_result": public.get("validation_result"),
            "consequential_impact": public.get("consequential_impact"),
            "warnings": [],
            "provenance": ["governed_write_orchestrator"],
        }
