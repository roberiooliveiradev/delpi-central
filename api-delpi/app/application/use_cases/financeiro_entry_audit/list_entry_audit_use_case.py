"""Entry-audit reads. Projects rows; does not apply fiscal rules."""

from __future__ import annotations

from app.application.dto.financeiro_entry_audit.entry_audit_query import (
    EntryAuditAccessKeyQuery,
    EntryAuditPeriodQuery,
    page_payload,
)
from app.infrastructure.persistence.totvs.financeiro_entry_audit.entry_audit_repository import (
    EntryAuditRepository,
)


class ListEntryAuditUseCase:
    def __init__(self, repository: EntryAuditRepository) -> None:
        self._repository = repository

    def documents(self, query: EntryAuditPeriodQuery) -> dict:
        rows = self._repository.fetch_documents(
            branch=query.branch,
            received_from=query.received_from,
            received_to=query.received_to,
            species=list(query.species),
            offset=query.offset,
            page_size=query.page_size,
        )
        return page_payload(rows, page=query.page, page_size=query.page_size)

    def documents_by_access_keys(self, query: EntryAuditAccessKeyQuery) -> dict:
        rows = self._repository.fetch_documents_by_access_keys(
            branch=query.branch,
            access_keys=list(query.access_keys),
        )
        page_size = max(len(rows), 1)
        return page_payload(rows, page=1, page_size=page_size)

    def items(self, query: EntryAuditPeriodQuery) -> dict:
        rows = self._repository.fetch_items(
            branch=query.branch,
            received_from=query.received_from,
            received_to=query.received_to,
            species=list(query.species),
            offset=query.offset,
            page_size=query.page_size,
        )
        return page_payload(rows, page=query.page, page_size=query.page_size)

    def fiscal_book(self, query: EntryAuditPeriodQuery) -> dict:
        rows = self._repository.fetch_fiscal_book(
            branch=query.branch,
            received_from=query.received_from,
            received_to=query.received_to,
            species=list(query.species),
            offset=query.offset,
            page_size=query.page_size,
        )
        return page_payload(rows, page=query.page, page_size=query.page_size)

    def tes(self, *, page: int, page_size: int) -> dict:
        rows = self._repository.fetch_tes(offset=(page - 1) * page_size, page_size=page_size)
        return page_payload(rows, page=page, page_size=page_size)

    def branches(self) -> dict:
        rows = self._repository.fetch_branches()
        items = []
        for row in rows:
            items.append(
                {
                    "code": row.get("code") or "",
                    "company_code": row.get("company_code") or "",
                    "name": row.get("name") or "",
                    "state": row.get("state") or "",
                    "tax_id": row.get("tax_id") or "",
                }
            )
        return {"items": items}
