from __future__ import annotations

from si_app.application.services.lmp.lmp_dashboard_summary_cache import (
    get_cached_lmp_dashboard_summary,
    lmp_dashboard_summary_cache_key,
    set_cached_lmp_dashboard_summary,
)
from si_app.application.services.lmp_business_rules import LMPBusinessRules


def resolve_lmp_dashboard_summary(
    *,
    gateway,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    include_avg_lead_time: bool = True,
    include_qtd_pi: bool = False,
) -> dict[str, float | int]:
    cache_key = lmp_dashboard_summary_cache_key(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        include_avg_lead_time=include_avg_lead_time,
        include_qtd_pi=include_qtd_pi,
    )
    cached = get_cached_lmp_dashboard_summary(cache_key)
    if cached is not None:
        return cached

    get_computed = getattr(gateway, "get_computed_dashboard_summary", None)
    if callable(get_computed):
        response = _from_computed_summary(
            gateway=gateway,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            get_computed=get_computed,
        )
    else:
        response = _from_rows(
            gateway=gateway,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            include_avg_lead_time=include_avg_lead_time,
            include_qtd_pi=include_qtd_pi,
        )

    set_cached_lmp_dashboard_summary(cache_key, response)
    return response


def _from_computed_summary(
    *,
    gateway,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    get_computed,
) -> dict[str, float | int]:
    computed = get_computed(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
    )
    return {
        "total_lmps": int(computed.get("total_lmps") or 0),
        "percent_dentro_prazo": float(computed.get("percent_dentro_prazo") or 0.0),
        "avg_lead_time": float(computed.get("avg_lead_time") or 0.0),
    }


def _from_rows(
    *,
    gateway,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    include_avg_lead_time: bool,
    include_qtd_pi: bool,
) -> dict[str, float | int]:
    rows = gateway.get_lmp_dashboard_rows(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        include_qtd_pi=include_qtd_pi,
    )

    total_lmps = len(rows)
    total_dentro_prazo = 0
    lead_times: list[int] = []

    for row in rows:
        if include_avg_lead_time:
            _, _, _, _, lead_time_util, status = LMPBusinessRules.get_dashboard_status(
                start_date_str=row.get("start_date"),
                end_date_str=row.get("end_date"),
                qtd_pi=row.get("qtd_pi"),
                engineering_status=row.get("engineering_status"),
                engineering_total_minutes=row.get("engineering_total_minutes"),
            )
            if lead_time_util is not None:
                lead_times.append(lead_time_util)
        else:
            status = LMPBusinessRules.resolve_dashboard_status(
                start_date_str=row.get("start_date"),
                end_date_str=row.get("end_date"),
                qtd_pi=row.get("qtd_pi"),
                engineering_status=row.get("engineering_status"),
                engineering_total_minutes=row.get("engineering_total_minutes"),
            )

        if status != LMPBusinessRules.DASHBOARD_STATUS_LATE:
            total_dentro_prazo += 1

    percent_dentro_prazo = (
        round((total_dentro_prazo / total_lmps) * 100, 2)
        if total_lmps > 0
        else 0.0
    )

    avg_lead_time = (
        round(sum(lead_times) / len(lead_times), 2)
        if include_avg_lead_time and lead_times
        else 0.0
    )

    return {
        "total_lmps": total_lmps,
        "percent_dentro_prazo": percent_dentro_prazo,
        "avg_lead_time": avg_lead_time,
    }
