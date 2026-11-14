"""Direct CLARA capabilities for entry audit. Same six tools."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

from controllership_finance_app.application.entry_audit.composer import (
    build_entry_audit_service,
)
from controllership_finance_app.application.entry_audit.errors import (
    EntryAuditError,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)


class EntryAuditCapabilityError(ChecklistDomainError):
    code = "business_rule"

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _fail(exc: EntryAuditError) -> None:
    raise EntryAuditCapabilityError(str(exc), code=exc.code) from exc


def _day(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _codes(value: Any) -> list[str] | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part) for part in value]


def _service():
    return build_entry_audit_service()


def _exec_run(params: dict, actor: str, _groups: Any) -> dict:
    try:
        return _service().create(
            date_from=_day(params["date_from"]),
            date_to=_day(params["date_to"]),
            document_types=_codes(params.get("document_types")),
            branches=_codes(params.get("branches")),
            user_id=str(actor or ""),
            user_name=str(actor or ""),
            via="clara",
        )
    except EntryAuditError as exc:
        _fail(exc)


def _exec_rerun(params: dict, actor: str, _groups: Any) -> dict:
    try:
        return _service().rerun(
            str(params["ref"]),
            _codes(params.get("branches")),
            user_id=str(actor or ""),
            user_name=str(actor or ""),
            via="clara",
        )
    except EntryAuditError as exc:
        _fail(exc)


def _exec_status(status_name: str):
    def _run(params: dict, actor: str, _groups: Any) -> dict:
        try:
            method = _service().resolve if status_name == "resolved" else _service().reopen
            return method(
                str(params["key"]),
                kind=str(params["kind"]),
                user_id=str(actor or ""),
                user_name=str(actor or ""),
            )
        except EntryAuditError as exc:
            _fail(exc)
    return _run


def build_entry_audit_capability_table(*, require: Callable[[dict, str], Any]) -> dict[str, dict]:
    del require
    return {
        "entry_audit.run": {
            "gate": "access",
            "direct": True,
            "resource_type": "entry_audit_analysis",
            "resource_key": lambda p: f"{p.get('date_from')}:{p.get('date_to')}:{p.get('branches')}:{p.get('document_types')}",
            "required_params": ("date_from", "date_to"),
            "describe": lambda p: f"auditar entradas de {p.get('date_from')} a {p.get('date_to')}",
            "execute": _exec_run,
            "verify": lambda p, result: bool((result or {}).get("id")),
            "postcondition": lambda p, result, actor: bool((result or {}).get("id")),
        },
        "entry_audit.rerun": {
            "gate": "access",
            "direct": True,
            "resource_type": "entry_audit_analysis",
            "resource_key": lambda p: f"{p.get('ref')}:{p.get('branches')}",
            "required_params": ("ref",),
            "describe": lambda p: f"reexecutar a análise {p.get('ref')}",
            "execute": _exec_rerun,
            "verify": lambda p, result: (result or {}).get("status") == "queued",
            "postcondition": lambda p, result, actor: (result or {}).get("status") == "queued",
        },
        "entry_audit.resolve": {
            "gate": "access",
            "direct": True,
            "resource_type": "entry_audit_status",
            "resource_key": lambda p: f"{p.get('kind')}:{p.get('key')}",
            "required_params": ("key", "kind"),
            "describe": lambda p: "marcar a ocorrência como resolvida",
            "execute": _exec_status("resolved"),
            "verify": lambda p, result: (result or {}).get("status") == "resolved",
            "postcondition": lambda p, result, actor: (result or {}).get("status") == "resolved",
        },
        "entry_audit.reopen": {
            "gate": "access",
            "direct": True,
            "resource_type": "entry_audit_status",
            "resource_key": lambda p: f"reopen:{p.get('kind')}:{p.get('key')}",
            "required_params": ("key", "kind"),
            "describe": lambda p: "reabrir a ocorrência",
            "execute": _exec_status("pending"),
            "verify": lambda p, result: (result or {}).get("status") == "pending",
            "postcondition": lambda p, result, actor: (result or {}).get("status") == "pending",
        },
    }
