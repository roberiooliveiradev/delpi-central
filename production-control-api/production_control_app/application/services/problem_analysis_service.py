"""Análise de problemas — orquestração dos detectores da fábrica.

O serviço não sabe o que cada detector procura: ele lê o catálogo declarativo,
casa cada entrada com a implementação registrada e devolve os cards. Detector
novo entra por registro + entrada no JSON, sem tocar em rota nem aqui.
"""

from __future__ import annotations

from typing import Any

from production_control_app.application.services.problem_analysis_settings import (
    as_int,
    detector_catalog,
    detector_entry,
)
from production_control_app.core.security import PC_PROBLEM_ANALYSIS_VIEW, can
from production_control_app.domain.errors import DetectorNotFound
from production_control_app.domain.ports.problem_detector import (
    DetectorSummary,
    ProblemDetector,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService


def _card(entry: dict[str, Any], summary: DetectorSummary) -> dict[str, Any]:
    return {
        "id": str(entry.get("id")),
        "title": str(entry.get("title") or ""),
        "description": str(entry.get("description") or ""),
        "action_hint": str(entry.get("actionHint") or "") or None,
        "icon": str(entry.get("icon") or "") or None,
        "order": as_int(entry.get("order"), 0),
        "severity": summary.severity,
        "count": summary.count,
        "metrics": summary.metrics,
    }


class ProblemAnalysisService:
    def __init__(
        self,
        detectors: dict[str, ProblemDetector],
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._detectors = detectors
        self._branch_access = branch_access or BranchAccessService()

    def _authorize(self, user: object | None, *, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_PROBLEM_ANALYSIS_VIEW):
            raise PermissionError("Você não tem permissão para análise de problemas.")

    def _entries(self) -> list[tuple[dict[str, Any], ProblemDetector]]:
        pairs = []
        for entry in detector_catalog():
            detector = self._detectors.get(str(entry.get("id")))
            if detector is not None:
                pairs.append((entry, detector))
        return pairs

    def list_detectors(self, user: object | None, *, branch: str) -> dict[str, Any]:
        self._authorize(user, branch=branch)
        cards = [
            _card(entry, detector.summarize(branch=branch))
            for entry, detector in self._entries()
        ]
        return {
            "branch": branch,
            "detectors": cards,
            "summary": {
                "detector_count": len(cards),
                "issue_count": sum(card["count"] for card in cards),
                "critical": sum(1 for card in cards if card["severity"] == "critical"),
                "attention": sum(1 for card in cards if card["severity"] == "attention"),
            },
        }

    def detector_items(
        self,
        user: object | None,
        *,
        branch: str,
        detector_id: str,
        page: int = 1,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        self._authorize(user, branch=branch)

        entry = detector_entry(detector_id)
        detector = self._detectors.get(str(detector_id or "").strip())
        if entry is None or detector is None:
            raise DetectorNotFound(f"Detector desconhecido: {detector_id}.")

        result = detector.collect(
            branch=branch,
            page=max(as_int(page, 1), 1),
            page_size=as_int(page_size, 0),
        )
        total_pages = 0
        if result.total and result.page_size:
            total_pages = (result.total + result.page_size - 1) // result.page_size
        return {
            "branch": branch,
            "detector": _card(entry, result.summary),
            "summary": result.summary.metrics,
            "items": result.items,
            "pagination": {
                "page": result.page,
                "page_size": result.page_size,
                "total": result.total,
                "total_pages": total_pages,
                "is_complete": result.page >= total_pages if total_pages else True,
            },
        }
