"""Unit — layout de marca dos e-mails Delpi Reports."""

from __future__ import annotations

from app.domain.services.reports.report_email_brand_layout_service import (
    BLUE_900,
    BLUE_ACCENT,
    LOGO_CONTENT_ID,
    ReportEmailBrandLayoutService,
)


def test_brand_wrap_includes_logo_cid_strip_and_footer() -> None:
    html = ReportEmailBrandLayoutService.wrap(
        title="Rupturas de estoque",
        subtitle="Filial 01",
        body_html="<p>miolo</p>",
    )
    assert f'cid:{LOGO_CONTENT_ID}' in html
    assert BLUE_900 in html
    assert BLUE_ACCENT in html
    assert "www.delpi.com.br" in html
    assert "Gerado pelo Minha DELPI — Relatórios" in html
    assert "Rupturas de estoque" in html
    assert "Filial 01" in html
    assert "<p>miolo</p>" in html


def test_data_table_escapes_and_zebra() -> None:
    html = ReportEmailBrandLayoutService.data_table_html(
        headers=["Código"],
        rows=[["A<b>"], ["B"]],
    )
    assert "A&lt;b&gt;" in html
    assert BLUE_900 in html


def test_data_table_applies_column_styles() -> None:
    html = ReportEmailBrandLayoutService.data_table_html(
        headers=["Código", "Data da ruptura"],
        rows=[["1", "21/07/2026"]],
        column_styles=["", "min-width:96px;width:96px;white-space:nowrap;"],
    )
    assert "min-width:96px" in html
    assert "21/07/2026" in html


def test_brand_wrap_content_padding() -> None:
    html = ReportEmailBrandLayoutService.wrap(
        title="T",
        body_html="<p>x</p>",
    )
    assert "padding:28px 32px 32px 32px" in html
    assert "max-width:860px" in html
