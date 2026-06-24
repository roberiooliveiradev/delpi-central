from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_present_system_tables_search_schema_first() -> None:
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "success": True,
            "total_records": 2,
            "results": [
                {
                    "X2_ARQUIVO": "SB1",
                    "X2_NOME": "CADASTRO DE PRODUTOS",
                    "total_score": 92.5,
                },
                {
                    "X2_ARQUIVO": "SB2",
                    "X2_NOME": "GRUPO DE PRODUTOS",
                    "total_score": 71.0,
                },
            ],
        },
        path="/system/tables/search",
    )

    assert result.get("titulo")
    joined = "\n".join(
        [
            result.get("titulo") or "",
            *(result.get("linhas") or []),
            result.get("humanizedMarkdown") or "",
        ]
    )
    assert "SB1" in joined
    assert "CADASTRO DE PRODUTOS" in joined
