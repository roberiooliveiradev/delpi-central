"""Provider — saldos PA armazém 01 com Excel anexo (Delpi Reports)."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any, Mapping, Protocol
from zoneinfo import ZoneInfo

from app.domain.services.reports.report_email_brand_layout_service import (
    GRAY_600,
    ReportEmailBrandLayoutService,
)
from app.domain.services.reports.report_types import (
    EmailPayload,
    ReportAttachment,
    ReportDataset,
)
from app.domain.services.reports.stock_balances_pa_excel_builder import (
    StockBalancesPaExcelBuilder,
)
from app.domain.services.reports.stock_balances_pa_rules import (
    COLUMN_PRODUCT,
    COLUMN_QUANTITY,
    DATASET_COLUMNS,
    DEFAULT_TIMEZONE,
    EXCLUDED_PRODUCT_CODE_PREFIXES,
    FETCH_PAGE_SIZE,
    MAX_FETCH_PAGES,
    ONLY_POSITIVE,
    PROVIDER_DISPLAY_NAME,
    PROVIDER_KEY,
    WAREHOUSE,
    export_quantity,
    format_issue_date,
    parse_branch_param,
    prefixes_for_branch,
    product_code_in_stock_balances_scope,
    title_for_branch,
)


class _StockBalancesItemsPort(Protocol):
    def count_items(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
    ) -> int: ...

    def fetch_items(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]: ...


class StockBalancesPaProvider:
    """ReportProviderPort — collect saldos PA + e-mail com XLSX."""

    def __init__(
        self,
        repository: _StockBalancesItemsPort,
        *,
        logo_attachment: ReportAttachment | None = None,
    ) -> None:
        self._repository = repository
        self._logo_attachment = logo_attachment

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    def describe_params(self) -> Mapping[str, Any]:
        return {
            "type": "object",
            "required": ["branch"],
            "properties": {
                "branch": {
                    "type": "string",
                    "enum": ["01", "02"],
                    "description": "Filial TOTVS (01=SC matriz, 02=ES filial).",
                }
            },
        }

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        del context
        branch = parse_branch_param(params)
        prefixes = prefixes_for_branch(branch)
        raw_rows = self._fetch_all(branch=branch)
        scoped = [
            row
            for row in raw_rows
            if product_code_in_stock_balances_scope(
                str(row.get("product_code") or ""), branch=branch
            )
        ]
        scoped.sort(key=lambda row: str(row.get("product_code") or "").strip().lower())
        issued_on = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
        title = title_for_branch(branch)
        rows = [
            {
                COLUMN_PRODUCT: str(row.get("product_code") or "").strip(),
                COLUMN_QUANTITY: float(row.get("quantity") or 0),
                "export_quantity": export_quantity(row.get("quantity")),
            }
            for row in scoped
        ]
        return ReportDataset(
            provider_key=PROVIDER_KEY,
            title=title,
            columns=DATASET_COLUMNS,
            rows=rows,
            meta={
                "branch": branch,
                "warehouse": WAREHOUSE,
                "productCodePrefixes": list(prefixes),
                "excludedProductCodePrefixes": list(EXCLUDED_PRODUCT_CODE_PREFIXES),
                "issuedOn": issued_on.isoformat(),
                "issueDateBr": format_issue_date(issued_on),
                "rowCount": len(rows),
                "displayName": PROVIDER_DISPLAY_NAME,
            },
        )

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        brand = ReportEmailBrandLayoutService()
        branch = str(dataset.meta.get("branch") or "01")
        issue_br = str(dataset.meta.get("issueDateBr") or format_issue_date())
        title = dataset.title or title_for_branch(branch)
        count = int(dataset.meta.get("rowCount") or dataset.row_count)
        subject = f"Saldos em estoque — {title} | {issue_br}"

        branch_label = "SC (01)" if branch == "01" else "ES (02)"
        body = (
            f'<p style="margin:0 0 12px 0;font-size:14px;color:#1A202C;line-height:1.5;">'
            f"Segue em anexo o saldo de produtos acabados (PA) do armazém "
            f"<strong>{html.escape(WAREHOUSE)}</strong> para a filial "
            f"<strong>{html.escape(branch_label)}</strong>.</p>"
            f'<p style="margin:0 0 12px 0;font-size:14px;color:#1A202C;line-height:1.5;">'
            f"Data de emissão: <strong>{html.escape(issue_br)}</strong>. "
            f"Total de produtos: <strong>{count}</strong>.</p>"
            f'<p style="margin:0 0 8px 0;font-size:13px;color:{GRAY_600};line-height:1.45;">'
            "A planilha contém código do produto e quantidade convertida "
            "(unidade × 1000).</p>"
        )
        html_body = brand.wrap(
            title=title,
            subtitle=f"{PROVIDER_DISPLAY_NAME} · {branch_label}",
            body_html=body,
        )

        excel = StockBalancesPaExcelBuilder.build_attachment(
            dataset.rows,
            branch=branch,
            issued_on=dataset.meta.get("issuedOn"),
        )
        attachments: list[ReportAttachment] = [excel]
        if self._logo_attachment is not None:
            attachments.insert(0, self._logo_attachment)

        return EmailPayload(
            subject=subject,
            html_body=html_body,
            attachments=tuple(attachments),
        )

    def _fetch_all(self, *, branch: str) -> list[dict[str, Any]]:
        total = self._repository.count_items(
            branch=branch,
            warehouse=WAREHOUSE,
            only_positive=ONLY_POSITIVE,
        )
        collected: list[dict[str, Any]] = []
        page = 0
        while page < MAX_FETCH_PAGES:
            offset = page * FETCH_PAGE_SIZE
            if total and offset >= total:
                break
            batch = self._repository.fetch_items(
                branch=branch,
                warehouse=WAREHOUSE,
                only_positive=ONLY_POSITIVE,
                sort="product_code_asc",
                offset=offset,
                page_size=FETCH_PAGE_SIZE,
            )
            if not batch:
                break
            collected.extend(batch)
            if len(batch) < FETCH_PAGE_SIZE:
                break
            page += 1
        return collected
