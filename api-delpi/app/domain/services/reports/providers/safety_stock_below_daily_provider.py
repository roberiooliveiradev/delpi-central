"""GLPI #1178: e-mail preventivo de estoque de segurança (seg–sex)."""
from __future__ import annotations

import html
from typing import Any, Mapping, Protocol

from app.domain.services.reports.report_email_brand_layout_service import (
    ReportEmailBrandLayoutService as Layout,
)
from app.domain.services.reports.report_types import (
    EmailPayload,
    ReportAttachment,
    ReportDataset,
)
from app.domain.services.reports.safety_stock_shortage_30d_rules import (
    format_branch_label,
    format_date_br,
    format_quantity_with_unit,
)

PROVIDER_KEY = "safety_stock_below_daily"
TITLE = "Alerta diário | Materiais abaixo do estoque de segurança"
DATA_COLUMNS = (
    "branch", "product_code", "product_description", "unit",
    "available_stock", "safety_stock", "deficit_quantity",
    "eligible_open_quantity", "projected_stock_after_orders",
    "remaining_to_buy", "coverage_status", "next_expected_delivery_date",
    "open_order_count", "eligible_order_count", "purchase_orders",
    "warnings", "is_stockout",
)

_EMAIL_HEADERS = [
    "Código", "Descrição", "Saldo 01+98+99", "Estoque segurança",
    "Falta p/ segurança", "Pedido(s) de compra", "Cobertura após pedidos",
]
_EMAIL_STYLES = [
    "white-space:nowrap;width:90px;",
    "min-width:150px;width:25%;",
    "white-space:nowrap;",
    "white-space:nowrap;",
    "white-space:nowrap;",
    "min-width:220px;width:28%;",
    "min-width:150px;width:17%;",
]

_STATUS_PT = {
    "sufficient": ("Atende em quantidade", "#067647", "#ECFDF3"),
    "partial": ("Atende parcialmente", "#9A6700", "#FFFAEB"),
    "none": ("Não atende", "#B42318", "#FEF3F2"),
}


class _Aggregation(Protocol):
    def collect_rows(self, *, branch: str) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...


class SafetyStockBelowDailyProvider:
    def __init__(
        self,
        aggregation: _Aggregation,
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
            "displayName": "Alerta diário — abaixo do estoque de segurança",
            "required": ["branch"],
            "properties": {
                "branch": {
                    "type": "string",
                    "enum": ["01", "02"],
                    "description": "Uma filial por definição; não consolida filiais.",
                }
            },
            "recommendedScheduleKind": "weekdays",
            "description": (
                "Saldo SB2 (01+98+99) inferior ao ESTSEG do SBZ, "
                "com pedidos SC7 abertos e cobertura em quantidade."
            ),
        }

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        del context
        branch = str(params.get("branch") or "").strip()
        if branch not in {"01", "02"}:
            raise ValueError("Escolha a filial 01 (SC) ou 02 (ES).")
        rows, meta = self._aggregation.collect_rows(branch=branch)
        return ReportDataset(
            provider_key=self.key,
            title=TITLE,
            columns=DATA_COLUMNS,
            rows=tuple(rows),
            meta=dict(meta),
        )

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        if dataset.provider_key != self.key:
            raise ValueError("Dataset incompatível com alerta de estoque de segurança.")
        branch = str(dataset.meta.get("branch") or "").strip()
        if branch not in {"01", "02"}:
            raise ValueError("Filial ausente no relatório de estoque de segurança.")
        if any(str(row.get("branch")) != branch for row in dataset.rows):
            raise ValueError("Relatório misturou filiais; envio recusado.")

        branch_label = format_branch_label(branch)
        as_of = format_date_br(dataset.meta.get("asOfDate")) or "data não informada"
        subject = f"Minha Delpi | Estoque abaixo da segurança | {branch_label} | {as_of}"
        summary = _summary_html(dataset)
        intro = (
            '<p style="margin:0 0 14px;color:#475467;font-size:13px;">'
            "Alerta preventivo por filial. O saldo considera exclusivamente "
            "<strong>armazéns 01, 98 e 99</strong>. "
            "A previsão de cobertura soma somente pedidos de compra abertos "
            "para armazéns elegíveis, convertidos para a unidade do produto. "
            "A quantidade prevista não garante o recebimento na data informada."
            "</p>"
        )
        if dataset.row_count:
            rows = [_email_row(row) for row in dataset.rows]
            body = summary + intro + Layout.data_table_html(
                headers=_EMAIL_HEADERS,
                rows=rows,
                column_styles=_EMAIL_STYLES,
                raw_html_columns=frozenset({5, 6}),
            )
        else:
            body = (
                summary + intro
                + '<p style="padding:18px;border:1px solid #D9E6F2;'
                'border-radius:10px;color:#067647;font-weight:600;">'
                "Nenhum material abaixo do estoque de segurança "
                "foi identificado nesta filial.</p>"
            )
        body += (
            '<p style="margin-top:16px;color:#64748B;font-size:12px;">'
            "Dados do Protheus no momento da geração. Pedidos atrasados "
            "ou sem previsão estão sinalizados. Este alerta compara o saldo "
            "atual com ESTSEG, não substitui a projeção de rupturas por empenhos."
            "</p>"
        )
        html_body = Layout.wrap(
            title="Materiais abaixo do estoque de segurança",
            subtitle=f"{branch_label} · Referência {as_of} · Segunda a sexta",
            body_html=body,
        )
        return EmailPayload(
            subject=subject,
            html_body=html_body,
            attachments=(self._logo_attachment,) if self._logo_attachment else (),
        )


