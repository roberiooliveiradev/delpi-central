"""Composer for the entry-audit Protheus reads."""

from __future__ import annotations

from app.application.use_cases.financeiro_entry_audit.list_entry_audit_use_case import (
    ListEntryAuditUseCase,
)
from app.infrastructure.persistence.totvs.financeiro_entry_audit.entry_audit_repository import (
    EntryAuditRepository,
)


def build_list_entry_audit_use_case() -> ListEntryAuditUseCase:
    return ListEntryAuditUseCase(repository=EntryAuditRepository())
