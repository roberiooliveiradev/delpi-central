from app.domain.services.chat_operational_result_completeness_service import (
    ChatOperationalResultCompletenessService,
)


def test_is_incomplete_when_pagination_flags_false() -> None:
    root = {
        "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        "summary": {"branch_filter_applied": False},
    }

    assert ChatOperationalResultCompletenessService.is_incomplete(root) is True


def test_is_complete_when_pagination_flags_true() -> None:
    root = {"pagination": {"limit": 50, "returned": 12, "is_complete": True}}

    assert ChatOperationalResultCompletenessService.is_incomplete(root) is False


def test_build_notice_message_for_unfiltered_branch() -> None:
    root = {
        "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        "summary": {"branch_filter_applied": False, "total_records": 50},
    }

    message = ChatOperationalResultCompletenessService.build_notice_message(root)

    assert message
    assert "Resultado incompleto" in message
    assert "sem filtro de filial" in message


def test_apply_to_commentary_adds_attention_and_limitations() -> None:
    root = {
        "items": [{"production_order": "1"}],
        "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        "summary": {"branch_filter_applied": False},
    }
    commentary: dict = {"profileKey": "generic_list", "attention": [], "limitations": []}
    metadata = {
        "apiDelpiResponseMeta": {
            "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        }
    }

    ChatOperationalResultCompletenessService.apply_to_commentary(
        commentary,
        metadata=metadata,
        data=root,
    )

    assert commentary.get("paginated") is True
    assert commentary["attention"]
    assert "Resultado incompleto" in commentary["attention"][0]
    assert commentary["limitations"]
    assert "Resultado incompleto" in commentary["limitations"][0]
