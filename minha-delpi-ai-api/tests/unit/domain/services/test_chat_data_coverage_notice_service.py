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
        {"root": {"code": "1"}, "items": [], "total": 0},
        path="/products/90260148/structure",
        parameters={"max_depth": 3},
    )

    assert notice is not None
    assert notice["kind"] == "depth"
    assert "max_depth=3" in notice["message"]


def test_table_preview_notice_when_rows_are_truncated():
    notice = ChatDataCoverageNoticeService.build(
        {"items": [{"code": str(i)} for i in range(120)], "total": 120},
        path="/products/search",
        table_presentation={
            "type": "table",
            "title": "Busca",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": str(i)} for i in range(100)],
        },
    )

    assert notice is not None
    assert "100 linha(s) de 120" in notice["message"]


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


def test_append_to_markdown_adds_coverage_block():
    markdown = ChatDataCoverageNoticeService.append_to_markdown(
        "### Título\n\nConteúdo",
        {"message": "Mostrando 2 de 10 registros."},
    )

    assert "Cobertura dos dados" in markdown
    assert "2 de 10" in markdown
