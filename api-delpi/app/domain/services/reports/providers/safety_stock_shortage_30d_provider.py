"""Provider — rupturas projetadas nos próximos N dias (estoque de segurança)."""

from __future__ import annotations

import html
from typing import Any, Mapping, Protocol

from app.domain.services.reports.report_email_brand_layout_service import (
    ReportEmailBrandLayoutService,
)
from app.domain.services.reports.report_types import (
    EmailPayload,
    ReportAttachment,
    ReportDataset,
)
from app.domain.services.reports.safety_stock_shortage_30d_rules import (
    COLUMN_LABELS_PT,
    DATASET_COLUMNS,
    DEFAULT_HORIZON_DAYS,
    EMAIL_COLUMNS,
    EMAIL_COLUMN_STYLES,
    PROVIDER_KEY,
    format_branch_label,
    format_date_br,
    format_quantity_with_unit,
)

_TITLE = "Rupturas de estoque nos próximos {horizon} dias"


class _ShortageAggregationPort(Protocol):
    def collect_rows(
        self,
        *,
        branch: str,
        horizon_days: int = ...,
        include_blocked: bool = ...,
        product_group: str | None = ...,
        unit: str | None = ...,
        search: str | None = ...,
        include_without_safety_stock: bool = ...,
        as_of_date: Any = ...,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        ...


class SafetyStockShortage30dProvider:
    """ReportProviderPort — collect + render_email tabular pt-BR."""

    def __init__(
        self,
        aggregation: _ShortageAggregationPort,
        *,
        logo_attachment: ReportAttachment | None = None,
    ) -> None:
        self._aggregation = aggregation
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
                    "description": "Filial Protheus",
                },
                "horizonDays": {
                    "type": "integer",
                    "default": DEFAULT_HORIZON_DAYS,
                    "minimum": 1,
                    "maximum": 365,
                },
                "includeBlocked": {"type": "boolean", "default": False},
                "productGroup": {"type": "string"},
                "unit": {"type": "string"},
                "search": {"type": "string"},
                "includeWithoutSafetyStock": {"type": "boolean", "default": True},
            },
        }

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        del context  # reserved for future run context
        branch = str(params.get("branch") or "").strip()
        horizon_raw = params.get("horizonDays", DEFAULT_HORIZON_DAYS)
        try:
            horizon_days = int(horizon_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("horizonDays inválido.") from exc

        include_blocked = bool(params.get("includeBlocked", False))
        include_without = bool(params.get("includeWithoutSafetyStock", True))
        product_group = _optional_str(params.get("productGroup"))
        unit = _optional_str(params.get("unit"))
        search = _optional_str(params.get("search"))

        rows, meta = self._aggregation.collect_rows(
            branch=branch,
            horizon_days=horizon_days,
            include_blocked=include_blocked,
            product_group=product_group,
            unit=unit,
            search=search,
            include_without_safety_stock=include_without,
        )
        title = _TITLE.format(horizon=horizon_days)
        return ReportDataset(
            provider_key=self.key,
            title=title,
            columns=DATASET_COLUMNS,
            rows=tuple(rows),
            meta=meta,
        )

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        horizon = dataset.meta.get("horizonDays", DEFAULT_HORIZON_DAYS)
        branch_label = format_branch_label(dataset.meta.get("branch", ""))
        subject = (
            f"{dataset.title} — {branch_label}" if branch_label else dataset.title
        )
        as_of_br = format_date_br(dataset.meta.get("asOfDate", ""))
        count = dataset.row_count
        brand = ReportEmailBrandLayoutService

        if count == 0:
            body = (
                f"<p style=\"margin:0 0 12px 0;\">Nenhuma ruptura projetada nos "
                f"próximos {html.escape(str(horizon))} dias"
                f"{f' ({html.escape(branch_label)})' if branch_label else ''}.</p>"
            )
            if as_of_br:
                body += (
                    f"<p style=\"margin:0;color:#64748B;font-size:13px;\">"
                    f"Referência: {html.escape(as_of_br)}.</p>"
                )
        else:
            headers = [
                COLUMN_LABELS_PT.get(col, col) for col in EMAIL_COLUMNS
            ]
            column_styles = [
                EMAIL_COLUMN_STYLES.get(col, "") for col in EMAIL_COLUMNS
            ]
            table_rows = [
                [_format_cell(col, row.get(col), row=row) for col in EMAIL_COLUMNS]
                for row in dataset.rows
            ]
            intro = (
                f"<p style=\"margin:0 0 8px 0;\">{html.escape(dataset.title)}"
                f"{f' — {html.escape(branch_label)}' if branch_label else ''}."
                f" Total: <strong>{count}</strong> item(ns).</p>"
            )
            if as_of_br:
                intro += (
                    f"<p style=\"margin:0 0 16px 0;color:#64748B;font-size:13px;\">"
                    f"Referência: {html.escape(as_of_br)}.</p>"
                )
            else:
                intro += "<div style=\"height:8px;\"></div>"
            next_purchase_idx = EMAIL_COLUMNS.index("next_purchase")
            body = intro + brand.data_table_html(
                headers=headers,
                rows=table_rows,
                column_styles=column_styles,
                raw_html_columns=frozenset({next_purchase_idx}),
            )

        subtitle_parts: list[str] = []
        if branch_label:
            subtitle_parts.append(branch_label)
        if as_of_br:
            subtitle_parts.append(f"Referência {as_of_br}")
        subtitle = " · ".join(subtitle_parts) or None

        html_body = brand.wrap(
            title=dataset.title,
            subtitle=subtitle,
            body_html=body,
        )
        attachments: tuple[ReportAttachment, ...] = ()
        if self._logo_attachment is not None:
            attachments = (self._logo_attachment,)
        return EmailPayload(
            subject=subject,
            html_body=html_body,
            attachments=attachments,
        )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _format_cell(
    column: str,
    value: Any,
    *,
    row: Mapping[str, Any] | None = None,
) -> str:
    unit = (row or {}).get("unit")
    if column == "first_shortage_date":
        return format_date_br(value)
    if column in {"available_stock", "shortage_balance"}:
        return format_quantity_with_unit(value, unit)
    if column == "next_purchase":
        return _format_next_purchase_html(value)
    if column == "observation":
        return str(value or "").strip()
    if value is None:
        return ""
    if isinstance(value, float):
        return format_quantity_with_unit(value, None)
    return str(value)


def _format_next_purchase_html(value: Any) -> str:
    """Pedido — fornecedor — entrega — qtd em bloco tipográfico (Outlook-safe)."""
    text = str(value or "").strip()
    if not text:
        return (
            f'<span style="color:{_OBS_MUTED};font-size:11px;">'
            f"{html.escape('—')}</span>"
        )

    primary, _, warning_tail = text.partition(" | ")
    parts = [part.strip() for part in primary.split(" — ") if part.strip()]
    if not parts:
        parts = [primary]

    blocks: list[str] = [
        f'<div style="font-weight:700;color:{_OBS_TITLE};line-height:1.35;'
        f'text-align:center;">{html.escape(parts[0])}</div>'
    ]
    if len(parts) > 1:
        blocks.append(
            f'<div style="color:{_OBS_MUTED};font-size:11px;line-height:1.35;'
            f'margin-top:2px;text-align:center;">{html.escape(parts[1])}</div>'
        )
    if len(parts) > 2:
        blocks.append(
            f'<div style="color:{_OBS_ACCENT};font-size:11px;line-height:1.35;'
            f'margin-top:2px;white-space:nowrap;text-align:center;">'
            f"{html.escape(parts[2])}</div>"
        )
    if len(parts) > 3:
        blocks.append(
            f'<div style="color:{_OBS_TITLE};font-size:11px;font-weight:600;'
            f'line-height:1.35;margin-top:2px;white-space:nowrap;text-align:center;">'
            f"{html.escape(parts[3])}</div>"
        )
    for extra in parts[4:]:
        blocks.append(
            f'<div style="color:{_OBS_MUTED};font-size:11px;line-height:1.35;'
            f'margin-top:2px;text-align:center;">{html.escape(extra)}</div>'
        )
    if warning_tail.strip():
        blocks.append(
            f'<div style="color:{_OBS_WARN};font-size:10px;line-height:1.35;'
            f'margin-top:4px;text-align:center;">'
            f"{html.escape(warning_tail.strip())}</div>"
        )
    return "".join(blocks)


_OBS_TITLE = "#013866"
_OBS_MUTED = "#64748B"
_OBS_ACCENT = "#015488"
_OBS_WARN = "#B45309"
