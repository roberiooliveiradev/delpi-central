"""Ranking de operadores com NC por descrição do defeito (#1538)."""

from __future__ import annotations

from collections import defaultdict

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.domain.services.quality.nonconformity_query_filter_service import (
    normalize_nonconformity_filter_type,
)
from app.infrastructure.gateways.portal_rh_nonconformity_operator_gateway import (
    resolve_nc_operator_name,
)
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_operator_ranking_repository import (
    NonconformityOperatorRankingRepository,
)


def build_operator_ranking(
    rows: list[dict],
    *,
    selected_code: str | None = None,
    resolve_name=resolve_nc_operator_name,
) -> dict:
    """Agrega todas as linhas da consulta, com nomes apenas para os 5 primeiros
    e o operador selecionado. Não altera a contagem quando não há nome no RH.
    """
    counts: dict[str, int] = defaultdict(int)
    defects: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        code = str(row.get("operator_code") or "").strip()
        if not code:
            continue
        defect = str(row.get("defect") or "").strip() or "Não informado"
        n = int(row.get("nc_count") or 0)
        if n <= 0:
            continue
        counts[code] += n
        defects[code][defect] += n

    ordered = sorted(counts, key=lambda code: (-counts[code], code))
    if selected_code is not None and selected_code not in counts:
        raise ValueError("Operador não encontrado no período e filtros selecionados.")

    name_cache: dict[str, str | None] = {}
    for code in set(ordered[:5] + ([selected_code] if selected_code else [])):
        if code:
            name_cache[code] = resolve_name(code)

    def label(code: str) -> str:
        return name_cache.get(code) or f"Operador {code}"

    def top_defect(code: str) -> str:
        return sorted(defects[code].items(), key=lambda item: (-item[1], item[0]))[0][0]

    ranking = [
        {
            "operator_code": code,
            "operator_name": label(code),
            "total_ncs": counts[code],
            "main_defect": top_defect(code),
        }
        for code in ordered[:5]
    ]
    selected = selected_code or (ordered[0] if ordered else None)
    detail = None
    if selected:
        distribution = sorted(
            defects[selected].items(), key=lambda item: (-item[1], item[0])
        )
        detail = {
            "operator_code": selected,
            "operator_name": label(selected),
            "total_ncs": counts[selected],
            "defect_types_count": len(distribution),
            "defects": [
                {"description": description, "count": quantity}
                for description, quantity in distribution
            ],
        }
    return {
        "ranking": ranking,
        "operators": [
            {"operator_code": code, "operator_name": label(code)}
            for code in ordered
        ],
        "detail": detail,
        "total_operators": len(ordered),
    }


def get_nonconformity_operator_ranking(
    *,
    type: str = "all",
    branch: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    status: str | None = None,
    item_code: str | None = None,
    description: str | None = None,
    operator_code: str | None = None,
) -> dict:
    code = operator_code.strip() if operator_code else None
    if code and len(code) > 30:
        raise ValueError("Código de operador inválido.")
    request = ListNonconformityRequest(
        type=normalize_nonconformity_filter_type(type),
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        status=status,
        item_code=item_code,
        description=description,
    )
    repository = NonconformityOperatorRankingRepository()
    return build_operator_ranking(
        repository.count_by_operator_and_defect(request),
        selected_code=code,
    )
