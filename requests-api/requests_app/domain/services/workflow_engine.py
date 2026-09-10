from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from requests_app.domain.entities import (
    Actor,
    AssignmentEntry,
    Request,
    StatusHistoryEntry,
    TransitionResult,
)
from requests_app.domain.exceptions import WorkflowEngineError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _actor_flag(actor: Actor, permission: str) -> bool:
    key = permission.strip().replace("-", "_")
    if key in {"view_all", "viewall"}:
        return actor.has_view_all
    attr = f"has_{key}"
    return bool(getattr(actor, attr, False))


def _is_owner(request: Request, actor: Actor) -> bool:
    return request.created_by_user_id == actor.user_id


def _matches_clause(
    *,
    request: Request,
    actor: Actor,
    clause: dict[str, Any],
    status: str,
) -> bool:
    from_statuses = clause.get("from")
    if isinstance(from_statuses, list) and from_statuses and status not in from_statuses:
        return False

    if clause.get("ownership") and not _is_owner(request, actor):
        return False

    ownership_or = clause.get("ownershipOr")
    if isinstance(ownership_or, list):
        if not (
            _is_owner(request, actor)
            or any(_actor_flag(actor, flag) for flag in ownership_or)
        ):
            return False

    required = clause.get("permissions")
    if isinstance(required, list) and required:
        if not all(_actor_flag(actor, flag) for flag in required):
            return False

    any_required = clause.get("permissionsAny")
    if isinstance(any_required, list) and any_required:
        if not any(_actor_flag(actor, flag) for flag in any_required):
            return False

    return True


def _matches_requires(
    *,
    request: Request,
    actor: Actor,
    requires: dict[str, Any] | None,
    status: str,
) -> bool:
    if not requires:
        return True

    any_of = requires.get("anyOf")
    if isinstance(any_of, list) and any_of:
        return any(
            _matches_clause(
                request=request,
                actor=actor,
                clause=item if isinstance(item, dict) else {},
                status=status,
            )
            for item in any_of
        )

    return _matches_clause(
        request=request,
        actor=actor,
        clause=requires,
        status=status,
    )


def _artifact_kinds(artifacts: list[dict[str, Any]] | None) -> list[str]:
    kinds: list[str] = []
    for item in artifacts or []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("artifact_kind") or item.get("kind") or "").strip()
        if kind:
            kinds.append(kind)
    return kinds


def _matches_artifacts(
    requires: dict[str, Any] | None,
    artifacts: list[dict[str, Any]] | None,
) -> bool:
    if not isinstance(requires, dict):
        return True
    spec = requires.get("artifacts")
    if not isinstance(spec, dict):
        return True
    try:
        min_count = int(spec.get("minCount") or 1)
    except (TypeError, ValueError):
        min_count = 1
    if min_count < 1:
        min_count = 1
    kinds = _artifact_kinds(artifacts)
    kinds_any = spec.get("kindsAny")
    if isinstance(kinds_any, list) and kinds_any:
        allowed = {str(item).strip() for item in kinds_any if str(item).strip()}
        matching = [kind for kind in kinds if kind in allowed]
        return len(matching) >= min_count
    return len(kinds) >= min_count


