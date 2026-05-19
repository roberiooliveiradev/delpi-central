# app/application/dto/lmp/list_lmp_request.py
from dataclasses import dataclass
from typing import Optional

LISTING_KIND_LMP = "LMP"
LISTING_KIND_SAMPLE = "AMOSTRA"
LISTING_KIND_OTHER = "OUTRO"


def resolve_listing_type_filter(
    raw: str | None,
    *,
    lmp_only: bool = False,
) -> str | None:
    if lmp_only:
        return LISTING_KIND_LMP

    if raw is None:
        return None

    normalized = str(raw).strip().lower()
    if normalized in ("", "todos", "all"):
        return None
    if normalized == "lmp":
        return LISTING_KIND_LMP
    if normalized in ("amostra", "amostras", "sample"):
        return LISTING_KIND_SAMPLE
    if normalized in ("outro", "outros", "other"):
        return LISTING_KIND_OTHER

    raise ValueError(
        "listing_type inválido. Valores aceitos: Todos, LMP, Amostra ou Outro."
    )


@dataclass
class ListLMPRequest:
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    listing_type: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None