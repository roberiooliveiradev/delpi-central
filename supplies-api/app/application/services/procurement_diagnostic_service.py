"""Procurement diagnostic — deterministic multi-entity composition.

Read-only analytics: composes canonical services (overview, OTD,
deliveries, safety stock) into a structured diagnostic with per-section
status, provenance, population/sample honesty and explicit limitations.
Never widens any source's own scope — every section runs under the same
authorized user and its own business rules. No generic query executor.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from app.application.services.late_deliveries_composition_service import (
    LateDeliveriesCompositionService,
)
from app.application.services.otd_aggregate_service import (
    OtdAggregateService,
)
from app.application.services.overview_composition_service import (
    OverviewCompositionService,
)
from app.application.services.safety_stock_service import (
    SafetyStockService,
)
from app.domain.entities import EffectiveUser

logger = logging.getLogger("supplies-api.procurement_diagnostic")

SECTIONS = (
    "overview", "otd", "deliveries", "safety_stock", "supply_risk"
)


def _status_code(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    if "auth" in name or "forbidden" in name or "denied" in name:
        return "unauthorized"
    if "notfound" in name or "not_found" in name:
        return "not_found"
    return "error"


class ProcurementDiagnosticService:
    """analyze(procurement_diagnostic) — bounded composition engine."""

    def __init__(self) -> None:
        self._overview = OverviewCompositionService()
        self._otd = OtdAggregateService()
        self._deliveries = LateDeliveriesCompositionService()
        self._safety = SafetyStockService()

    def _section(
        self, name: str, source: str, fn: Callable[[], dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            data = fn()
        except Exception as exc:  # noqa: BLE001 — per-section isolation
            logger.warning(
                "procurement_diagnostic section=%s failed type=%s",
                name, type(exc).__name__,
            )
            return {
                "section": name,
                "status": "data_gap",
                "reason": _status_code(exc),
                "source": source,
                "facts": {},
                "limitations": [
                    f"Source returned {type(exc).__name__} — section "
                    "excluded rather than fabricated."
                ],
            }
        return {
            "section": name,
            "status": "ok",
            "source": source,
            "facts": data,
            "limitations": [],
        }

    def compose(
        self,
        user: EffectiveUser,
        *,
        branch: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        include_sections: list[str] | None = None,
    ) -> dict[str, Any]:
        wanted = set(include_sections or SECTIONS)
        unknown = wanted - set(SECTIONS)
        if unknown:
            raise ValueError(
                f"Unknown sections: {sorted(unknown)}. "
                f"Allowed: {sorted(SECTIONS)}"
            )
        sections: list[dict[str, Any]] = []

        if "overview" in wanted:
            sections.append(self._section(
                "overview", "bff:/analytics/overview",
                lambda: self._overview.compose(
                    user, branch=branch,
                    start_date=start_date, end_date=end_date)))
        if "otd" in wanted:
            sections.append(self._section(
                "otd", "bff:/analytics/otd",
                lambda: self._otd.compose(
                    user, branch=branch,
                    start_date=start_date, end_date=end_date)))
        if "deliveries" in wanted:
            branches = None if branch in {None, "all"} else [branch]
            sections.append(self._section(
                "deliveries", "bff:/deliveries/late",
                lambda: self._deliveries.compose(
                    user, branches=branches, status="late",
                    start_date=start_date, end_date=end_date,
                    page=1, page_size=20, sort_by=None)))
        safety: dict[str, Any] = {}
        if "safety_stock" in wanted:
            safety = self._section(
                "safety_stock", "bff:/safety-stock/summary",
                lambda: self._safety.get_summary(
                    user, branch=branch))
            sections.append(safety)
        if "supply_risk" in wanted:
            sections.append(self._section(
                "supply_risk", "derived:safety_stock+deliveries",
                lambda: self._supply_risk(safety, branch)))

        findings = []
        ok = [s["section"] for s in sections if s["status"] == "ok"]
        gaps = [s["section"] for s in sections if s["status"] == "data_gap"]
        findings.append({
            "kind": "CALCULATION",
            "label": "sections_ok",
            "value": ok,
        })
        return {
            "analysis": "procurement_diagnostic",
            "scope": {
                "branch": branch or "all",
                "start_date": start_date,
                "end_date": end_date,
            },
            "evidence_model": {
                "FACT": "values returned by canonical services",
                "CALCULATION": "deterministic derivations over returned "
                               "data",
                "INFERENCE": "none produced by this engine",
                "RECOMMENDATION": "none produced by this engine",
                "UNKNOWN": "sections in data_gap",
            },
            "population": {
                "each section reports its own universe; no sampling "
                "is presented as population"
            },
            "sections": sections,
            "completeness": {
                "sections_requested": sorted(wanted),
                "sections_ok": ok,
                "sections_data_gap": gaps,
            },
            "findings": findings,
            "limitations": [
                "Composition never widens a source's own unit/resource "
                "scope; gaps are reported, not fabricated.",
                "Cross-entity correlation is by canonical keys only; "
                "no fuzzy joins.",
            ],
        }

    def _supply_risk(
        self, safety: dict[str, Any], branch: str | None
    ) -> dict[str, Any]:
        """Deterministic exposure signals — no invented probabilities."""
        if safety.get("status") != "ok":
            return {
                "signals": [],
                "evidence": "safety_stock section unavailable — "
                            "risk signals not computed",
                "data_gap": True,
            }
        facts = safety.get("facts") or {}
        summary = facts.get("summary") or facts.get("data") or {}
        signals = []
        for key in ("deficit_items", "below_safety_stock", "deficits"):
            value = summary.get(key)
            if isinstance(value, (int, float)) and value:
                signals.append({
                    "signal": key,
                    "value": value,
                    "evidence": "safety_stock.summary (owner-calculated)",
                })
        return {
            "signals": signals,
            "evidence": "derived from safety_stock summary only — "
                        "no supplier attribution without canonical link",
            "data_gap": False,
            "branch": branch or "all",
        }
