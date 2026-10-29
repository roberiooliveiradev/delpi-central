"""Semântica de listagem LMP — S03/S05/S07/R17 (owner: Engineering API).

Portado de `api-delpi/.../lmp_listing_kind_semantics_service.py` +
`list_lmp_request.py` (constantes e resolução de filtros), conforme
`lmp_semantics.v1.yaml` S03/S05/S07.

A Engineering API reclassifica o `listing_kind` efetivo sobre os fatos
(`listing_kind_source` + flags declaradas). O valor executado na fonte
(SQL `_effective_listing_kind_expr`) vem em `listing_kind` como referência
— a reclassificação aqui é a autoridade semântica e alimenta a paridade.
"""

from __future__ import annotations

LISTING_KIND_LMP = "LMP"
LISTING_KIND_SAMPLE = "AMOSTRA"
LISTING_KIND_OTHER = "OUTRO"

LISTING_KIND_PRIORITY = {LISTING_KIND_LMP: 2, LISTING_KIND_SAMPLE: 1, LISTING_KIND_OTHER: 0}

DEFAULT_MIN_RESIDENCE_MINUTES = 30
DEFAULT_STRICT_RESIDENCE_AFTER_HOMOLOG = False


def resolve_listing_type_filter(
    raw: str | None,
    *,
    lmp_only: bool = False,
) -> str | None:
    """Filtro funcional da listagem — aliases do contrato legado."""
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


def effective_listing_kind(
    *,
    anchor_kind: str | None,
    has_sample_anchor: bool,
    sample_minutes: int,
    total_minutes: int,
    has_lmp_finalized: bool,
    min_residence_minutes: int = DEFAULT_MIN_RESIDENCE_MINUTES,
    strict_residence_after_homolog: bool = DEFAULT_STRICT_RESIDENCE_AFTER_HOMOLOG,
) -> str | None:
    """S05/S07 — classe efetiva por revisão sobre os fatos declarados."""
    if anchor_kind != LISTING_KIND_LMP:
        return anchor_kind

    if strict_residence_after_homolog and has_lmp_finalized:
        if total_minutes < min_residence_minutes:
            return LISTING_KIND_OTHER

    if has_sample_anchor and not has_lmp_finalized:
        if sample_minutes > 0:
            return LISTING_KIND_SAMPLE
        if total_minutes < min_residence_minutes:
            return LISTING_KIND_OTHER

    return anchor_kind


def lmp_passes_residence_filter(
    *,
    listing_kind: str | None,
    total_minutes: int,
    has_sample_anchor: bool,
    has_lmp_finalized: bool,
    min_residence_minutes: int = DEFAULT_MIN_RESIDENCE_MINUTES,
    strict_residence_after_homolog: bool = DEFAULT_STRICT_RESIDENCE_AFTER_HOMOLOG,
    has_engineering_stage: bool = False,
) -> bool:
    """S03 — elegibilidade por residência em engenharia.

    - Amostra/Outro: sem piso de minutos, exigem estágio de engenharia.
    - LMP: >= min_residence_minutes (ou bypass por âncora de amostra
      quando não strict).
    """
    if listing_kind in (LISTING_KIND_SAMPLE, LISTING_KIND_OTHER):
        return has_engineering_stage
    if listing_kind != LISTING_KIND_LMP:
        return True
    if total_minutes >= min_residence_minutes:
        return True
    if strict_residence_after_homolog and has_lmp_finalized:
        return False
    return has_sample_anchor
