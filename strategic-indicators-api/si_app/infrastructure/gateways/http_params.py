from __future__ import annotations


def std_http_params(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    **extra: str | None,
) -> dict[str, str | None]:
    params = {
        "branch": branch,
        "start_date": start_date,
        "end_date": end_date,
    }
    params.update(extra)
    return params


def opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
