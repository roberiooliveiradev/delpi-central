from app.domain.services.chat_turn_grounding_service import (
    ChatTurnGroundingService,
    ChatTurnGroundingStatus,
)


def test_grounded_with_last_result_excerpt():
    result = ChatTurnGroundingService.evaluate(
        message="o que me diz sobre os itens?",
        snapshot={
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 6,
                "topKeys": ["10380044"],
            }
        },
    )

    assert result.status == ChatTurnGroundingStatus.GROUNDED
    assert result.reason == "last_result_excerpt"
    assert result.referring_label
    assert "90260149" in result.referring_label


def test_ungrounded_without_history():
    result = ChatTurnGroundingService.evaluate(
        message="isso",
        snapshot={},
        previous_messages=[],
    )

    assert result.status == ChatTurnGroundingStatus.UNGROUNDED


def test_grounded_operational_focus_follow_up():
    result = ChatTurnGroundingService.evaluate(
        message="e o estoque dele?",
        snapshot={"operationalFocus": {"productCode": "10080001"}},
    )

    assert result.status == ChatTurnGroundingStatus.GROUNDED
    assert result.reason == "operational_focus_follow_up"


def test_grounded_recent_tool_success():
    result = ChatTurnGroundingService.evaluate(
        message="os itens",
        snapshot={},
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "metadata": {"ok": True, "path": "/products/1/structure"},
                        }
                    ]
                },
            }
        ],
    )

    assert result.status == ChatTurnGroundingStatus.GROUNDED
    assert result.reason == "recent_tool_success"


def test_should_narrate_excerpt_for_vague_items_question():
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044"],
    }

    assert ChatTurnGroundingService.should_narrate_excerpt(
        "o que me diz sobre os itens?",
        excerpt,
    )


def test_should_not_narrate_when_stock_expansion_requested():
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044", "10380045"],
    }

    assert not ChatTurnGroundingService.should_narrate_excerpt(
        "e o estoque desses itens?",
        excerpt,
    )
    assert ChatTurnGroundingService.should_expand_from_excerpt(
        "e o estoque desses itens?",
        excerpt,
    )
