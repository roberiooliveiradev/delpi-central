"""Cobertura de série temporal (meses pedidos vs retornados) — módulo canônico."""

from __future__ import annotations


def build_series_coverage(
    *,
    months_requested: int,
    competences_requested: list[str],
    competences_returned: list[str],
) -> dict:
    returned_set = set(competences_returned)
    missing = [
        competence
        for competence in competences_requested
        if competence not in returned_set
    ]
    return {
        "months_requested": months_requested,
        "competences_requested": list(competences_requested),
        "competences_returned": list(competences_returned),
        "missing_competences": missing,
    }
