from app.domain.services.chat_chart_type_selection_service import (
    ChatChartTypeSelectionService,
)


def _rows(*pairs: tuple[str, float]) -> list[dict]:
    return [{"name": label, "value": value} for label, value in pairs]


def test_resolve_donut_from_message():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=_rows(("A", 40), ("B", 35), ("C", 25)),
        label_key="name",
        numeric_keys=["value"],
        user_message="mostre participação em rosca",
    )

    assert chart_type == "donut"


def test_resolve_horizontal_bar_for_ranking():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=_rows(
            ("Produto com nome bem longo", 10),
            ("Outro produto extenso", 8),
            ("Terceiro", 6),
            ("Quarto", 4),
            ("Quinto", 2),
            ("Sexto", 1),
            ("Sétimo", 1),
        ),
        label_key="name",
        numeric_keys=["value"],
    )

    assert chart_type == "horizontal_bar"


def test_resolve_line_for_temporal_periods():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[
            {"period": "2026-01", "value": 10},
            {"period": "2026-02", "value": 12},
            {"period": "2026-03", "value": 9},
        ],
        label_key="period",
        numeric_keys=["value"],
    )

    assert chart_type == "line"


def test_resolve_grouped_bar_for_multiple_series():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[
            {"name": "Jan", "meta": 10, "realizado": 8},
            {"name": "Fev", "meta": 11, "realizado": 12},
        ],
        label_key="name",
        numeric_keys=["meta", "realizado"],
    )

    assert chart_type == "grouped_bar"


def test_resolve_combo_for_meta_realizado_series():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[
            {"period": "2026-01", "meta": 100, "realizado": 80},
            {"period": "2026-02", "meta": 110, "realizado": 105},
        ],
        label_key="period",
        numeric_keys=["meta", "realizado"],
    )

    assert chart_type == "combo"


def test_resolve_heatmap_from_message():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[
            {"cliente": "A", "mes": "jan", "valor": 10},
            {"cliente": "A", "mes": "fev", "valor": 12},
            {"cliente": "B", "mes": "jan", "valor": 8},
            {"cliente": "B", "mes": "fev", "valor": 9},
        ],
        label_key="cliente",
        numeric_keys=["valor"],
        user_message="mostre mapa de calor por cliente e mês",
    )

    assert chart_type == "heatmap"


def test_resolve_heatmap_for_matrix_shape():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[
            {"turno": "A", "dia": "seg", "qtd": 4},
            {"turno": "A", "dia": "ter", "qtd": 6},
            {"turno": "B", "dia": "seg", "qtd": 3},
            {"turno": "B", "dia": "ter", "qtd": 5},
        ],
        label_key="turno",
        numeric_keys=["qtd"],
    )

    assert chart_type == "heatmap"


def test_resolve_scatter_for_two_numeric_columns():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[
            {"x": 1, "y": 2},
            {"x": 3, "y": 5},
            {"x": 4, "y": 3},
        ],
        label_key="x",
        numeric_keys=["x", "y"],
    )

    assert chart_type == "scatter"


def test_resolve_histogram_for_many_buckets():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[{"bucket": f"B{i}", "count": i} for i in range(10)],
        label_key="bucket",
        numeric_keys=["count"],
    )

    assert chart_type == "histogram"


def test_resolve_gauge_for_single_row_meta_value():
    chart_type = ChatChartTypeSelectionService.resolve(
        rows=[{"label": "OTD", "meta": 95, "realizado": 88}],
        label_key="label",
        numeric_keys=["meta", "realizado"],
    )

    assert chart_type == "gauge"


def test_try_chart_from_rows_uses_selection():
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    chart = presenter._try_chart_from_rows(
        [
            {"period": "2026-01", "revenue": 100},
            {"period": "2026-02", "revenue": 120},
            {"period": "2026-03", "revenue": 90},
        ],
        force=True,
    )

    assert chart is not None
    assert chart["chartType"] == "line"
