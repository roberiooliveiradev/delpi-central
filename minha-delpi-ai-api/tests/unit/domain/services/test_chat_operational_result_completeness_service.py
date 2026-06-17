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


def test_build_notice_lines_for_unfiltered_branch() -> None:
    root = {
        "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        "summary": {"branch_filter_applied": False, "total_records": 50},
    }
    captured: list[tuple[str, dict[str, str]]] = []

    def text(key: str, **values: str) -> str:
        captured.append((key, values))
        return key

    lines = ChatOperationalResultCompletenessService.build_notice_lines(root, text=text)

    assert "incompleteResultNoBranchFilter" in lines[0]
    assert captured[0][0] == "incompleteResultNoBranchFilter"
    assert lines[-1] == "incompleteResultHint"
