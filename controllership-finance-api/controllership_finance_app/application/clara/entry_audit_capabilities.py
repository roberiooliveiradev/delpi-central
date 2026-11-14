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


def snapshot_for(capability: str, params: dict) -> dict | None:
    """Estado selável da auditoria. `None` quando a capability é de outro domínio.

    `run` ainda não tem análise: o estado ausente é válido, como em
    `invoice_posting.create`. `rerun` sela a análise. `resolve`/`reopen`
    selam o status da ocorrência pela stable_key.
    """
    if not capability.startswith("entry_audit."):
        return None
    if capability == "entry_audit.run":
        return {"analysis": {"status": "absent"}}
    service = _service()
    if capability == "entry_audit.rerun":
        ref = str(params.get("ref") or "")
        if not ref:
            return {}
        try:
            analysis = service.get_analysis(ref)
        except EntryAuditError:
            return {}
        return {"analysis": {"status": analysis.get("status"), "id": str(analysis.get("id") or ref)}}
    if capability in {"entry_audit.resolve", "entry_audit.reopen"}:
        key = str(params.get("key") or "")
        if not key:
            return {}
        return service.occurrence_state(key) or {}
    return None


def _visible_analysis(_params: dict, result: dict, _actor: str) -> bool:
    found = _service().get_analysis(str((result or {}).get("id") or ""))
    return found.get("status") in {"queued", "running", "done", "partial"}


def _visible_status(expected: str):
    def _check(params: dict, result: dict, _actor: str) -> bool:
        del result
        state = _service().occurrence_state(str(params.get("key") or "")) or {}
        return (state.get("occurrence") or {}).get("status") == expected
    return _check


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
            "postcondition": _visible_analysis,
        },
        "entry_audit.rerun": {
            "gate": "access",
            "direct": True,
            "resource_type": "entry_audit_analysis",
            "resource_key": lambda p: f"{p.get('ref')}:{p.get('branches')}",
            "required_params": ("ref",),
            "describe": lambda p: f"reexecutar a análise {p.get('ref')}",
            "execute": _exec_rerun,
            "verify": lambda p, result: (result or {}).get("status") in {"queued", "running", "done", "partial"},
            "postcondition": _visible_analysis,
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
            "postcondition": _visible_status("resolved"),
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
            "postcondition": _visible_status("pending"),
        },
    }