def _required_fields(transition: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    top = transition.get("fields")
    if isinstance(top, list):
        fields.extend(str(item) for item in top)
    requires = transition.get("requires") or {}
    nested = requires.get("fields") if isinstance(requires, dict) else None
    if isinstance(nested, list):
        fields.extend(str(item) for item in nested)
    # preserve order, unique
    seen: set[str] = set()
    ordered: list[str] = []
    for name in fields:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _field_value(body: dict[str, Any] | None, field_name: str) -> str | None:
    if not body:
        return None
    raw = body.get(field_name)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


class WorkflowEngine:
    """Declarative state machine — no request_type branching."""

    def resolve_transition(
        self,
        workflow: dict[str, Any],
        action: str,
    ) -> dict[str, Any] | None:
        needle = (action or "").strip()
        if not needle:
            return None
        for transition in workflow.get("transitions") or []:
            if not isinstance(transition, dict):
                continue
            if transition.get("action") == needle:
                return transition
            if transition.get("actionAlias") == needle:
                return transition
        return None

    def terminal_statuses(self, workflow: dict[str, Any]) -> set[str]:
        raw = workflow.get("terminalStatuses") or []
        return {str(item) for item in raw}

    def can_transition(
        self,
        *,
        request: Request,
        actor: Actor,
        workflow: dict[str, Any],
        action: str,
        body: dict[str, Any] | None = None,
        require_fields: bool = True,
        expected_version: int | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> tuple[bool, str | None, str | None]:
        """
        Returns (ok, error_code, missing_field).
        """
        if expected_version is not None and request.version != expected_version:
            return False, "stale_version", None

        transition = self.resolve_transition(workflow, action)
        if transition is None:
            return False, "invalid_transition", None

        status = request.status
        if status in self.terminal_statuses(workflow):
            return False, "invalid_transition", None

        from_statuses = transition.get("from") or []
        if status not in from_statuses:
            return False, "invalid_transition", None

        requires = transition.get("requires") if isinstance(transition.get("requires"), dict) else {}
        if not _matches_requires(
            request=request,
            actor=actor,
            requires=requires,
            status=status,
        ):
            return False, "forbidden", None

        if not _matches_artifacts(requires, artifacts):
            return False, "artifact_required", "invoice_pdf"

        if require_fields:
            for field_name in _required_fields(transition):
                if _field_value(body, field_name) is None:
                    return False, "missing_field", field_name

        return True, None, None

    def compute_allowed_actions(
        self,
        *,
        request: Request,
        actor: Actor,
        workflow: dict[str, Any],
        artifacts: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        actions: list[str] = []
        status = request.status
        terminals = self.terminal_statuses(workflow)

        for computed in workflow.get("computedActions") or []:
            if not isinstance(computed, dict):
                continue
            action = str(computed.get("action") or "").strip()
            if not action:
                continue
            when_status = computed.get("whenStatus")
            if isinstance(when_status, list) and when_status and status not in when_status:
                continue
            if status in terminals and action != "view":
                continue
            requires = computed.get("requires") if isinstance(computed.get("requires"), dict) else {}
            if _matches_requires(
                request=request,
                actor=actor,
                requires=requires,
                status=status,
            ):
                actions.append(action)

        if status in terminals:
            return actions

        for transition in workflow.get("transitions") or []:
            if not isinstance(transition, dict):
                continue
            action = str(transition.get("action") or "").strip()
            if not action:
                continue
            ok, _, _ = self.can_transition(
                request=request,
                actor=actor,
                workflow=workflow,
                action=action,
                body=None,
                require_fields=False,
                artifacts=artifacts,
            )
            if ok:
                # Prefer actionAlias for UI when present (avoid Concluir + Registrar emissão).
                alias = transition.get("actionAlias")
                if isinstance(alias, str) and alias.strip():
                    actions.append(alias.strip())
                else:
                    actions.append(action)

        # unique preserve order
        seen: set[str] = set()
        ordered: list[str] = []
        for item in actions:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered

    def apply_transition(
        self,
        *,
        request: Request,
        actor: Actor,
        workflow: dict[str, Any],
        action: str,
        body: dict[str, Any] | None = None,
        expected_version: int | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> TransitionResult:
        ok, error_code, missing_field = self.can_transition(
            request=request,
            actor=actor,
            workflow=workflow,
            action=action,
            body=body,
            require_fields=True,
            expected_version=expected_version,
            artifacts=artifacts,
        )
        if not ok:
            raise WorkflowEngineError(
                code=error_code or "invalid_transition",
                field=missing_field,
                status_code=409 if error_code == "stale_version" else (
                    422 if error_code == "artifact_required" else (
                        403 if error_code == "forbidden" else 409
                    )
                ),
            )

        transition = self.resolve_transition(workflow, action)
        assert transition is not None

        canonical_action = str(transition.get("action"))
        from_status = request.status
        to_status = str(transition["to"])
        now = _utcnow()

        updated = deepcopy(request)
        updated.status = to_status
        updated.version = request.version + 1
        updated.updated_at = now

        justification = None
        for field_name in _required_fields(transition):
            value = _field_value(body, field_name)
            if field_name == "return_reason":
                updated.return_reason = value
                justification = value
            elif field_name == "cancel_justification":
                updated.cancel_justification = value
                justification = value

        from requests_app.domain.services.correction_targets import (
            normalize_correction_targets,
        )

        history_changes: dict[str, Any] = {"action_requested": action}
        if canonical_action == "return":
            targets = normalize_correction_targets(
                (body or {}).get("correction_targets"),
                type_code=request.type_code,
            )
            updated.correction_targets = targets
            if targets:
                history_changes["correction_targets"] = targets

        if to_status in self.terminal_statuses(workflow):
            if to_status == "cancelled":
                updated.cancelled_at = now
            else:
                updated.completed_at = now

        if to_status == "submitted":
            updated.return_reason = None
            updated.correction_targets = []

        # Fresh confirmation cycle: clear previous rework reason after re-issue.
        if to_status == "awaiting_requester_confirmation":
            updated.return_reason = None
            updated.correction_targets = []

        assignment: AssignmentEntry | None = None
        if transition.get("assignSelf"):
            assignment = AssignmentEntry(
                role="processor",
                assignee_user_id=actor.user_id,
            )

        history = StatusHistoryEntry(
            from_status=from_status,
            to_status=to_status,
            action=canonical_action,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            justification=justification,
            changes=history_changes,
        )

        events = [
            {
                "event_type": "transition",
                "action": canonical_action,
                "from_status": from_status,
                "to_status": to_status,
                "request_id": str(updated.id),
                "request_version": updated.version,
            }
        ]

        return TransitionResult(
            request=updated,
            history=history,
            assignment=assignment,
            domain_events=events,
        )
