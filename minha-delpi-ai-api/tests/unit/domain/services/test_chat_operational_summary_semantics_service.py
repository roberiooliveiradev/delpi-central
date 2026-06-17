from app.domain.services.chat_operational_summary_semantics_service import (
    ChatOperationalSummarySemanticsService,
)


def test_consolidated_across_branches_reads_summary_flag() -> None:
    root = {
        "summary": {
            "consolidated_across_branches": True,
            "branch_filter_applied": False,
        }
    }

    assert ChatOperationalSummarySemanticsService.consolidated_across_branches(root) is True


def test_filter_summary_removes_technical_keys() -> None:
    filtered = ChatOperationalSummarySemanticsService.filter_summary(
        {
            "total_records": 50,
            "is_complete": False,
            "branch_filter_applied": False,
            "consolidated_across_branches": True,
        }
    )

    assert filtered == {"total_records": 50}
