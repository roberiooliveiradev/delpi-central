from app.domain.services.chat_pagination_consolidation_service import (
    ChatPaginationConsolidationService,
    PaginationConsolidationState,
)


def _paginated_payload(page: int, *, page_size: int = 2, total: int = 6):
    items = [{"code": f"p{page}-{index}"} for index in range(page_size)]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total // page_size,
    }


def test_looks_like_full_fetch_request():
    assert ChatPaginationConsolidationService.looks_like_full_fetch_request(
        "traga a lista completa dos pais"
    )
    assert ChatPaginationConsolidationService.looks_like_full_fetch_request(
        "arvore completa"
    )
    assert not ChatPaginationConsolidationService.looks_like_full_fetch_request(
        "onde é usado o produto 10080047"
    )


def test_looks_like_continue_fetch_request():
    assert ChatPaginationConsolidationService.looks_like_continue_fetch_request(
        "sim, continue"
    )
    assert ChatPaginationConsolidationService.looks_like_continue_fetch_request("sim")
    assert not ChatPaginationConsolidationService.looks_like_continue_fetch_request(
        "sim, quero ver o produto"
    )


def test_extract_snapshot_from_payload():
    snapshot = ChatPaginationConsolidationService.extract_snapshot(
        metadata={},
        data={"data": _paginated_payload(1)},
    )

    assert snapshot is not None
    assert snapshot.page == 1
    assert snapshot.total == 6
    assert snapshot.total_pages == 3


def test_build_fetch_plan_for_full_request():
    plan = ChatPaginationConsolidationService.build_fetch_plan(
        message="traga tudo",
        metadata={"actionId": "parents-action", "path": "/products/{code}/parents"},
        data={"data": _paginated_payload(1)},
        arguments={"actionId": "parents-action", "parameters": {"code": "10080047"}},
    )

    assert plan is not None
    assert plan.mode == "full_fetch"
    assert plan.pages_to_fetch == (2, 3)
    assert plan.resume_state is not None
    assert plan.resume_state.merged_count == 2


def test_merge_payloads_consolidates_items():
    merged = ChatPaginationConsolidationService.merge_payloads(
        [
            {"data": _paginated_payload(1)},
            {"data": _paginated_payload(2)},
        ]
    )

    root = ChatPaginationConsolidationService._unwrap(merged)
    assert len(root["items"]) == 4
    assert root["page"] == 1
    assert root["total_pages"] == 1


def test_collect_state_from_previous_messages():
    previous_messages = [
        {
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "actionId": "parents-action",
                            "path": "/products/{code}/parents",
                            "paginationConsolidation": {
                                "actionId": "parents-action",
                                "path": "/products/{code}/parents",
                                "parameters": {"code": "10080047"},
                                "fetchedPages": [1, 2],
                                "mergedCount": 4,
                                "apiTotal": 6,
                                "totalPages": 3,
                                "completed": False,
                            },
                        },
                    }
                ]
            }
        }
    ]

    state = ChatPaginationConsolidationService.collect_state(previous_messages)

    assert state is not None
    assert state.merged_count == 4
    assert state.fetched_pages == (1, 2)


def test_build_continue_plan_from_state():
    previous_messages = [
        {
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "actionId": "parents-action",
                            "paginationConsolidation": {
                                "actionId": "parents-action",
                                "path": "/products/{code}/parents",
                                "parameters": {"code": "10080047"},
                                "fetchedPages": [1, 2],
                                "mergedCount": 4,
                                "apiTotal": 6,
                                "totalPages": 3,
                                "completed": False,
                            },
                        },
                    }
                ]
            }
        }
    ]

    plan = ChatPaginationConsolidationService.build_continue_plan(
        message="sim, continue",
        previous_messages=previous_messages,
    )

    assert plan is not None
    assert plan.mode == "continue"
    assert plan.pages_to_fetch == (3,)


def test_build_continue_prompt_when_incomplete():
    prompt = ChatPaginationConsolidationService.build_continue_prompt(
        state=PaginationConsolidationState(
            action_id="parents-action",
            path="/products/{code}/parents",
            parameters={"code": "10080047"},
            fetched_pages=(1, 2),
            merged_count=50,
            api_total=282,
            total_pages=12,
            completed=False,
        ),
    )

    assert "50" in prompt
    assert "282" in prompt
    assert "continue" in prompt.lower()


def test_build_state_marks_completed_when_all_pages_fetched():
    state = ChatPaginationConsolidationService.build_state(
        plan=ChatPaginationConsolidationService.build_fetch_plan(
            message="traga tudo",
            metadata={"actionId": "a", "path": "/x"},
            data={"data": _paginated_payload(1, page_size=2, total=4)},
            arguments={"actionId": "a", "parameters": {}},
        ),
        fetched_pages=[1, 2],
        merged_count=4,
        api_total=4,
        total_pages=2,
    )

    assert state.completed is True
