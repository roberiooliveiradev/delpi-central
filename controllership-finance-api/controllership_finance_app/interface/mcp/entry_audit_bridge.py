"""CLARA reads and findings for entry audit. No new MCP tool.

The six semantic tools stay. These handlers are catalog entries that
call the same application service as the HTTP routes.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from mcp.types import CallToolResult

from controllership_finance_app.application.entry_audit.composer import (
    build_entry_audit_service,
)
from controllership_finance_app.application.entry_audit.errors import (
    EntryAuditError,
)
from controllership_finance_app.interface.mcp.tool_bridge import _error, _ok

_LIST_FILTERS = (
    "branch",
    "severity",
    "theme",
    "supplier",
    "tes",
    "document_type",
    "day",
    "status",
    "q",
)


def _service():
    return build_entry_audit_service()


def _call(action):
    try:
        return _ok(action())
    except EntryAuditError as exc:
        return _error(str(exc), status_code=exc.status_code, error_code=exc.code)
    except ValueError as exc:
        return _error(str(exc), status_code=422, error_code="INVALID_PERIOD")


def _day(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _filters(source: dict) -> dict:
    return {name: source[name] for name in _LIST_FILTERS if source.get(name)}


def _pages(page: int | None, page_size: int | None) -> tuple[int, int]:
    return int(page or 1), int(page_size or 50)


def tool_entry_audit_options() -> CallToolResult:
    """Filiais e tipos de documento da auditoria de entradas."""
    return _call(lambda: _service().options())


def tool_entry_audit_analysis(
    analysis_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    branch: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> CallToolResult:
    """Histórico ou andamento de uma análise de entradas."""
    page_n, size = _pages(page, page_size)

    def _run():
        if analysis_id:
            return _service().get_analysis(analysis_id)
        return _service().list_analyses(
            date_from=_day(date_from),
            date_to=_day(date_to),
            branch=branch,
            status=status,
            page=page_n,
            page_size=size,
        )

    return _call(_run)


def tool_entry_audit_summary(analysis_id: str, **filters: Any) -> CallToolResult:
    """KPIs e conformidade de uma análise."""
    return _call(lambda: _service().summary(analysis_id, _filters(filters)))


def tool_entry_audit_daily(analysis_id: str, **filters: Any) -> CallToolResult:
    """Divergências por dia."""
    return _call(lambda: _service().daily(analysis_id, _filters(filters)))


def tool_entry_audit_breakdowns(analysis_id: str, **filters: Any) -> CallToolResult:
    """Severidade, tema, fornecedor e TES."""
    return _call(lambda: _service().breakdowns(analysis_id, _filters(filters)))


def tool_entry_audit_trend(
    date_from: str,
    date_to: str,
    branch: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> CallToolResult:
    """Evolução entre análises do período."""
    del page, page_size
    return _call(lambda: _service().trend(branch=branch, date_from=_day(date_from), date_to=_day(date_to)))


def tool_entry_audit_occurrences(analysis_id: str, page: int | None = None, page_size: int | None = None, **filters: Any) -> CallToolResult:
    """Lista de ocorrências da análise."""
    page_n, size = _pages(page, page_size)
    return _call(lambda: _service().occurrences(analysis_id, _filters(filters), page=page_n, page_size=size, sort=""))


def tool_entry_audit_occurrence(analysis_id: str, key: str) -> CallToolResult:
    """Detalhe de uma ocorrência, com a regra e o histórico."""
    return _call(lambda: _service().occurrence(analysis_id, key))


def tool_entry_audit_documents(analysis_id: str, page: int | None = None, page_size: int | None = None, **filters: Any) -> CallToolResult:
    """Notas da análise."""
    page_n, size = _pages(page, page_size)
    return _call(lambda: _service().documents(analysis_id, _filters(filters), page=page_n, page_size=size))


def tool_entry_audit_unmatched(analysis_id: str, page: int | None = None, page_size: int | None = None, **filters: Any) -> CallToolResult:
    """Notas sem par, com a situação que explica cada uma."""
    page_n, size = _pages(page, page_size)
    return _call(lambda: _service().unmatched_documents(analysis_id, _filters(filters), page=page_n, page_size=size))


def tool_entry_audit_cte(analysis_id: str, page: int | None = None, page_size: int | None = None, **filters: Any) -> CallToolResult:
    """CT-e da análise."""
    page_n, size = _pages(page, page_size)
    return _call(lambda: _service().ctes(analysis_id, _filters(filters), page=page_n, page_size=size))


def tool_entry_audit_tes(analysis_id: str, page: int | None = None, page_size: int | None = None, **filters: Any) -> CallToolResult:
    """TES usadas na análise."""
    del page, page_size
    return _call(lambda: _service().tes_used(analysis_id, _filters(filters)))


def _cause(rule_id: str) -> str:
    if rule_id.startswith("key.supplier") or rule_id == "simples.presumed_wrong_tes":
        return "cadastro"
    if rule_id.startswith("key.") or rule_id.startswith("item.cfop") or rule_id.startswith("coherence."):
        return "cadastro"
    return "tes"


def _public_row(row: dict) -> dict:
    hidden = {"access_key", "stable_key", "supplier_name", "xml"}
    return {key: value for key, value in row.items() if key not in hidden and not isinstance(value, (dict, list))}


def tool_analyze_entry_audit_findings(
    ref: str | None = None,
    analysis_id: str | None = None,
    compare_to: str | None = None,
    **filters: Any,
) -> CallToolResult:
    """Achados FACT/RECOMMENDATION da auditoria, agrupados pela causa."""
    target = ref or analysis_id
    if not target:
        return _error("Informe ref com o id da análise.", status_code=422, error_code="MISSING_REF")

    def _run():
        service = _service()
        page_n = 1
        rows: list[dict] = []
        total = None
        while page_n <= 5:
            page = service.occurrences(target, _filters(filters), page=page_n, page_size=200, sort="")
            rows.extend(page.get("items") or [])
            total = page.get("total")
            if total is None or len(rows) >= int(total):
                break
            page_n += 1
        summary = service.summary(target, _filters(filters))
        groups: dict[tuple, list[dict]] = {}
        for row in rows:
            key = (str(row.get("rule_id") or ""), str(row.get("title") or ""), str(row.get("severity") or ""), str(row.get("tes") or ""))
            groups.setdefault(key, []).append(row)
        findings = []
        kpis = (summary.get("kpis") or {}) if isinstance(summary, dict) else {}
        conformity = (summary.get("conformity") or {}) if isinstance(summary, dict) else {}
        findings.append({
            "kind": "FACT",
            "code": "entry_audit.coverage",
            "message": (
                f"{kpis.get('documents', 0)} notas, {kpis.get('occurrences', 0)} ocorrências, "
                f"{conformity.get('unmatched_explained', 0)} sem par explicadas, "
                f"{kpis.get('xml_unavailable', 0)} XML indisponível."
            ),
            "value": {"kpis": kpis, "conformity": conformity},
        })
        for (rule_id, title, severity, tes), items in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0][0])):
            action = str(items[0].get("action") or items[0].get("what_to_do") or "")
            findings.append({
                "kind": "FACT",
                "code": rule_id or "entry_audit.occurrence",
                "cause": _cause(rule_id),
                "message": f"{len(items)} × {title or rule_id} ({severity}). TES {tes or '—'}.",
                "value": {"count": len(items), "severity": severity, "rule_id": rule_id, "tes": tes, "sample": [_public_row(row) for row in items[:3]]},
            })
            if action:
                findings.append({
                    "kind": "RECOMMENDATION",
                    "code": rule_id or "entry_audit.occurrence",
                    "cause": _cause(rule_id),
                    "message": action,
                    "value": {"rule_id": rule_id, "count": len(items)},
                })
        if compare_to:
            other = service.summary(compare_to, _filters(filters))
            other_kpis = other.get("kpis") or {}
            delta = {
                name: int(kpis.get(name) or 0) - int(other_kpis.get(name) or 0)
                for name in ("documents", "occurrences", "high", "xml_unavailable")
            }
            findings.append({
                "kind": "FACT",
                "code": "entry_audit.compare",
                "message": "Diferença contra a análise comparada (esta menos a outra).",
                "value": delta,
            })
        counts = Counter(row.get("severity") for row in rows)
        return {
            "analysis_id": target,
            "findings": findings,
            "by_severity": {str(key): value for key, value in counts.items() if key},
            "truncated": bool(total is not None and len(rows) < int(total)),
        }

    return _call(_run)
