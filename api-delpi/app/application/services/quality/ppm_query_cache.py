from __future__ import annotations

from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.composition.query_cache_composer import build_query_cache
from app.domain.entities.ppm.ppm_summary import PpmSummary


def ppm_summary_cache_key(request: PpmSummaryRequest) -> str:
    return "|".join(
        [
            "ppm-summary",
            request.type,
            request.branch or "",
            request.date_start or "",
            request.date_end or "",
            request.product_prefix or "",
        ]
    )


def get_cached_ppm_summary(key: str) -> PpmSummary | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        payload = {
            k: cached[k]
            for k in (
                "type",
                "branch",
                "start_date",
                "end_date",
                "total_devolvido_un",
                "total_produzido_milheiro",
                "total_produzido_un",
                "ppm",
            )
            if k in cached
        }
        return PpmSummary(**payload)
    return None


def set_cached_ppm_summary(key: str, value: PpmSummary) -> None:
    build_query_cache().set(key, value.to_dict())
