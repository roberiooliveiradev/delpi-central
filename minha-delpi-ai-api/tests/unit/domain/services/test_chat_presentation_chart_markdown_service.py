from app.domain.services.chat_presentation_chart_markdown_service import (
    ChatPresentationChartMarkdownService,
)


def _donut_chart() -> dict:
    return {
        "type": "chart",
        "title": "Composição por tipo",
        "chartType": "donut",
        "data": [
            {"label": "MP (7)", "value": 7},
            {"label": "PI (2)", "value": 2},
        ],
    }


def _bar_chart() -> dict:
    return {
        "type": "chart",
        "title": "Saldo por filial",
        "chartType": "bar",
        "config": {"xAxis": "branch", "yAxis": "quantity"},
        "data": [
            {"branch": "01", "quantity": 120},
            {"branch": "02", "quantity": 85},
        ],
    }


def test_mermaid_pie_from_donut_chart():
    section = ChatPresentationChartMarkdownService._chart_section(
        _donut_chart(),
        metadata={"path": "/products/90269001/analyser"},
    )

    assert "**Composição por tipo**" in section
    assert "```mermaid" in section
    assert "pie showData" in section
    assert '"MP (7)" : 7' in section


def test_mermaid_xychart_from_bar_chart():
    section = ChatPresentationChartMarkdownService._chart_section(
        _bar_chart(),
        metadata={"path": "/products/90269001/stock"},
    )

    assert "```mermaid" in section
    assert "xychart-beta" in section
    assert "bar [" in section
    assert '"01"' in section


def test_horizontal_bar_falls_back_to_markdown_table():
    chart = {
        "type": "chart",
        "title": "Saldo de MP — 90262404",
        "chartType": "horizontal_bar",
        "config": {"xAxis": "raw_material_code", "yAxis": "available_quantity_total"},
        "data": [
            {"raw_material_code": "10080063", "available_quantity_total": 0},
            {"raw_material_code": "10130006", "available_quantity_total": 0},
        ],
    }

    section = ChatPresentationChartMarkdownService._chart_section(
        chart,
        metadata={"path": "/products/90262404/factory-status"},
    )

    assert "```mermaid" not in section
    assert "|" in section
    assert "10080063" in section


def test_embed_charts_skips_when_chart_policy_is_skip():
    metadata = {
        "path": "/products/90262404/factory-status",
        "explicitSessionFormat": "text",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nResumo.",
        },
        "chartPresentation": {
            "type": "chart",
            "title": "Saldo de MP",
            "chartType": "horizontal_bar",
            "data": [{"raw_material_code": "10080063", "available_quantity_total": 0}],
        },
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
        },
    }

    ChatPresentationChartMarkdownService.embed_charts_in_text_presentation(metadata)

    assert "```mermaid" not in metadata["textPresentation"]["markdown"]


def test_mermaid_xychart_quotes_branch_labels_with_slash_and_dot():
    chart = {
        "type": "chart",
        "title": "Estoque por filial/armazém",
        "chartType": "bar",
        "config": {"xAxis": "branch", "yAxis": "quantity"},
        "data": [{"branch": "Fil.01/01", "quantity": 0}],
    }

    section = ChatPresentationChartMarkdownService._chart_section(
        chart,
        metadata={"path": "/products/90269001/stock"},
    )

    assert 'x-axis ["Fil.01/01"]' in section


def test_heatmap_falls_back_to_markdown_table():
    chart = {
        "type": "chart",
        "title": "Mapa de calor",
        "chartType": "heatmap",
        "data": [
            {"row": "A", "col": "B", "value": 3},
            {"row": "C", "col": "D", "value": 5},
        ],
    }

    section = ChatPresentationChartMarkdownService._chart_section(
        chart,
        metadata={"path": "/products/90269001/stock"},
    )

    assert "```mermaid" not in section
    assert "| row |" in section or "|" in section
    assert "heatmap" in section.lower()


def test_embed_charts_in_text_presentation_when_text_selected():
    metadata = {
        "path": "/products/90269001/analyser",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Analyser\n\nResumo.",
        },
        "chartPresentation": _donut_chart(),
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
        },
    }

    ChatPresentationChartMarkdownService.embed_charts_in_text_presentation(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "pie showData" in markdown
    assert "MP (7)" in markdown
    assert metadata.get("chartPresentation") is None


def test_embed_charts_skips_stack_layout_without_explicit_text():
    metadata = {
        "path": "/products/90269001/analyser",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Analyser\n\nResumo.",
        },
        "chartPresentation": _donut_chart(),
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
        },
    }

    ChatPresentationChartMarkdownService.embed_charts_in_text_presentation(metadata)

    assert "pie showData" not in metadata["textPresentation"]["markdown"]


def test_embed_charts_in_explicit_text_stack_layout():
    metadata = {
        "path": "/products/90269001/analyser",
        "explicitSessionFormat": "text",
        "preferredFormat": "text",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Analyser\n\nResumo.",
        },
        "chartPresentation": _donut_chart(),
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
        },
    }

    ChatPresentationChartMarkdownService.embed_charts_in_text_presentation(metadata)

    assert "pie showData" in metadata["textPresentation"]["markdown"]
