"""Provider — Relatório Gerencial (faturamento mensal MoM + IGD/IDDs)."""

from __future__ import annotations

import html
from datetime import date, datetime
from typing import Any, Mapping, Protocol
from zoneinfo import ZoneInfo

from app.domain.shared.numeric_parsing import to_optional_float
from app.domain.services.commercial.commercial_rol_mom_comparison_service import (
    BRANCH_LABELS_PT,
    CommercialRolMomComparisonService,
)
from app.domain.services.reports.management_revenue_monthly_rules import (
    DEFAULT_CUSTOMER_LIMIT,
    PROVIDER_DISPLAY_NAME,
    PROVIDER_KEY,
    SECTION_FATURAMENTO,
    SI_DEPARTMENT_IDS,
    SI_DEPARTMENT_LABELS_PT,
    TITLE,
    format_brl,
    format_delta_brl_html,
    format_pct_html,
    parse_as_of_date,
    parse_customer_limit,
    trend_arrow_html,
)
from app.domain.services.reports.report_email_brand_layout_service import (
    BLUE_900,
    GRAY_600,
    GRAY_900,
    ReportEmailBrandLayoutService,
)
from app.domain.services.reports.report_previous_calendar_month_service import (
    DEFAULT_TIMEZONE,
    ReportPreviousCalendarMonthService,
)
from app.domain.services.reports.report_types import (
    EmailPayload,
    ReportAttachment,
    ReportDataset,
)


class _MomBuilderPort(Protocol):
    def build(
        self,
        periods: Any,
        *,
        customer_limit: int = ...,
        branch_for_customers: str | None = ...,
    ) -> dict[str, Any]: ...


class _IgdPort(Protocol):
    def get_igd(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any] | None: ...


class _DepartmentsIndicatorsPort(Protocol):
    def list_departments_indicators(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, Any]: ...


class _DepartmentIddPort(Protocol):
    def get_department_idd(
        self,
        *,
        department_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
    ) -> dict[str, Any] | None: ...


