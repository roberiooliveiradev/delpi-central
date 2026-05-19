from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_present_lmp_page_from_items():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "success": True,
            "data": {
                "items": [
                    {
                        "sale_number": "123456",
                        "sale_description": "AMOSTRA TESTE",
                        "listing_kind": "Amostra",
                        "status": "Aberto",
                        "branch": "01",
                    }
                ],
                "total": 1,
                "page": 1,
            },
        }
    )

    assert result["titulo"] == "Lista de LMPs"
    assert any("123456" in line for line in result["linhas"])


def test_present_lmp_detail():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "data": {
                "sale_number": "123456",
                "sale_description": "AMOSTRA TESTE",
                "listing_kind": "LMP",
                "engineering_status": "Em andamento",
                "branch": "01",
                "qtd_pi": 3,
            }
        }
    )

    assert "123456" in result["titulo"]
    assert any("AMOSTRA" in line for line in result["linhas"])
