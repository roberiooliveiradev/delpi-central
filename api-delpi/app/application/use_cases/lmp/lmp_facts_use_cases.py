# app/application/use_cases/lmp/lmp_facts_use_cases.py
"""Contratos facts F-LMP-01..04 (doc 33) — extração oficial, sem regra de negócio.

Estes use cases NÃO classificam status, nível, prazo ou KPI: essas
semânticas pertencem à engineering-api (G3). O facts contract devolve
dados de origem normalizados + sinalizadores derivados declarados, para
que o consumer execute as regras oficialmente.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.services.lmp_business_rules import LMPBusinessRules
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort

FACTS_PAGE_SIZE_DEFAULT = 50
FACTS_PAGE_SIZE_MAX = 500
FACTS_PI_COUNT_BATCH_MAX = 500

_FACTS_PROVENANCE = {"source_system": "TOTVS", "integration_owner": "api-delpi"}


def _facts_policy_meta(repository: LMPQueryRepositoryPort) -> dict[str, Any]:
    settings = getattr(repository, "settings", None)
    return {
        "period_policy": getattr(settings, "period_inclusion_policy", None),
        "min_engineering_residence_minutes": getattr(
            settings, "min_engineering_residence_minutes", None
        ),
        "strict_residence_after_homolog": getattr(
            settings, "strict_residence_after_homolog", None
        ),
        "residence_filter_applied": True,
        "listing_type_filter_semantics": "effective",
    }


class ListLmpFactsUseCase:
    """F-LMP-01 — lista paginada de fatos por OV qualificada."""

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: ListLMPRequest) -> dict[str, Any]:
        page = max(int(request.page or 1), 1)
        page_size = int(request.page_size or FACTS_PAGE_SIZE_DEFAULT)
        if page_size < 1:
            page_size = FACTS_PAGE_SIZE_DEFAULT
        if page_size > FACTS_PAGE_SIZE_MAX:
            page_size = FACTS_PAGE_SIZE_MAX

        rows = self._repository.get_lmp_facts(request)
        items = [LMPBusinessRules.format_payload_dates(dict(row)) for row in rows]

        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]

        return {
            "items": page_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total else 0,
            "provenance": _FACTS_PROVENANCE,
            "policy": _facts_policy_meta(self._repository),
        }


class GetLmpFactUseCase:
    """F-LMP-02 — fato detalhado de uma OV; include=products|history opcional."""

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetLMPRequest, *, include: str | None = None) -> dict:
        item = self._repository.get_lmp(request)
        payload = item.to_dict()
        include_set = {
            part.strip().lower() for part in (include or "").split(",") if part.strip()
        }

        if "history" not in include_set:
            payload["list_history"] = []
        else:
            events = self._repository.get_lmp_history_events(
                GetLmpHistoryRequest(
                    sale_number=request.sale_number,
                    date_start=request.date_start,
                    date_end=request.date_end,
                    branch=request.branch,
                )
            )
            payload["list_history"] = [
                LMPBusinessRules.format_payload_dates(event.to_dict())
                for event in events
            ]

        payload["provenance"] = _FACTS_PROVENANCE
        return payload


class GetLmpFactsHistoryUseCase:
    """F-LMP-03 — eventos/fluxo crus da fonte (sem enriquecimento de domínio)."""

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetLmpHistoryRequest, *, view: str = "events") -> dict:
        panel_context = self._repository.get_lmp_history_panel_context(request)
        if view == "flow":
            events = self._repository.get_lmp_history_flow(request)
        else:
            events = self._repository.get_lmp_history_events(request)

        items = [
            LMPBusinessRules.format_payload_dates(event.to_dict()) for event in events
        ]
        return {
            "sale_number": request.sale_number,
            "branch": panel_context.get("branch") or request.branch,
            "reference_revision": panel_context.get("reference_revision"),
            "panel_start_date": LMPBusinessRules.format_date_for_response(
                panel_context.get("panel_start_date")
            ),
            "view": view,
            "items": items,
            "total": len(items),
            "provenance": _FACTS_PROVENANCE,
        }


class GetLmpPiCountsUseCase:
    """F-LMP-04 — contagens PI por (branch, sale_number, revision) em lote."""

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(
        self,
        *,
        ov_keys: list[dict[str, Optional[str]]],
        requested_branch: str | None = None,
    ) -> dict[str, Any]:
        if len(ov_keys) > FACTS_PI_COUNT_BATCH_MAX:
            raise ValueError(
                f"Lote excede o máximo de {FACTS_PI_COUNT_BATCH_MAX} OVs por requisição."
            )
        counts = self._repository.get_lmp_pi_counts_by_ovs(
            ov_keys=ov_keys,
            requested_branch=requested_branch,
        )
        items = [
            {
                "branch": branch,
                "sale_number": sale_number,
                "revision": revision,
                "qtd_pi": int(qtd_pi),
            }
            for (branch, sale_number, revision), qtd_pi in sorted(counts.items())
        ]
        return {
            "items": items,
            "total": len(items),
            "provenance": _FACTS_PROVENANCE,
        }
