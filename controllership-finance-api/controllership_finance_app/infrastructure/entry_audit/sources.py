"""Leituras da api-delpi, da financial-api e do LNF. O worker usa o bearer do pedido."""

from __future__ import annotations

import logging

from psycopg.rows import dict_row

from controllership_finance_app.application.entry_audit.request_bearer import current_bearer
from controllership_finance_app.infrastructure.api_delpi_gateway import ApiDelpiSettlementsGateway
from controllership_finance_app.infrastructure.invoice_posting.financial_received_invoice_gateway import (
    FinancialReceivedInvoiceGateway,
    FinancialReceivedInvoiceGatewayError,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_configured,
    plugins_db_connect,
)

logger = logging.getLogger("controllership_finance.entry_audit.sources")


class DelegatedSessionExpired(RuntimeError):
    """O processo reiniciou e o bearer do pedido não está mais em memória."""


class ProtheusEntriesGateway:
    def __init__(self, gateway: ApiDelpiSettlementsGateway | None = None) -> None:
        self._gateway = gateway or ApiDelpiSettlementsGateway()

    def documents(self, *, branch, received_from, received_to, species):
        return self._collect("/financeiro/entry-audit/documents", branch, received_from, received_to, species)

    def items(self, *, branch, received_from, received_to, species):
        return self._collect("/financeiro/entry-audit/items", branch, received_from, received_to, species)

    def fiscal_book(self, *, branch, received_from, received_to, species):
        return self._collect("/financeiro/entry-audit/fiscal-book", branch, received_from, received_to, species)

    def tes(self):
        return self._collect("/financeiro/entry-audit/tes", None, None, None, None)

    def branches(self):
        payload = self._get("/financeiro/entry-audit/branches", {})
        data = payload.get("data") if isinstance(payload, dict) else None
        return list((data or {}).get("items") or [])

    def _collect(self, path, branch, received_from, received_to, species):
        page = 1
        rows = []
        while page < 50:
            params = {"page": page, "page_size": 200}
            if branch:
                params.update({
                    "branch": branch,
                    "received_from": received_from.isoformat(),
                    "received_to": received_to.isoformat(),
                    "species": species,
                })
            payload = self._get(path, params)
            data = payload.get("data") if isinstance(payload, dict) else {}
            chunk = list((data or {}).get("items") or [])
            rows.extend(chunk)
            if not chunk or page >= int((data or {}).get("total_pages") or page):
                break
            page += 1
        return rows

    def _get(self, path, params):
        token = current_bearer.get()
        if not token:
            raise DelegatedSessionExpired()
        return self._gateway.get(path, access_token=token, params=params)


class FiscalXmlGateway:
    def __init__(self, gateway: FinancialReceivedInvoiceGateway | None = None) -> None:
        self._gateway = gateway or FinancialReceivedInvoiceGateway()

    def download_by_key(self, *, branch, access_key, document_type):
        try:
            return self._gateway.download_xml_by_key(
                authorization=self._authorization(),
                access_key=access_key,
                branch=branch,
                document_type=document_type,
            )
        except (DelegatedSessionExpired, FinancialReceivedInvoiceGatewayError):
            logger.warning("entry_audit_xml_download_failed")
            if not current_bearer.get():
                raise DelegatedSessionExpired()
            return None

    def list_issued(self, *, branch, document_type, issued_from, issued_to):
        keys = []
        page = 1
        while page < 50:
            try:
                data = self._gateway.export_received_documents(
                    authorization=self._authorization(),
                    branch=branch,
                    document_type=document_type,
                    issued_from=issued_from.isoformat(),
                    issued_to=issued_to.isoformat(),
                    page=page,
                    page_size=200,
                )
            except (DelegatedSessionExpired, FinancialReceivedInvoiceGatewayError):
                logger.warning("entry_audit_xml_list_failed")
                if not current_bearer.get():
                    raise DelegatedSessionExpired()
                break
            items = data.get("items") or []
            keys.extend(str(item.get("access_key") or "") for item in items if item.get("access_key"))
            if data.get("complete", True) or not items:
                break
            page += 1
        return keys

    def _authorization(self) -> str:
        token = current_bearer.get()
        if not token:
            raise DelegatedSessionExpired()
        return f"Bearer {token}"


class InvoicePostingLookup:
    def find_open(self, *, branch, access_key, document_number, series, supplier_code):
        if not plugins_db_configured():
            return None
        try:
            with plugins_db_connect() as connection:
                connection.row_factory = dict_row
                if access_key:
                    row = connection.execute(
                        """
                        SELECT r.id::text AS request_id, r.status
                          FROM lancamento_notas_fiscais.invoice_posting_danfe_attachments a
                          JOIN lancamento_notas_fiscais.invoice_posting_requests r ON r.id = a.request_id
                         WHERE a.access_key = %s
                           AND r.branch_code = %s
                           AND r.status IN ('pending', 'in_progress', 'blocked')
                         LIMIT 1
                        """,
                        (access_key, branch),
                    ).fetchone()
                    if row:
                        return {"request_id": row["request_id"], "status": row["status"]}
                row = connection.execute(
                    """
                    SELECT id::text AS request_id, status
                      FROM lancamento_notas_fiscais.invoice_posting_requests
                     WHERE branch_code = %s
                       AND document_number = %s
                       AND (%s = '' OR series = %s)
                       AND (%s = '' OR supplier_code = %s)
                       AND status IN ('pending', 'in_progress', 'blocked')
                     LIMIT 1
                    """,
                    (branch, document_number, series, series, supplier_code, supplier_code),
                ).fetchone()
        except Exception:
            logger.warning("entry_audit_lnf_lookup_failed")
            return None
        if not row:
            return None
        return {"request_id": row["request_id"], "status": row["status"]}
