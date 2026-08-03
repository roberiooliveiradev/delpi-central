"""Unit — provider Relatório Gerencial (faturamento mensal)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.domain.services.reports.management_revenue_monthly_rules import (
    PROVIDER_KEY,
    format_brl,
    format_pct,
)
from app.domain.services.reports.providers.management_revenue_monthly_provider import (
    ManagementRevenueMonthlyProvider,
)
from app.domain.services.reports.report_previous_calendar_month_service import (
    ReportPreviousCalendarMonthService,
)


def test_format_brl_and_pct() -> None:
    assert format_brl(1234.5) == "R$ 1.234,50"
    assert format_pct(12.5) == "+12,50%"
    assert format_pct(-3.2) == "-3,20%"
    assert format_pct(None) == "—"


def test_trend_arrow_html() -> None:
    from app.domain.services.reports.management_revenue_monthly_rules import (
        NEGATIVE_COLOR,
        POSITIVE_COLOR,
        trend_arrow_html,
    )

    up = trend_arrow_html(1.57)
    down = trend_arrow_html(-3.33)
    flat = trend_arrow_html(0)
    assert "▲" in up and POSITIVE_COLOR in up
    assert "▼" in down and NEGATIVE_COLOR in down
    assert "●" in flat


def test_provider_collect_and_render() -> None:
    mom = MagicMock()
    periods = ReportPreviousCalendarMonthService.resolve(date(2026, 7, 1))
    mom.build.return_value = {
        "report_period": {
            "start_date": periods.report.start_date,
            "end_date": periods.report.end_date,
            "label_pt": periods.report.label_pt,
            "label_pt_title": periods.report.label_pt_title,
            "year": periods.report.year,
            "month": periods.report.month,
        },
        "compare_period": {
            "start_date": periods.compare.start_date,
            "end_date": periods.compare.end_date,
            "label_pt": periods.compare.label_pt,
            "label_pt_title": periods.compare.label_pt_title,
            "year": periods.compare.year,
            "month": periods.compare.month,
        },
        "branches": [
            {
                "branch": "consolidated",
                "label_pt": "Consolidado",
                "current": 1000.0,
                "previous": 800.0,
                "delta": 200.0,
                "pct_change": 25.0,
            },
            {
                "branch": "01",
                "label_pt": "Jaraguá do Sul (SC)",
                "current": 700.0,
                "previous": 600.0,
                "delta": 100.0,
                "pct_change": 16.67,
            },
            {
                "branch": "02",
                "label_pt": "Rio Bananal (ES)",
                "current": 300.0,
                "previous": 200.0,
                "delta": 100.0,
                "pct_change": 50.0,
            },
        ],
        "customers": [
            {
                "customer_code": "000001",
                "customer_store": "01",
                "customer_name": "WEG",
                "current": 500.0,
                "previous": 400.0,
                "share_pct": 50.0,
                "delta": 100.0,
                "pct_change": 25.0,
                "rank": 1,
                "is_others": False,
            }
        ],
        "year_evolution": [
            {"label": "Jan/26", "value": 8_200_000.0, "month": 1, "year": 2026},
            {"label": "Fev/26", "value": 9_100_000.0, "month": 2, "year": 2026},
            {"label": "Mar/26", "value": 10_400_000.0, "month": 3, "year": 2026},
            {"label": "Abr/26", "value": 12_000_000.0, "month": 4, "year": 2026},
            {"label": "Mai/26", "value": 13_500_000.0, "month": 5, "year": 2026},
            {"label": "Jun/26", "value": 14_800_000.0, "month": 6, "year": 2026},
        ],
    }
    igd = MagicMock()
    igd.get_igd.return_value = {
        "igd": 7.8,
        "classification": "Bom",
        "trendDirection": "up",
        "bestDepartment": "Comercial",
        "primaryRisk": "Qualidade",
        "competence": "2026-06",
    }
    departments = MagicMock()
    departments.list_departments_indicators.return_value = {
        "items": [
            {
                "department_id": "quality",
                "department_name": "Qualidade",
                "idd": 6.2,
                "classification": "Atenção",
            },
            {
                "department_id": "commercial",
                "department_name": "Comercial",
                "score": 8.5,
                "classification": "Excelência",
            },
        ],
        "partial_success": False,
        "errors": [],
    }
    provider = ManagementRevenueMonthlyProvider(
        mom,
        igd_service=igd,
        departments_indicators_service=departments,
    )
    assert provider.key == PROVIDER_KEY
    dataset = provider.collect({"asOfDate": "2026-07-01", "customerLimit": 20})
    assert "Faturamento" in dataset.title
    assert dataset.meta["reportPeriod"]["label_pt"] == "jun/2026"
    assert dataset.meta["competence"] == "2026-06"
    assert dataset.meta["igd"]["igd"] == 7.8
    assert [row["department_name"] for row in dataset.meta["iddDepartments"]] == [
        "Comercial",
        "Qualidade",
    ]
    assert "desempenho_igd_idd" in dataset.meta["sections"]
    igd.get_igd.assert_called_once_with(competence="2026-06")
    departments.list_departments_indicators.assert_called_once_with(competence="2026-06")
    email = provider.render_email(dataset)
    assert "jun/2026" in email.subject
    assert "Resumo executivo" in email.html_body
    assert "WEG" in email.html_body
    assert "000001" not in email.html_body
    assert "Evolução do faturamento" in email.html_body
    assert "Consolidado no ano" in email.html_body
    # Valor integral no subtítulo (não abreviação em mi)
    assert "R$ 68.000.000,00" in email.html_body
    assert email.html_body.count("Consolidado no ano") == 1
    assert "cid:rol-year-chart" in email.html_body
    assert "<svg" not in email.html_body
    assert "Desempenho — IGD e IDDs" in email.html_body
    assert "IGD — Índice Geral de Desempenho" in email.html_body
    assert "7,8" in email.html_body
    assert "Comercial" in email.html_body
    assert "Qualidade" in email.html_body
    assert "8,5" in email.html_body
    assert any(
        getattr(att, "content_id", None) == "rol-year-chart"
        for att in email.attachments
    )
    assert "cid:delpi-logo" in email.html_body or "DELPI" in email.html_body


def test_provider_falls_back_to_per_department_idd() -> None:
    mom = MagicMock()
    periods = ReportPreviousCalendarMonthService.resolve(date(2026, 7, 1))
    mom.build.return_value = {
        "report_period": {
            "start_date": periods.report.start_date,
            "end_date": periods.report.end_date,
            "label_pt": periods.report.label_pt,
            "label_pt_title": periods.report.label_pt_title,
            "year": periods.report.year,
            "month": periods.report.month,
        },
        "compare_period": {
            "start_date": periods.compare.start_date,
            "end_date": periods.compare.end_date,
            "label_pt": periods.compare.label_pt,
            "label_pt_title": periods.compare.label_pt_title,
            "year": periods.compare.year,
            "month": periods.compare.month,
        },
        "branches": [],
        "customers": [],
        "year_evolution": [],
    }
    igd = MagicMock()
    igd.get_igd.return_value = {
        "igd": 7.0,
        "classification": "Bom",
        "trendDirection": "flat",
        "competence": "2026-06",
    }
    departments = MagicMock()
    departments.list_departments_indicators.return_value = {
        "items": [],
        "partial_success": False,
        "errors": [],
    }
    per_dept = MagicMock()

    def _idd(**kwargs):
        dept = kwargs["department_id"]
        if dept == "commercial":
            return {
                "department_id": "commercial",
                "department_name": "Comercial",
                "score": 8.1,
                "classification": "Excelência",
            }
        if dept == "quality":
            return {
                "department_id": "quality",
                "score": 6.0,
                "classification": "Atenção",
            }
        return None

    per_dept.get_department_idd.side_effect = _idd
    provider = ManagementRevenueMonthlyProvider(
        mom,
        igd_service=igd,
        departments_indicators_service=departments,
        department_idd_service=per_dept,
    )
    dataset = provider.collect({"asOfDate": "2026-07-01"})
    names = [row["department_name"] for row in dataset.meta["iddDepartments"]]
    assert names == ["Comercial", "Qualidade"]
    email = provider.render_email(dataset)
    assert "IDDs departamentais indisponíveis" not in email.html_body
    assert "Comercial" in email.html_body
    assert "8,1" in email.html_body


def test_provider_omits_performance_when_si_unavailable() -> None:
    mom = MagicMock()
    periods = ReportPreviousCalendarMonthService.resolve(date(2026, 7, 1))
    mom.build.return_value = {
        "report_period": {
            "start_date": periods.report.start_date,
            "end_date": periods.report.end_date,
            "label_pt": periods.report.label_pt,
            "label_pt_title": periods.report.label_pt_title,
            "year": periods.report.year,
            "month": periods.report.month,
        },
        "compare_period": {
            "start_date": periods.compare.start_date,
            "end_date": periods.compare.end_date,
            "label_pt": periods.compare.label_pt,
            "label_pt_title": periods.compare.label_pt_title,
            "year": periods.compare.year,
            "month": periods.compare.month,
        },
        "branches": [],
        "customers": [],
        "year_evolution": [],
    }
    igd = MagicMock()
    igd.get_igd.return_value = None
    departments = MagicMock()
    departments.list_departments_indicators.return_value = {
        "items": [],
        "partial_success": False,
        "errors": [],
    }
    provider = ManagementRevenueMonthlyProvider(
        mom,
        igd_service=igd,
        departments_indicators_service=departments,
    )
    dataset = provider.collect({"asOfDate": "2026-07-01"})
    assert dataset.meta["igd"] is None
    assert dataset.meta["iddDepartments"] == []
    assert "desempenho_igd_idd" not in dataset.meta["sections"]
    email = provider.render_email(dataset)
    assert "Desempenho — IGD e IDDs" not in email.html_body
    assert "Resumo executivo" in email.html_body


def test_format_brl_mi() -> None:
    from app.domain.services.reports.management_revenue_monthly_rules import (
        format_brl_mi,
    )

    assert format_brl_mi(24_800_000) == "R$ 24,8 mi"
    assert format_brl_mi(3_700_000) == "R$ 3,7 mi"


def test_line_chart_png_formats_millions() -> None:
    from app.domain.services.reports.report_email_consolidated_line_chart_service import (
        CHART_CONTENT_ID,
        ReportEmailConsolidatedLineChartService,
        _axis_bounds,
        _fmt_mi,
    )

    html_out, attachment = ReportEmailConsolidatedLineChartService.build(
        title="Evolução do faturamento (R$ mi) — 2026",
        points=[
            {"label": "Jan/26", "value": 8_200_000},
            {"label": "Jun/26", "value": 14_800_000},
        ],
        year_total_label="Consolidado no ano (2026): R$ 23.000.000,00",
    )
    assert f"cid:{CHART_CONTENT_ID}" in html_out
    assert "Consolidado no ano (2026): R$ 23.000.000,00" in html_out
    # Título limpo — consolidado só no subtítulo
    assert "· Consolidado" not in html_out
    assert attachment is not None
    assert attachment.content_id == "rol-year-chart"
    assert attachment.content_type == "image/png"
    assert len(attachment.content_base64) > 100
    assert _fmt_mi(4.27551795, digits=2) == "4,28"

    y_min, y_max, _step = _axis_bounds([3.6, 3.7, 4.0, 4.3, 4.4])
    assert y_min >= 2.5
    assert y_max <= 5.5
    assert (y_max - y_min) < 4.0
