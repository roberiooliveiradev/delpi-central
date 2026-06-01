from app.domain.services.chat_presentation_axis_preference_service import (
    ChatPresentationAxisPreferenceService,
)


def _efficiency_rows():
    return [
        {
            "filial": "02",
            "nome_operador": "ELISANGELA ANDRADE DOS SANTOS",
            "qtd_apontada": 1.8,
            "tempo_real_horas": 0.5166666666666667,
            "tempo_previsto_horas": 0.764,
            "eficiencia_percentual": 147.87,
        },
        {
            "filial": "02",
            "nome_operador": "SAULO DOS REIS CRISTO",
            "qtd_apontada": 6,
            "tempo_real_horas": 3.783333333333333,
            "tempo_previsto_horas": 2.06,
            "eficiencia_percentual": 54.45,
        },
    ]


def test_scatter_axes_prefer_efficiency_on_y():
    rows = _efficiency_rows()
    numeric = ChatPresentationAxisPreferenceService.list_numeric_keys(rows[0])

    resolved = ChatPresentationAxisPreferenceService.resolve(
        rows=rows,
        chart_type="scatter",
        label_key="nome_operador",
        numeric_keys=numeric,
        user_message="qual a eficiencia fabril de hoje?",
    )

    assert resolved["yAxis"] == ["eficiencia_percentual"]
    assert resolved["xAxis"] == "qtd_apontada"


def test_bar_axes_use_operator_category_and_efficiency_value():
    rows = _efficiency_rows()
    numeric = ChatPresentationAxisPreferenceService.list_numeric_keys(rows[0])
    categories = ChatPresentationAxisPreferenceService.list_category_keys(rows[0], numeric)

    resolved = ChatPresentationAxisPreferenceService.resolve(
        rows=rows,
        chart_type="horizontal_bar",
        label_key="filial",
        numeric_keys=numeric,
        user_message="eficiencia fabril",
    )

    assert resolved["xAxis"] in categories
    assert resolved["yAxis"][0] == "eficiencia_percentual"


def test_apply_to_chart_config_updates_presentation():
    presentation = {
        "type": "chart",
        "chartType": "scatter",
        "data": _efficiency_rows(),
        "config": {
            "xAxis": "tempo_real_horas",
            "yAxis": ["tempo_previsto_horas"],
        },
    }

    ChatPresentationAxisPreferenceService.apply_to_chart_config(
        presentation,
        user_message="qual a eficiencia fabril de hoje?",
    )

    assert presentation["config"]["yAxis"] == ["eficiencia_percentual"]
    assert presentation["config"]["xAxis"] == "qtd_apontada"
