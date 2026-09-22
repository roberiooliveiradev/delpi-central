"""GPT Actions façade over GovernedWriteOrchestrator (shared with MCP)."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from tm_app.application.governed_writes.errors import (
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import GovernedWriteOrchestrator
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

    def prepare_record_change(
        self,
        request: Request,
        *,
        entity: str,
        operation: str,
        record_id: str | None = None,
        changes: dict[str, Any] | None = None,
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
        return self._proposal_envelope(
            operation=f"prepare_record_change:{op}",
            public=public,
        )

    def prepare_capability(
        self,
        request: Request,
        *,
        capability: str,
        args: dict[str, Any],
        operation_label: str,
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
                    "Write flags are ignored on PREPARE; "
                    "commit uses the bound proposal only."
                ),
            }
        return envelope

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
        # Derive capability from stored proposal (opaque handle is authority).
        from tm_app.application.governed_writes.proposal_store import (
            load_valid_proposal,
        )
        from tm_app.application.governed_writes.orchestrator import _actor

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
            "warnings": [],
        }

    def _reject_server_owned_fields(self, entity: str, data: dict[str, Any]) -> None:
        owned = SERVER_OWNED_FIELDS.get(entity) or frozenset()
        if not owned:
            # Default block of common identity/audit fields
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
