from app.domain.services.chat_data_coverage_notice_service import (
    ChatDataCoverageNoticeService,
)


def test_pagination_notice_for_search_page():
    notice = ChatDataCoverageNoticeService.build(
        {
            "items": [{"code": "1"}, {"code": "2"}],
            "page": 1,
            "page_size": 2,
            "total": 10,
            "total_pages": 5,
        },
        path="/products/search",
    )

    assert notice is not None
    assert notice["kind"] == "pagination"
    assert "página 1 de 5" in notice["message"]
    assert "2 de 10" in notice["message"]


def test_pagination_notice_when_total_exceeds_items_without_page():
    notice = ChatDataCoverageNoticeService.build(
        {
            "items": [{"code": "1"}],
            "total": 8,
        },
        path="/products/search",
    )

    assert notice is not None
    assert "1 de 8" in notice["message"]


def test_depth_notice_for_structure_max_depth():
    notice = ChatDataCoverageNoticeService.build(
        {
            "root": {"code": "90260148", "type": "PA"},
            "items": [
                {
                    "code": "50220013",
                    "type": "PI",
                    "components": [],
                }
            ],
            "total": 1,
        },
        path="/products/90260148/structure",
        parameters={"max_depth": 1},
    )

    assert notice is not None
    assert notice["kind"] == "depth"
    assert "max_depth=1" in notice["message"]


def test_no_depth_notice_for_complete_flat_mp_structure():
    notice = ChatDataCoverageNoticeService.build(
        {
            "root": {
                "code": "90260047",
                "description": "CHICOTE DE LIGACAO",
                "type": "PA",
                "unit": "MI",
                "quantity": 1,
            },
            "items": [
                {
                    "code": "10070085",
                    "description": "CABO PP CIRCULAR",
                    "type": "MP",
                    "unit": "MT",
                    "quantity": 2015.0,
                    "components": [],
                },
                {
                    "code": "10150006",
                    "description": "PRENSA CABO PLASTICO",
                    "type": "MP",
                    "unit": "PC",
                    "quantity": 1000.0,
                    "components": [],
                },
            ],
            "page": 1,
            "page_size": 200,
            "total": 2,
            "total_pages": 1,
        },
        path="/products/90260047/structure",
        parameters={"max_depth": 99, "page": 1, "page_size": 200},
    )

    assert notice is None


def test_no_notice_when_table_shows_all_returned_items():
    notice = ChatDataCoverageNoticeService.build(
        {"items": [{"code": str(i)} for i in range(120)], "total": 120},
        path="/products/search",
        table_presentation={
            "type": "table",
            "title": "Busca",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": str(i)} for i in range(120)],
        },
    )

    assert notice is None


def test_no_notice_for_full_structure_response():
    notice = ChatDataCoverageNoticeService.build(
        {
            "root": {"code": "90260148"},
            "items": [{"code": "50220013"}, {"code": "50220015"}],
            "total": 2,
            "page": None,
            "page_size": None,
        },
        path="/products/90260148/structure",
    )

    assert notice is None


def test_sections_notice_from_response_meta():
    notice = ChatDataCoverageNoticeService.build(
        {
            "product": {"code": "90269001"},
            "structure": {"items": [{"code": "1"}], "total": 10},
        },
        path="/products/90269001/analyser",
        response_meta={
            "sections": [
                {
                    "key": "structure",
                    "label": "Estrutura",
                    "itemCount": 10,
                    "truncated": True,
                }
            ]
        },
    )

    assert notice is not None
    assert "Estrutura" in notice["message"]
    assert notice["details"]["compositeSections"]["sections"][0]["truncated"] is True


def test_operational_limit_notice_when_playbook_pagination_incomplete():
    notice = ChatDataCoverageNoticeService.build(
        {
            "items": [{"production_order": "1"} for _ in range(50)],
            "summary": {
                "total_records": 50,
                "branch_filter_applied": False,
                "is_complete": False,
            },
            "pagination": {
                "limit": 50,
                "offset": 0,
                "returned": 50,
                "is_complete": False,
            },
        },
        path="/production/schedule/today",
        response_meta={
            "pagination": {
                "limit": 50,
                "returned": 50,
                "is_complete": False,
            }
        },
    )

    assert notice is not None
    assert notice["kind"] == "pagination"
    assert "Resultado incompleto" in notice["message"]
    assert "sem filtro de filial" in notice["message"]
    assert notice["details"]["operationalPagination"]["isComplete"] is False


def test_append_to_markdown_adds_coverage_block():
    markdown = ChatDataCoverageNoticeService.append_to_markdown(
        "### Título\n\nConteúdo",
        {"message": "Mostrando 2 de 10 registros."},
    )

    assert "Cobertura dos dados" in markdown
    assert "2 de 10" in markdown