def _summary_html(dataset: ReportDataset) -> str:
    meta = dataset.meta
    stats = [
        ("Materiais em alerta", dataset.row_count, "#023667"),
        ("Sem cobertura", int(meta.get("uncoveredCount") or 0), "#B42318"),
        ("Cobertura parcial", int(meta.get("partialCount") or 0), "#9A6700"),
        ("Cobertos em qtd.", int(meta.get("coveredCount") or 0), "#067647"),
    ]
    cells = "".join(
        '<td valign="top" style="width:25%;padding:12px;border:1px solid #D9E6F2;">'
        f'<div style="font-size:11px;color:#64748B;">{html.escape(label)}</div>'
        f'<div style="font-size:22px;font-weight:800;color:{color};">'
        f"{value}</div></td>"
        for label, value, color in stats
    )
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="border-collapse:collapse;margin-bottom:17px;">'
        f"<tr>{cells}</tr></table>"
    )


def _email_row(row: Mapping[str, Any]) -> list[str]:
    unit = row.get("unit")
    return [
        str(row.get("product_code") or ""),
        str(row.get("product_description") or ""),
        format_quantity_with_unit(row.get("available_stock"), unit),
        format_quantity_with_unit(row.get("safety_stock"), unit),
        format_quantity_with_unit(row.get("deficit_quantity"), unit),
        _orders_html(row),
        _coverage_html(row),
    ]


def _orders_html(row: Mapping[str, Any]) -> str:
    orders = row.get("purchase_orders") or []
    if not orders:
        return '<span style="color:#B42318;">Sem pedido de compra aberto</span>'
    unit = str(row.get("unit") or "")
    blocks = []
    for order in orders:
        number = html.escape(str(order.get("order_number") or "—"))
        item = html.escape(str(order.get("order_item") or ""))
        reference = f"{number}/{item}" if item else number
        converted = order.get("open_quantity_primary_unit")
        eligible = bool(order.get("coverage_eligible"))
        quantity = (
            format_quantity_with_unit(converted, unit)
            if eligible and converted is not None
            else format_quantity_with_unit(
                order.get("open_quantity"), order.get("order_unit")
            )
        )
        delivery = format_date_br(order.get("expected_delivery_date")) or "Sem data"
        status = str(order.get("delivery_status") or "")
        flags = []
        if not eligible:
            flags.append("não elegível à cobertura (armazém/UM)")
        if status == "overdue":
            flags.append("entrega prevista vencida")
        elif status == "without_date":
            flags.append("sem data confirmada")
        flag = (
            f'<div style="color:#B45309;font-size:10px;">'
            f'{html.escape("; ".join(flags))}</div>' if flags else ""
        )
        blocks.append(
            '<div style="margin:3px 0 7px;padding-bottom:6px;'
            'border-bottom:1px solid #E2E8F0;">'
            f'<strong style="color:#023667;">PC {reference}</strong>'
            f'<div style="color:#475467;">Qtd. pendente: '
            f'{html.escape(quantity)} · Entrega: {html.escape(delivery)}</div>'
            f'{flag}</div>'
        )
    return "".join(blocks)


def _coverage_html(row: Mapping[str, Any]) -> str:
    status = str(row.get("coverage_status") or "none")
    label, color, bg = _STATUS_PT.get(status, _STATUS_PT["none"])
    eligible = format_quantity_with_unit(
        row.get("eligible_open_quantity"), row.get("unit")
    )
    after = format_quantity_with_unit(
        row.get("projected_stock_after_orders"), row.get("unit")
    )
    remaining = format_quantity_with_unit(
        row.get("remaining_to_buy"), row.get("unit")
    )
    return (
        f'<span style="display:inline-block;padding:5px 7px;'
        f'background:{bg};color:{color};font-weight:700;border-radius:6px;">'
        f'{html.escape(label)}</span>'
        f'<div style="margin-top:5px;font-size:11px;color:#475467;">'
        f'Pedidos elegíveis: {html.escape(eligible)}'
        f'<div>Saldo + pedidos: {html.escape(after)}</div>'
        f'<div>Falta adquirir: {html.escape(remaining)}</div></div>'
    )
