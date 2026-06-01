from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_infer_items_title_eficiencia_fabril_not_lmp():
    presenter = ExternalActionResultPresenter()

    title = presenter._infer_items_title(
        [],
        "/production/eficiencia-fabril/dashboard",
    )

    assert title == "Eficiência fabril"


def test_infer_items_title_lmp_route_unchanged():
    presenter = ExternalActionResultPresenter()

    title = presenter._infer_items_title(
        [],
        "/engineering/lmps/dashboard",
    )

    assert title == "Lista de LMPs"


def test_build_presentation_table_title_for_eficiencia_fabril():
    presenter = ExternalActionResultPresenter()
    payload = {
        "items": [
            {
                "filial": "01",
                "op": "OP1",
                "eficiencia_percentual": 98.5,
                "tempo_real_horas": 1.2,
            },
            {
                "filial": "02",
                "op": "OP2",
                "eficiencia_percentual": 88.0,
                "tempo_real_horas": 2.0,
            },
        ],
    }

    table = presenter.build_presentation(
        payload,
        path="/production/eficiencia-fabril/dashboard",
    )

    assert table is not None
    assert table.get("type") == "table"
    assert table.get("title") == "Eficiência fabril"


def test_build_chart_title_for_eficiencia_fabril():
    presenter = ExternalActionResultPresenter()
    payload = {
        "items": [
            {
                "filial": "01",
                "op": "OP1",
                "eficiencia_percentual": 98.5,
                "qtd_apontada": 3,
            },
            {
                "filial": "02",
                "op": "OP2",
                "eficiencia_percentual": 88.0,
                "qtd_apontada": 5,
            },
        ],
    }

    chart = presenter.build_chart_presentation(
        payload,
        path="/production/eficiencia-fabril/dashboard",
        force=True,
    )

    assert chart is not None
    assert chart.get("title") == "Eficiência fabril"
