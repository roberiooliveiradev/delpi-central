from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_present_sql_resultsets_empty_production():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "success": True,
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "columns": ["COD_PRODUTO", "DESCRICAO_PRODUTO"],
                        "total": 0,
                        "data": [],
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert humanized["titulo"] == "Produtos programados para produção hoje"
    assert humanized["linhas"] == [
        "Nenhum produto programado para produção hoje."
    ]


def test_present_sql_resultsets_with_production_rows():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "success": True,
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "total": 2,
                        "data": [
                            {
                                "COD_PRODUTO": "90264130",
                                "DESCRICAO_PRODUTO": "PARAFUSO M8",
                                "QTD_PLANEJADA": 1200,
                                "UNIDADE": "UN",
                            },
                            {
                                "COD_PRODUTO": "10080047",
                                "DESCRICAO_PRODUTO": "TERMINAL PINO",
                                "QTD_PLANEJADA": 500,
                                "UNIDADE": "UN",
                            },
                        ],
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert "90264130" in humanized["linhas"][0]
    assert "PARAFUSO M8" in humanized["linhas"][0]
    assert "**1200 UN**" in humanized["linhas"][0]
    assert len(humanized["sqlRows"]) == 2


def test_format_sql_direct_answer_uses_product_markdown():
    presenter = ExternalActionResultPresenter()
    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "sql": "DECLARE @DATA DATE = CAST(GETDATE() AS DATE);",
                "resultsets": [
                    {
                        "data": [
                            {
                                "COD_PRODUTO": "90264130",
                                "DESCRICAO_PRODUTO": "PARAFUSO M8",
                                "QTD_PLANEJADA": 1200,
                                "UNIDADE": "UN",
                            }
                        ]
                    }
                ],
            },
        },
        path="/data/sql",
    )

    answer = ChatExternalActionDirectAnswerService.format(
        humanized,
        message="quais produtos serão produzidos hoje?",
        path="/data/sql",
    )

    assert answer is not None
    assert "**Produtos programados para produção hoje**" in answer
    assert "**`90264130`**" in answer
    assert "PARAFUSO M8" in answer
    assert "Success" not in answer
    assert "DECLARE @FILIAL" not in answer


def test_format_sql_direct_answer_for_monday():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "sql": (
                    "DECLARE @FILIAL CHAR(2) = '01';\n"
                    "DECLARE @DATA DATE = '2026-06-01';\n"
                    "SELECT OP.C2_PRODUTO AS COD_PRODUTO FROM SC2010 OP"
                ),
                "resultsets": [{"data": []}],
            },
        },
        path="/data/sql",
    )

    answer = ChatExternalActionDirectAnswerService.format(
        humanized,
        message="quais produtos serão produzidos na segunda-feira?",
        path="/data/sql",
    )

    assert answer is not None
    assert "segunda-feira" in answer.lower()
    assert "Nenhum produto programado" in answer
