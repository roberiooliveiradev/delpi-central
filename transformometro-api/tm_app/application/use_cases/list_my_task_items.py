from __future__ import annotations

from datetime import date
from typing import Any, Callable

from tm_app.application.security.authorization_policy import TransformometroAuthorizationPolicy
from tm_app.application.use_cases.manage_transformometro_tasks import TaskCommandUseCases
from tm_app.domain.entities.transformometro_task import TransformometroTask
from tm_app.domain.services.transformometro_task_rules import (
    can_cancel_task,
    can_complete_task,
    can_update_task,
    is_due_soon,
    is_overdue,
    normalize_user_id,
    today_in_portal,
)

STATUS_LABELS = {
    "pending": "Pendente",
    "completed": "Concluída",
    "cancelled": "Cancelada",
}

# Portal vocabulary (`received` / `delegated`) plus the two authorized
# views the Portal already implies by combining those tabs.
# `visible` is the personal union (assignee OR creator), never the team.
MY_TASK_SCOPES = ("received", "delegated", "created", "visible")
DEFAULT_MY_TASK_SCOPE = "received"
MY_TASK_PAGE_SIZE_MAX = 100
MY_TASK_PAGE_SIZE_WHEN_PAGING = 50
MY_TASK_QUERY_MAX = 200
_INVALID_SCOPE = (
    "Escopo de consulta inválido. Use received, delegated, created ou visible. "
    "visible é a união das tarefas em que o usuário é responsável ou criador, "
    "não todas as tarefas da organização."
)


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

    def execute(
        self,
        user: Any,
        *,
        status: str = "pending",
        scope: str = DEFAULT_MY_TASK_SCOPE,
        authorization: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        overdue: bool | None = None,
        q: str | None = None,
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        scope_norm = (scope or DEFAULT_MY_TASK_SCOPE).strip().lower()
        if scope_norm not in MY_TASK_SCOPES:
            raise ValueError(_INVALID_SCOPE)
        overdue_only = _coerce_overdue(overdue)
        page_n = _coerce_page(page, name="page")
        size_n = _coerce_page(page_size, name="page_size")
        query = _normalize_query(q)
        viewer_id = normalize_user_id(
            str(getattr(user, "id", "") or ""), field="Usuário autenticado"
        )
        is_manager = self._policy.has_manage(user)
        today = today_in_portal()
        tasks, items, partial_error = self._collect(
            user,
            status=status,
            scope=scope_norm,
            authorization=authorization,
            viewer_id=viewer_id,
            is_manager=is_manager,
            today=today,
        )
        items = [
            item
            for item in items
            if _matches(item, query=query, overdue_only=overdue_only)
        ]
        items.sort(key=self._sort_key)
        summary = _summary(items, today)
        total = len(items)
        page_items, page_out, size_out = _paginate(items, page_n, size_n)
        payload: dict[str, Any] = {
            "items": page_items,
            "total": total,
            "scope": scope_norm,
            "summary": summary,
            "partial_error": partial_error,
        }
        if page_out is not None:
            payload["page"] = page_out
            payload["page_size"] = size_out
        return payload

    def _collect(
        self,
        user: Any,
        *,
        status: str,
        scope: str,
        authorization: str | None,
        viewer_id: str,
        is_manager: bool,
        today,
    ) -> tuple[list[TransformometroTask], list[dict[str, Any]], str | None]:
        if scope == "received":
            tasks = self._commands.list_mine(user, status=status)
            items = [
                self._manual_item(task, today, viewer_id, is_manager) for task in tasks
            ]
            partial = self._append_signatures(user, status, items)
            return tasks, items, partial
        if scope == "delegated":
            tasks = self._commands.list_delegated(user, status=status)
            items = self._project_tasks(
                user,
                tasks,
                authorization=authorization,
                today=today,
                viewer_id=viewer_id,
                is_manager=is_manager,
                origin_for_all=True,
            )
            return tasks, items, None
        assigned = self._commands.list_mine(user, status=status)
        delegated = self._commands.list_delegated(user, status=status)
        if scope == "created":
            own = [task for task in assigned if task.created_by_user_id == viewer_id]
            tasks = _dedupe([*own, *delegated])
            items = self._project_tasks(
                user,
                tasks,
                authorization=authorization,
                today=today,
                viewer_id=viewer_id,
                is_manager=is_manager,
                origin_for_all=False,
            )
            return tasks, items, None
        tasks = _dedupe([*assigned, *delegated])
        items = self._project_tasks(
            user,
            tasks,
            authorization=authorization,
            today=today,
            viewer_id=viewer_id,
            is_manager=is_manager,
            origin_for_all=False,
        )
        partial = self._append_signatures(user, status, items)
        return tasks, items, partial

    def _append_signatures(
        self, user: Any, status: str, items: list[dict[str, Any]]
    ) -> str | None:
        if status not in {"pending", "all"}:
            return None
        try:
            payload = self._pending_signatures(user) or {}
            signatures = list(payload.get("items") or [])
        except Exception as exc:
            return str(exc) or "Não foi possível carregar as assinaturas pendentes."
        items.extend(self._signature_item(item) for item in signatures)
        return None

    def _project_tasks(
        self,
        user: Any,
        tasks: list[TransformometroTask],
        *,
        authorization: str | None,
        today,
        viewer_id: str,
        is_manager: bool,
        origin_for_all: bool,
    ) -> list[dict[str, Any]]:
        needs_origin = origin_for_all or any(
            task.assignee_user_id != viewer_id for task in tasks
        )
        contexts = (
            self._commands.origin_contexts(
                user, [task.id for task in tasks], authorization=authorization
            )
            if needs_origin
            else {}
        )
        items: list[dict[str, Any]] = []
        for task in tasks:
            use_origin = origin_for_all or task.assignee_user_id != viewer_id
            if use_origin:
                items.append(
                    self._delegated_item(
                        task,
                        contexts.get(task.id),
                        today,
                        viewer_id,
                        is_manager,
                    )
                )
            else:
                items.append(self._manual_item(task, today, viewer_id, is_manager))
        return items

    @staticmethod
    def _delegated_item(
        task: TransformometroTask,
        context,
        today,
        viewer_id: str,
        is_manager: bool,
    ) -> dict[str, Any]:
        item = ListMyTaskItemsUseCase._manual_item(task, today, viewer_id, is_manager)
        room_id = context.room_id if context else None
        item["context_label"] = context.context_label if context else None
        item["route"] = (
            f"/apps/transformometro/interaction-rooms/{room_id}" if room_id else None
        )
        item["created_at_label"] = (
            task.created_at.strftime("%d/%m/%Y") if task.created_at else None
        )
        item["actions"]["can_open"] = bool(room_id)
        return item

    @staticmethod
    def _manual_item(
        task: TransformometroTask,
        today,
        viewer_id: str = "",
        is_manager: bool = False,
    ) -> dict[str, Any]:
        overdue = is_overdue(task.status, task.due_date, today)
        pending = task.status == "pending"
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
            "created_by_user_id": task.created_by_user_id,
            "viewer_relation": _viewer_relation(task, viewer_id),
            "context_label": None,
            "route": None,
            "actions": {
                "can_open": False,
                "can_edit": pending and can_update_task(viewer_id, is_manager, task),
                "can_complete": pending and can_complete_task(viewer_id, is_manager, task),
                "can_cancel": pending and can_cancel_task(viewer_id, is_manager, task),
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
            "created_by_user_id": None,
            "viewer_relation": "pending_signature",
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


def _viewer_relation(task: TransformometroTask, viewer_id: str) -> str:
    is_assignee = bool(viewer_id) and task.assignee_user_id == viewer_id
    is_creator = bool(viewer_id) and task.created_by_user_id == viewer_id
    if is_assignee and is_creator:
        return "assignee_and_creator"
    if is_assignee:
        return "assignee"
    if is_creator:
        return "creator"
    return "unrelated"


def _dedupe(tasks: list[TransformometroTask]) -> list[TransformometroTask]:
    seen: set[str] = set()
    unique: list[TransformometroTask] = []
    for task in tasks:
        if task.id in seen:
            continue
        seen.add(task.id)
        unique.append(task)
    return unique


def _summary(items: list[dict[str, Any]], today: date) -> dict[str, int]:
    due_soon = 0
    for item in items:
        if item.get("type") != "manual_task":
            continue
        raw = item.get("due_date")
        due = date.fromisoformat(str(raw)) if raw else None
        if is_due_soon(item["status"], due, today):
            due_soon += 1
    return {
        "pending": sum(1 for item in items if item["status"] == "pending"),
        "due_soon": due_soon,
        "overdue": sum(1 for item in items if item.get("overdue")),
    }


def _matches(item: dict[str, Any], *, query: str, overdue_only: bool | None) -> bool:
    if overdue_only is True and not item.get("overdue"):
        return False
    if not query:
        return True
    haystack = " ".join(
        str(item.get(key) or "")
        for key in (
            "title",
            "description",
            "context_label",
            "source_label",
            "status_label",
        )
    ).casefold()
    return query.casefold() in haystack


def _normalize_query(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > MY_TASK_QUERY_MAX:
        raise ValueError("Busca textual excede o limite.")
    return text


def _coerce_overdue(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        token = value.strip().lower()
        if token in {"true", "1", "yes"}:
            return True
        if token in {"false", "0", "no"}:
            return False
    raise ValueError("Filtro overdue inválido.")


def _coerce_page(value: Any, *, name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} inválido.") from exc


def _paginate(
    items: list[dict[str, Any]], page: int | None, page_size: int | None
) -> tuple[list[dict[str, Any]], int | None, int | None]:
    if page is None and page_size is None:
        return items, None, None
    size = MY_TASK_PAGE_SIZE_WHEN_PAGING if page_size is None else page_size
    current = 1 if page is None else page
    if size < 1 or size > MY_TASK_PAGE_SIZE_MAX:
        raise ValueError("page_size inválido.")
    if current < 1:
        raise ValueError("page inválido.")
    start = (current - 1) * size
    return items[start : start + size], current, size
