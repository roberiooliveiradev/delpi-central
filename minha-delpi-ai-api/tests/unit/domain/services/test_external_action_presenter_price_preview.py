from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_product_price_preview_uses_humanized_labels():
    presenter = ExternalActionResultPresenter()

    line = presenter._format_detail_preview_line(
        {
            "table_code": "054",
            "table_description": "WEG LINHARES",
            "sale_price": 225.7,
            "discount_percent": 0.0,
        }
    )

    assert "table_code=" not in line
    assert "sale_price=" not in line
    assert "Cód. tabela" in line or "054" in line
    assert "225" in line
