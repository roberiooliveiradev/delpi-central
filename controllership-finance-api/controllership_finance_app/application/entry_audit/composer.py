"""Montagem da auditoria de entradas. Sem banco, a fila fica em memória no processo."""

from __future__ import annotations

from controllership_finance_app.application.entry_audit.service import EntryAuditService
from controllership_finance_app.config import settings
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from controllership_finance_app.infrastructure.entry_audit.memory_store import MemoryEntryAuditStore
from controllership_finance_app.infrastructure.entry_audit.sources import (
    FiscalXmlGateway,
    InvoicePostingLookup,
    ProtheusEntriesGateway,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import plugins_db_configured

_memory = MemoryEntryAuditStore()


def audit_config() -> AuditConfig:
    return AuditConfig(
        presumed_credit_tes=settings.ENTRY_AUDIT_PRESUMED_CREDIT_TES,
        freight_cfop_suffix=settings.ENTRY_AUDIT_FREIGHT_CFOP_SUFFIX,
        tolerance=float(settings.ENTRY_AUDIT_TOLERANCE),
        unmatched_grace_days=int(settings.ENTRY_AUDIT_UNMATCHED_GRACE_DAYS),
    )


def build_entry_audit_service() -> EntryAuditService:
    store = _memory
    if plugins_db_configured():
        from controllership_finance_app.infrastructure.entry_audit.postgres_store import PostgresEntryAuditStore

        store = PostgresEntryAuditStore()
    return EntryAuditService(
        store,
        ProtheusEntriesGateway(),
        FiscalXmlGateway(),
        InvoicePostingLookup(),
        audit_config(),
        lookback_days=int(settings.ENTRY_AUDIT_XML_LOOKBACK_DAYS),
    )
