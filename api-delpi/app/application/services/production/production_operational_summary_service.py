def build_period_summary(
    *,
    items: list[dict],
    branch: str | None,
    period_start: str,
    period_end_exclusive: str,
) -> dict:
    return {
        "total_records": len(items),
        "branch": branch,
        "period": {
            "start": period_start,
            "end": period_end_exclusive,
        },
    }


def build_reference_date_summary(
    *,
    items: list[dict],
    branch: str | None,
    reference_date: str,
) -> dict:
    return {
        "total_records": len(items),
        "branch": branch,
        "reference_date": reference_date,
    }
