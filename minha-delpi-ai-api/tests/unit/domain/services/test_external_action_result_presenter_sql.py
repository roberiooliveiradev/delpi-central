from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_present_sql_resultsets_empty_inventory_below_minimum():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "sql": (
                    "SELECT SB2.B2_COD AS product_code, SB1.B1_EMIN AS minimum_stock "
                    "FROM SB2010 SB2 INNER JOIN SB1010 SB1 ON SB1.B1_COD = SB2.B2_COD"
                ),
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "columns": [
                            "product_code",
                            "product_description",
                            "branch",
                            "warehouse",
                            "current_quantity",
                            "minimum_stock",
                            "available_quantity",
                        ],
                        "total": 0,
                        "data": [],
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert humanized["titulo"] == "Produtos com estoque abaixo do mínimo"
    assert humanized["linhas"] == [
        "Nenhum produto com estoque abaixo do mínimo cadastrado."
    ]


def test_build_presentation_empty_inventory_resultset_table():
    presenter = ExternalActionResultPresenter()

    table = presenter.build_presentation(
        {
            "success": True,
            "data": {
                "sql": (
                    "SELECT SB2.B2_COD AS product_code, COALESCE(SBZ.BZ_ESTSEG, SB1.B1_EMIN) "
                    "AS minimum_stock FROM SB2010 SB2 LEFT JOIN SBZ010 SBZ ON SBZ.BZ_COD = SB2.B2_COD"
                ),
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "columns": [
                            "product_code",
                            "product_description",
                            "minimum_stock",
                            "current_quantity",
                        ],
                        "total": 0,
                        "data": [],
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert table is not None
    assert table["type"] == "table"
    assert table["title"] == "Produtos com estoque abaixo do mínimo"
    assert table["rows"] == []
    assert any(col.get("key") == "minimum_stock" for col in table["columns"])


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

    assert humanized["linhas"] == ["A consulta retornou **2** registro(s)."]
    assert len(humanized["sqlRows"]) == 2

    table = presenter.build_presentation(
        {
            "success": True,
            "data": {
                "success": True,
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "total": 2,
                        "data": humanized["sqlRows"],
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert table is not None
    assert table["type"] == "table"
    assert len(table["rows"]) == 2


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


def test_present_sql_empty_production_title_from_message_when_sql_missing():
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

    answer = ChatExternalActionDirectAnswerService.format(
        humanized,
        message="quais produtos serão produzidos na segunda-feira?",
        path="/data/sql",
    )

    assert answer is not None
    assert "segunda-feira" in answer.lower()
    assert "hoje" not in answer.lower().split("programados para produção", 1)[-1][:40]
