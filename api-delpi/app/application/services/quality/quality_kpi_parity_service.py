"""Paridade add-only das rotas centrais de qualidade com scrap/rework ÷ ROL.

Após ``enrich_dashboard_metric``, o hub expõe:
- ``value`` espelhando o KPI primário (TV/chat)
- ``summary`` operacional (filial, período, is_complete + contexto)

Nunca remove nem renomeia chaves existentes.
"""

from __future__ import annotations

from typing import Any, Mapping


def _copy_if_present(source: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in keys:
        if key in source and source[key] is not None:
            out[key] = source[key]
    return out


def _ensure_value(target: dict[str, Any], *, primary_field: str) -> None:
    if "value" in target and target.get("value") is not None:
        return
    if primary_field in target and target.get(primary_field) is not None:
        target["value"] = target[primary_field]


def _build_operational_summary(
    payload: Mapping[str, Any],
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    summary_extra_fields: tuple[str, ...],
) -> dict[str, Any]:
    existing = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    summary: dict[str, Any] = dict(existing)

    resolved_branch = branch if branch is not None else payload.get("branch")
    if "branch" not in summary and resolved_branch is not None:
        summary["branch"] = resolved_branch

    branch_filter = bool(str(resolved_branch or "").strip())
    summary.setdefault("branch_filter_applied", branch_filter)
    summary.setdefault("consolidated_across_branches", not branch_filter)
    summary.setdefault("is_complete", True)

    start = start_date if start_date is not None else payload.get("start_date")
    end = end_date if end_date is not None else payload.get("end_date")
    period = summary.get("period") if isinstance(summary.get("period"), dict) else {}
    if start is not None and "start" not in period:
        period = {**period, "start": start}
    if end is not None and "end" not in period:
        period = {**period, "end": end}
    if period:
        summary["period"] = period

    for key, value in _copy_if_present(payload, summary_extra_fields).items():
        summary.setdefault(key, value)

    return summary


def attach_quality_kpi_parity(
    payload: dict[str, Any],
    *,
    primary_field: str,
    branch: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    summary_extra_fields: tuple[str, ...] = (),
    nested_blocks: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """
    ``nested_blocks``: mapa ``bloco → campo primário`` (ex.: ideas_goal → total_kaizens).
    Só acrescenta ``value`` dentro do bloco; não altera o enrich SI já aplicado.
    """
    if not isinstance(payload, dict):
        return payload

    out = dict(payload)
    _ensure_value(out, primary_field=primary_field)

    if nested_blocks:
        for block_key, nested_primary in nested_blocks.items():
            block = out.get(block_key)
            if not isinstance(block, dict):
                continue
            nested = dict(block)
            _ensure_value(nested, primary_field=nested_primary)
            out[block_key] = nested

    out["summary"] = _build_operational_summary(
        out,
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        summary_extra_fields=summary_extra_fields,
    )
    return out
