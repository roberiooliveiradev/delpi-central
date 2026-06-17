def build_period_summary(
    *,
    items: list[dict],
    branch: str | None,
    period_start: str,
    period_end_exclusive: str,
    is_complete: bool | None = None,
) -> dict:
    summary = {
        "total_records": len(items),
        "branch": branch,
        "branch_filter_applied": branch is not None,
        "period": {
            "start": period_start,
            "end": period_end_exclusive,
        },
    }

    if is_complete is not None:
        summary["is_complete"] = is_complete

    return summary


def build_reference_date_summary(
    *,
    items: list[dict],
    branch: str | None,
    reference_date: str,
    is_complete: bool | None = None,
) -> dict:
    summary = {
        "total_records": len(items),
        "branch": branch,
        "branch_filter_applied": branch is not None,
        "reference_date": reference_date,
    }

    if is_complete is not None:
        summary["is_complete"] = is_complete

    return summary
