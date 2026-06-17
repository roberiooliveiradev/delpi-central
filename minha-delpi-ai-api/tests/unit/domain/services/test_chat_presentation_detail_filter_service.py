from app.domain.services.chat_presentation_detail_filter_service import (
    ChatPresentationDetailFilterService,
)


def test_apply_filters_schedule_items_by_product_code_prefix():
    payload = {
        "items": [
            {"product_code": "90260255", "description": "PA A"},
            {"product_code": "10080001", "description": "PA B"},
            {"product_code": "90261486", "description": "PA C"},
        ]
    }

    filtered = ChatPresentationDetailFilterService.apply(
        payload,
        {"product_code_prefix": "9026"},
    )

    assert filtered["items"] == [
        {"product_code": "90260255", "description": "PA A"},
        {"product_code": "90261486", "description": "PA C"},
    ]


def test_apply_returns_empty_list_when_prefix_has_no_matches():
    payload = {
        "items": [
            {"product_code": "10080001", "description": "PA B"},
        ]
    }

    filtered = ChatPresentationDetailFilterService.apply(
        payload,
        {"product_code_prefix": "9026"},
    )

    assert filtered["items"] == []


def test_apply_filters_sql_resultsets_by_product_code_prefix():
    payload = {
        "resultsets": [
            {
                "rows": [
                    {"COD_PRODUTO": "90261486", "C2_OP": "10405001001"},
                    {"COD_PRODUTO": "70260010", "C2_OP": "99999999001"},
                ]
            }
        ]
    }

    filtered = ChatPresentationDetailFilterService.apply(
        payload,
        {"product_code_prefix": "90261486"},
    )

    rows = filtered["resultsets"][0]["rows"]
    assert len(rows) == 1
    assert rows[0]["COD_PRODUTO"] == "90261486"
    assert filtered["query_context"]["product_code_prefix"] == "90261486"
