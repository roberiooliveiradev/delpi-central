from app.application.services.response_date_format_service import (
    ResponseDateFormatService,
)


def build_period_summary(
    *,
    items: list[dict],
    branch: str | None,
    period_start: str,
    period_end_exclusive: str,
    is_complete: bool | None = None,
    consolidated_across_branches: bool | None = None,
) -> dict:
    summary = {
        "total_records": len(items),
        "branch": branch,
        "branch_filter_applied": branch is not None,
        "period": {
            "start": ResponseDateFormatService.format_date(period_start),
            "end": ResponseDateFormatService.format_date(period_end_exclusive),
        },
    }

    if consolidated_across_branches is not None:
        summary["consolidated_across_branches"] = bool(consolidated_across_branches)

    if is_complete is not None:
        summary["is_complete"] = is_complete

    return summary


def build_reference_date_summary(
    *,
    items: list[dict],
    branch: str | None,
    reference_date: str,
    is_complete: bool | None = None,
    consolidated_across_branches: bool | None = None,
) -> dict:
    summary = {
        "total_records": len(items),
        "branch": branch,
        "branch_filter_applied": branch is not None,
        "reference_date": ResponseDateFormatService.format_date(reference_date),
    }

    if consolidated_across_branches is not None:
        summary["consolidated_across_branches"] = bool(consolidated_across_branches)

    if is_complete is not None:
        summary["is_complete"] = is_complete

    return summary