class ManagementRevenueMonthlyProvider:
    """ReportProviderPort — faturamento do mês anterior com MoM, Top clientes e IGD/IDDs."""

    def __init__(
        self,
        mom_service: CommercialRolMomComparisonService | _MomBuilderPort,
        *,
        igd_service: _IgdPort | None = None,
        departments_indicators_service: _DepartmentsIndicatorsPort | None = None,
        department_idd_service: _DepartmentIddPort | None = None,
        logo_attachment: ReportAttachment | None = None,
    ) -> None:
        self._mom = mom_service
        self._igd = igd_service
        self._departments_indicators = departments_indicators_service
        self._department_idd = department_idd_service
        self._logo_attachment = logo_attachment

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    def describe_params(self) -> Mapping[str, Any]:
        return {
            "type": "object",
            "required": [],
            "properties": {
                "asOfDate": {
                    "type": "string",
                    "format": "date",
                    "description": "Data de referência (YYYY-MM-DD). Default: hoje.",
                },
                "customerLimit": {
                    "type": "integer",
                    "default": DEFAULT_CUSTOMER_LIMIT,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Top N clientes no ranking",
                },
            },
            "displayName": PROVIDER_DISPLAY_NAME,
        }

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        del context
        as_of_raw = parse_as_of_date(params.get("asOfDate"))
        as_of: date | None = None
        if as_of_raw:
            as_of = date.fromisoformat(as_of_raw)
        customer_limit = parse_customer_limit(params.get("customerLimit"))
        periods = ReportPreviousCalendarMonthService.resolve(as_of)
        comparison = self._mom.build(periods, customer_limit=customer_limit)

        branch_rows = comparison.get("branches") or []
        customer_rows = comparison.get("customers") or []
        report_period = comparison.get("report_period") or {}
        compare_period = comparison.get("compare_period") or {}
        year_evolution = comparison.get("year_evolution") or []

        year = int(report_period.get("year") or periods.report.year)
        month = int(report_period.get("month") or periods.report.month)
        competence = f"{year:04d}-{month:02d}"
        igd = self._collect_igd(competence)
        idd_departments = self._collect_idd_departments(competence)

        title = f"{TITLE} — {SECTION_FATURAMENTO}"
        dataset_rows = [
            {
                "section": "branch",
                "label": row.get("label_pt"),
                "branch": row.get("branch"),
                "current": row.get("current"),
                "previous": row.get("previous"),
                "delta": row.get("delta"),
                "pct_change": row.get("pct_change"),
            }
            for row in branch_rows
        ]
        dataset_rows.extend(
            {
                "section": "customer",
                "label": row.get("customer_name"),
                "customer_code": row.get("customer_code"),
                "current": row.get("current"),
                "previous": row.get("previous"),
                "share_pct": row.get("share_pct"),
                "delta": row.get("delta"),
                "pct_change": row.get("pct_change"),
                "is_others": row.get("is_others"),
            }
            for row in customer_rows
        )

        sections = ["faturamento"]
        if igd is not None or idd_departments:
            sections.append("desempenho_igd_idd")

        return ReportDataset(
            provider_key=self.key,
            title=title,
            columns=(
                "section",
                "label",
                "current",
                "previous",
                "delta",
                "pct_change",
            ),
            rows=tuple(dataset_rows),
            meta={
                "displayName": PROVIDER_DISPLAY_NAME,
                "asOfDate": as_of_raw
                or datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date().isoformat(),
                "customerLimit": customer_limit,
                "reportPeriod": report_period,
                "comparePeriod": compare_period,
                "branches": branch_rows,
                "customers": customer_rows,
                "yearEvolution": year_evolution,
                "competence": competence,
                "igd": igd,
                "iddDepartments": idd_departments,
                "sections": sections,
                "shellSectionsFuture": [
                    "meta_rol_si",
                    "weg_novos_negocios",
                    "otd_comercial",
                ],
            },
        )

    def _collect_igd(self, competence: str) -> dict[str, Any] | None:
        if self._igd is None:
            return None
        try:
            return self._igd.get_igd(competence=competence)
        except Exception:
            # Não derruba o relatório de faturamento se a SI falhar.
            return None

    def _collect_idd_departments(self, competence: str) -> list[dict[str, Any]]:
        rows = self._idd_rows_from_board(competence)
        if not rows:
            rows = self._idd_rows_from_per_department(competence)
        rows.sort(
            key=lambda row: (
                row["idd"] is None,
                -(row["idd"] if row["idd"] is not None else 0.0),
                str(row["department_name"]),
            )
        )
        return rows

    def _idd_rows_from_board(self, competence: str) -> list[dict[str, Any]]:
        if self._departments_indicators is None:
            return []
        try:
            payload = self._departments_indicators.list_departments_indicators(
                competence=competence,
            )
        except Exception:
            return []
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list) or not items:
            return []
        rows: list[dict[str, Any]] = []
        for item in items:
            mapped = self._map_idd_item(item)
            if mapped is not None:
                rows.append(mapped)
        return rows

    def _idd_rows_from_per_department(self, competence: str) -> list[dict[str, Any]]:
        """Fallback: mesma rota dos badges dos dashboards (department-score)."""
        if self._department_idd is None:
            return []
        rows: list[dict[str, Any]] = []
        for department_id in SI_DEPARTMENT_IDS:
            try:
                item = self._department_idd.get_department_idd(
                    department_id=department_id,
                    competence=competence,
                )
            except Exception:
                continue
            mapped = self._map_idd_item(item, fallback_id=department_id)
            if mapped is not None:
                rows.append(mapped)
        return rows

    @staticmethod
    def _map_idd_item(
        item: Any,
        *,
        fallback_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(item, dict):
            return None
        department_id = str(
            item.get("department_id") or item.get("id") or fallback_id or ""
        ).strip()
        score = item.get("idd")
        if score is None:
            score = item.get("score")
        score_num = to_optional_float(score)
        name = (
            item.get("department_name")
            or item.get("name")
            or SI_DEPARTMENT_LABELS_PT.get(department_id)
            or department_id
            or "—"
        )
        return {
            "department_id": department_id or None,
            "department_name": name,
            "idd": score_num,
            "classification": item.get("classification") or "—",
        }

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        report_period = dict(dataset.meta.get("reportPeriod") or {})
        compare_period = dict(dataset.meta.get("comparePeriod") or {})
        branches = list(dataset.meta.get("branches") or [])
        customers = list(dataset.meta.get("customers") or [])
        igd = dataset.meta.get("igd")
        idd_departments = list(dataset.meta.get("iddDepartments") or [])
        label = str(report_period.get("label_pt") or "")
        label_title = str(report_period.get("label_pt_title") or label)
        compare_label = str(compare_period.get("label_pt") or "")

        subject = f"{PROVIDER_DISPLAY_NAME} | {label}" if label else PROVIDER_DISPLAY_NAME
        brand = ReportEmailBrandLayoutService
        body = (
            self._executive_summary_html(branches, label_title, compare_label)
            + self._kpi_cards_html(branches)
            + self._section_heading("Filiais")
            + self._branches_table_html(branches, label, compare_label)
            + self._performance_section_html(igd, idd_departments)
            + self._section_heading("Distribuição Faturamento por cliente (Top)")
            + self._customers_table_html(customers, label, compare_label)
        )
        html_body = brand.wrap(
            title=TITLE,
            subtitle=f"{SECTION_FATURAMENTO} — {label_title}" if label_title else SECTION_FATURAMENTO,
            body_html=body,
        )
        attachments: list[ReportAttachment] = []
        if self._logo_attachment is not None:
            attachments.append(self._logo_attachment)
        return EmailPayload(
            subject=subject,
            html_body=html_body,
            attachments=tuple(attachments),
        )

    def _executive_summary_html(
        self,
        branches: list[dict[str, Any]],
        label_title: str,
        compare_label: str,
    ) -> str:
        by_key = {str(row.get("branch")): row for row in branches}
        consolidated = by_key.get("consolidated") or {}
        sc = by_key.get("01") or {}
        es = by_key.get("02") or {}
        total = float(consolidated.get("current") or 0)
        pct = consolidated.get("pct_change")
        sc_share = (
            round((float(sc.get("current") or 0) * 100.0) / total, 1)
            if total
            else None
        )
        es_share = (
            round((float(es.get("current") or 0) * 100.0) / total, 1)
            if total
            else None
        )
        bullets = [
            f"Faturamento consolidado em <strong>{html.escape(label_title)}</strong>: "
            f"<strong>{html.escape(format_brl(total))}</strong>"
            f" ({format_pct_html(pct)} vs {html.escape(compare_label)}).",
            f"{html.escape(BRANCH_LABELS_PT['01'])}: "
            f"<strong>{html.escape(format_brl(sc.get('current')))}</strong>"
            f"{f' ({sc_share}% do consolidado)' if sc_share is not None else ''}"
            f" — {format_pct_html(sc.get('pct_change'))}.",
            f"{html.escape(BRANCH_LABELS_PT['02'])}: "
            f"<strong>{html.escape(format_brl(es.get('current')))}</strong>"
            f"{f' ({es_share}% do consolidado)' if es_share is not None else ''}"
            f" — {format_pct_html(es.get('pct_change'))}.",
        ]
        items = "".join(
            f'<li style="margin:0 0 8px 0;color:{GRAY_900};font-size:14px;'
            f'line-height:1.45;">{bullet}</li>'
            for bullet in bullets
        )
        return (
            f'<p style="margin:0 0 10px 0;font-size:13px;font-weight:700;'
            f'color:{BLUE_900};text-transform:uppercase;letter-spacing:0.04em;">'
            f"Resumo executivo</p>"
            f'<ul style="margin:0 0 20px 0;padding-left:18px;">{items}</ul>'
        )

    def _kpi_cards_html(self, branches: list[dict[str, Any]]) -> str:
        cards = []
        for row in branches:
            cards.append(self._kpi_card(row))
        cells = "".join(
            f'<td width="33%" valign="top" style="padding:0 6px 12px 6px;">{card}</td>'
            for card in cards
        )
        return (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0" style="border-collapse:collapse;margin:0 0 18px 0;">'
            f"<tr>{cells}</tr></table>"
        )

    def _kpi_card(self, row: Mapping[str, Any]) -> str:
        label = html.escape(str(row.get("label_pt") or ""))
        current = html.escape(format_brl(row.get("current")))
        delta_value = row.get("delta")
        pct_value = row.get("pct_change")
        # Preferência: seta pelo %; se ausente, pelo Δ R$
        arrow_basis = pct_value if pct_value is not None else delta_value
        arrow = trend_arrow_html(arrow_basis)
        delta = format_delta_brl_html(delta_value)
        pct = format_pct_html(pct_value)
        return (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'border="0" style="border-collapse:collapse;border:1px solid #E2E8F0;'
            'border-radius:10px;background:#F8FAFC;">'
            "<tr><td style=\"padding:14px 14px 12px 14px;\">"
            f'<p style="margin:0 0 6px 0;font-size:11px;font-weight:700;'
            f'color:{GRAY_600};text-transform:uppercase;letter-spacing:0.03em;">'
            f"{label}</p>"
            f'<p style="margin:0 0 8px 0;font-size:18px;font-weight:700;'
            f'color:{BLUE_900};">{current}</p>'
            f'<p style="margin:0;font-size:12px;color:{GRAY_900};">'
            f"{arrow} {delta} · {pct}</p>"
            "</td></tr></table>"
        )

    def _performance_section_html(
        self,
        igd: Any,
        idd_departments: list[dict[str, Any]],
    ) -> str:
        if not isinstance(igd, dict) and not idd_departments:
            return ""
        parts = [self._section_heading("Desempenho — IGD e IDDs")]
        if isinstance(igd, dict):
            parts.append(self._igd_card_html(igd))
        if idd_departments:
            parts.append(self._idd_table_html(idd_departments))
        elif isinstance(igd, dict):
            parts.append(
                f'<p style="margin:0 0 16px 0;color:{GRAY_600};font-size:13px;">'
                "IDDs departamentais indisponíveis neste envio.</p>"
            )
        return "".join(parts)

    def _igd_card_html(self, igd: Mapping[str, Any]) -> str:
        score = igd.get("igd")
        try:
            score_txt = f"{float(score):.1f}".replace(".", ",") if score is not None else "—"
        except (TypeError, ValueError):
            score_txt = "—"
        classification = html.escape(str(igd.get("classification") or "—"))
        trend = str(igd.get("trendDirection") or "").strip().lower()
        if trend in {"up", "alta", "positive", "positivo"}:
            arrow = trend_arrow_html(1)
            trend_label = "alta vs período anterior"
        elif trend in {"down", "baixa", "negative", "negativo"}:
            arrow = trend_arrow_html(-1)
            trend_label = "queda vs período anterior"
        else:
            arrow = trend_arrow_html(0)
            trend_label = "estável vs período anterior"
        extras: list[str] = []
        best = igd.get("bestDepartment")
        risk = igd.get("primaryRisk")
        if best:
            extras.append(f"Melhor: {html.escape(str(best))}")
        if risk:
            extras.append(f"Atenção: {html.escape(str(risk))}")
        extras_html = (
            f'<p style="margin:8px 0 0 0;font-size:12px;color:{GRAY_600};">'
            f"{' · '.join(extras)}</p>"
            if extras
            else ""
        )
        return (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'border="0" style="border-collapse:collapse;margin:0 0 14px 0;'
            'border:1px solid #E2E8F0;border-radius:10px;background:#F8FAFC;">'
            "<tr><td style=\"padding:14px 16px;\">"
            f'<p style="margin:0 0 6px 0;font-size:11px;font-weight:700;'
            f'color:{GRAY_600};text-transform:uppercase;letter-spacing:0.03em;">'
            "Índice Global DELPI</p>"
            f'<p style="margin:0 0 6px 0;font-size:28px;font-weight:700;'
            f'color:{BLUE_900};">{html.escape(score_txt)}</p>'
            f'<p style="margin:0;font-size:13px;color:{GRAY_900};">'
            f"<strong>{classification}</strong> · {arrow} {html.escape(trend_label)}</p>"
            f"{extras_html}"
            "</td></tr></table>"
        )

    def _idd_table_html(self, departments: list[dict[str, Any]]) -> str:
        headers = ["Departamento", "IDD", "Classificação"]
        rows: list[list[str]] = []
        for row in departments:
            score = row.get("idd")
            try:
                score_txt = (
                    f"{float(score):.1f}".replace(".", ",") if score is not None else "—"
                )
            except (TypeError, ValueError):
                score_txt = "—"
            rows.append(
                [
                    str(row.get("department_name") or "—"),
                    score_txt,
                    str(row.get("classification") or "—"),
                ]
            )
        return ReportEmailBrandLayoutService.data_table_html(
            headers=headers,
            rows=rows,
            column_styles=[
                "text-align:left;",
                "text-align:right;",
                "text-align:left;",
            ],
        )

    def _section_heading(self, text: str) -> str:
        return (
            f'<p style="margin:8px 0 10px 0;font-size:13px;font-weight:700;'
            f'color:{BLUE_900};text-transform:uppercase;letter-spacing:0.04em;">'
            f"{html.escape(text)}</p>"
        )

    def _branches_table_html(
        self,
        branches: list[dict[str, Any]],
        label: str,
        compare_label: str,
    ) -> str:
        headers = [
            "Filial",
            label or "Mês",
            compare_label or "Anterior",
            "Δ %",
        ]
        rows = [
            [
                str(row.get("label_pt") or ""),
                format_brl(row.get("current")),
                format_brl(row.get("previous")),
                format_pct_html(row.get("pct_change")),
            ]
            for row in branches
        ]
        return ReportEmailBrandLayoutService.data_table_html(
            headers=headers,
            rows=rows,
            column_styles=[
                "text-align:left;",
                "text-align:right;",
                "text-align:right;",
                "text-align:right;",
            ],
            raw_html_columns=frozenset({3}),
        )

    def _customers_table_html(
        self,
        customers: list[dict[str, Any]],
        label: str,
        compare_label: str,
    ) -> str:
        if not customers:
            return (
                f'<p style="margin:0 0 12px 0;color:{GRAY_600};font-size:13px;">'
                "Nenhum faturamento por cliente no período.</p>"
            )
        headers = [
            "Cliente",
            label or "Mês",
            "Share",
            compare_label or "Anterior",
            "Δ %",
        ]
        rows = []
        for row in customers:
            name = str(row.get("customer_name") or "").strip() or "—"
            share = row.get("share_pct")
            share_txt = "—" if share is None else f"{float(share):.2f}%".replace(".", ",")
            rows.append(
                [
                    name,
                    format_brl(row.get("current")),
                    share_txt,
                    format_brl(row.get("previous")),
                    format_pct_html(row.get("pct_change")),
                ]
            )
        return ReportEmailBrandLayoutService.data_table_html(
            headers=headers,
            rows=rows,
            column_styles=[
                "text-align:left;",
                "text-align:right;",
                "text-align:right;",
                "text-align:right;",
                "text-align:right;",
            ],
            raw_html_columns=frozenset({4}),
        )
