from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_present_product_billing_summary():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "value": 21024.26,
            "documents": 19,
            "first_billing_date": "20070518",
            "last_billing_date": "20150331",
        },
        path="/products/10080047/sales/billing",
    )

    assert humanized["titulo"] == "Faturamento do produto 10080047"
    assert any("21.024,26" in line for line in humanized["linhas"])
    assert any("Documentos" in line for line in humanized["linhas"])


def test_present_stock_value_summary_with_kpi():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "branch": "consolidated",
            "summary": {
                "total_stock_value": 13961229.55,
                "total_stock_quantity": 45095937.19,
                "total_records": 71504,
                "total_products": 40473,
                "total_locations": 21,
            },
            "by_branch": [
                {"branch": "01", "total_stock_value": 4025471.8, "total_stock_quantity": 5895695.29},
            ],
        },
        path="/supplies/stock-value",
    )

    assert humanized["titulo"] == "Valor Total de Estoque"
    assert any("Valor total em estoque" in line for line in humanized["linhas"])
    assert humanized["apresentacao"]["type"] == "kpi"


def test_present_financial_pmr_without_data():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {"branch": "02", "pmr_days": None},
        path="/financial/pmr",
    )

    assert "PMR" in humanized["titulo"]
    assert any("Não há PMR calculado" in line for line in humanized["linhas"])


def test_build_text_presentation_for_billing():
    presenter = ExternalActionResultPresenter()

    text = presenter.build_text_presentation(
        {
            "value": 21024.26,
            "documents": 19,
            "first_billing_date": "20070518",
            "last_billing_date": "20150331",
        },
        path="/products/10080047/sales/billing",
    )

    assert text is not None
    assert "21.024,26" in text["markdown"]
    assert "veja os dados abaixo" not in text["markdown"].lower()
