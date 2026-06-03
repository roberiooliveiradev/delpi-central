from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.domain.services.chat_data_coverage_notice_service import (
    ChatDataCoverageNoticeService,
)


def test_sanitize_sql_resultset_keeps_all_rows_from_api():
    policy = ExternalActionExecutionPolicy()
    rows = [{"A1_COD": str(index)} for index in range(120)]

    sanitized = policy.sanitize_response(
        {
            "success": True,
            "data": {
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "columns": ["A1_COD"],
                        "total": 284,
                        "data": rows,
                    }
                ],
            },
        }
    )

    resultsets = sanitized["data"]["resultsets"]

    assert len(resultsets[0]["data"]) == 120
    assert resultsets[0]["total"] == 284


def test_sanitize_items_list_without_artificial_cap():
    policy = ExternalActionExecutionPolicy()
    items = [{"code": str(index)} for index in range(620)]

    sanitized = policy.sanitize_response(
        {
            "items": items,
            "page": 1,
            "page_size": 620,
            "total": 620,
        }
    )

    assert len(sanitized["items"]) == 620
    assert "_dataTruncations" not in sanitized


def test_present_sql_resultsets_uses_total_not_preview_row_count():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "columns": ["A1_COD", "A1_NOME"],
                        "total": 284,
                        "data": [
                            {"A1_COD": "000179", "A1_NOME": "EMPRESA A"},
                            {"A1_COD": "000072", "A1_NOME": "EMPRESA B"},
                        ],
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert "**284**" in humanized["linhas"][0] or "284" in humanized["linhas"][0]
    assert "25 registro" not in humanized["linhas"][0].lower()
    assert len(humanized["linhas"]) <= 2
    assert not any(line.strip().startswith("1.") for line in humanized["linhas"])


def test_build_text_presentation_sql_keeps_summary_without_row_dump():
    presenter = ExternalActionResultPresenter()
    rows = [
        {"A1_COD": f"{index:06d}", "A1_NOME": f"EMPRESA {index}"}
        for index in range(20)
    ]

    text = presenter.build_text_presentation(
        {
            "success": True,
            "data": {
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "columns": ["A1_COD", "A1_NOME"],
                        "total": 284,
                        "data": rows,
                    }
                ],
            },
        },
        path="/data/sql",
    )

    table = presenter.build_presentation(
        {
            "success": True,
            "data": {
                "total_resultsets": 1,
                "resultsets": [
                    {
                        "index": 1,
                        "columns": ["A1_COD", "A1_NOME"],
                        "total": 284,
                        "data": rows,
                    }
                ],
            },
        },
        path="/data/sql",
    )

    assert text is not None
    assert table is not None
    assert table["type"] == "table"
    assert len(table["rows"]) == 20
    assert "284" in text["markdown"]
    assert "EMPRESA 0" not in text["markdown"]
    assert "1." not in text["markdown"]


def test_sql_resultset_coverage_notice_when_api_total_exceeds_rows():
    notice = ChatDataCoverageNoticeService.build(
        {
            "total_resultsets": 1,
            "resultsets": [
                {
                    "index": 1,
                    "total": 284,
                    "data": [{"A1_COD": "1"} for _ in range(25)],
                }
            ],
        },
        path="/data/sql",
        table_presentation={
            "type": "table",
            "title": "Consulta SQL",
            "columns": [{"key": "A1_COD", "label": "A1 cod"}],
            "rows": [{"A1_COD": "1"} for _ in range(25)],
        },
    )

    assert notice is not None
    assert "25 de 284" in notice["message"]
    assert "limite de segurança" not in notice["message"]
