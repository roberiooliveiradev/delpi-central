from __future__ import annotations

from typing import Any, Callable

from tm_app.application.security.authorization_policy import TransformometroAuthorizationPolicy
from tm_app.application.use_cases.manage_transformometro_tasks import TaskCommandUseCases
from tm_app.domain.entities.transformometro_task import TransformometroTask
from tm_app.domain.services.transformometro_task_rules import is_due_soon, is_overdue, today_in_portal

STATUS_LABELS = {
    "pending": "Pendente",
    "completed": "Concluída",
    "cancelled": "Cancelada",
}


class ListMyTaskItemsUseCase:
    def __init__(
        self,
        commands: TaskCommandUseCases,
        pending_signatures: Callable[[Any], dict[str, Any]],
        policy: TransformometroAuthorizationPolicy | None = None,
    ) -> None:
        self._commands = commands
        self._pending_signatures = pending_signatures
        self._policy = policy or TransformometroAuthorizationPolicy()

    def execute(self, user: Any, *, status: str = "pending") -> dict[str, Any]:
        self._policy.require_access(user)
        tasks = self._commands.list_mine(user, status=status)
        signatures: list[dict[str, Any]] = []
        partial_error = None
        if status in {"pending", "all"}:
            try:
                payload = self._pending_signatures(user) or {}
                signatures = list(payload.get("items") or [])
            except Exception as exc:
                partial_error = str(exc) or "Não foi possível carregar as assinaturas pendentes."
        today = today_in_portal()
        items = [self._manual_item(task, today) for task in tasks]
        if status in {"pending", "all"}:
            items.extend(self._signature_item(item) for item in signatures)
        items.sort(key=self._sort_key)
        pending_count = sum(1 for item in items if item["status"] == "pending")
        overdue = sum(1 for item in items if item.get("overdue"))
        due_soon = sum(
            1
            for task in tasks
            if is_due_soon(task.status, task.due_date, today)
        )
        return {
            "items": items,
            "summary": {
                "pending": pending_count,
                "due_soon": due_soon,
                "overdue": overdue,
            },
            "partial_error": partial_error,
        }

    @staticmethod
    def _manual_item(task: TransformometroTask, today) -> dict[str, Any]:
        overdue = is_overdue(task.status, task.due_date, today)
        return {
            "id": f"task:{task.id}",
            "type": "manual_task",
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "status_label": STATUS_LABELS[task.status],
            "source_label": "Tarefa",
            "source_id": task.id,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "due_date_label": task.due_date.strftime("%d/%m/%Y") if task.due_date else None,
            "overdue": overdue,
            "assignee_user_id": task.assignee_user_id,
            "context_label": None,
            "route": None,
            "actions": {
                "can_open": False,
                "can_edit": task.status == "pending",
                "can_complete": task.status == "pending",
                "can_cancel": task.status == "pending",
            },
        }

    @staticmethod
    def _signature_item(item: dict[str, Any]) -> dict[str, Any]:
        source_id = str(item.get("id") or "")
        number = str(item.get("minute_number") or "").strip()
        unit = str(item.get("unit_code") or "").strip()
        origin = f"Ata #{number}" if number else "Ata"
        return {
            "id": f"meeting_minute_signature:{source_id}",
            "type": "meeting_minute_signature",
            "title": "Assinar ata",
            "description": str(item.get("title") or "").strip() or number or None,
            "status": "pending",
            "status_label": "Pendente",
            "source_label": origin,
            "source_id": source_id,
            "due_date": None,
            "due_date_label": None,
            "overdue": False,
            "assignee_user_id": None,
            "context_label": f"Unidade {unit}" if unit else None,
            "route": f"/apps/transformometro/meeting-minutes/{source_id}",
            "actions": {
                "can_open": True,
                "can_edit": False,
                "can_complete": False,
                "can_cancel": False,
            },
        }

    @staticmethod
    def _sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
        if item.get("overdue"):
            bucket = 0
        elif item.get("due_date"):
            bucket = 1
        elif item.get("type") == "manual_task":
            bucket = 2
        else:
            bucket = 3
        return (bucket, item.get("due_date") or "9999-99-99", item.get("title") or "")
