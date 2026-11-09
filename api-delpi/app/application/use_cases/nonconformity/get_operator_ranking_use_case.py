"""Ranking de NCs (#1538): reincidência, quantidade rejeitada, descrição."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation

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


def _quantity(value: object) -> Decimal:
    if value is None:
        return Decimal(0)
    try:
        number = Decimal(str(value))
        return number if number.is_finite() else Decimal(0)
    except (InvalidOperation, ValueError):
        return Decimal(0)


def build_operator_ranking(
    rows: list[dict],
    *,
    selected_code: str | None = None,
    resolve_name=resolve_nc_operator_name,
    include_all: bool = False,
) -> dict:
    """Ordenação de defeitos: reincidência DESC, QI2_QTDDEV DESC, nome ASC.

    A API normal consulta nomes somente no Top 5 + operador selecionado;
    a exportação resolve todos os nomes para não mostrar matrículas sem nome.
    A falha no Portal RH não elimina as ocorrências do Protheus.
    """
    counts: dict[str, int] = defaultdict(int)
    quantities: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    defects: dict[str, dict[str, dict]] = defaultdict(dict)

    for row in rows:
        code = str(row.get("operator_code") or "").strip()
        if not code:
            continue
        defect = str(row.get("defect") or "").strip() or "Não informado"
        n = int(row.get("nc_count") or 0)
        if n <= 0:
            continue
        rejected = _quantity(row.get("rejected_quantity"))
        counts[code] += n
        quantities[code] += rejected
        bucket = defects[code].setdefault(
            defect, {"count": 0, "rejected_quantity": Decimal(0)}
        )
        bucket["count"] += n
        bucket["rejected_quantity"] += rejected

    ordered = sorted(counts, key=lambda code: (-counts[code], code))
    if selected_code is not None and selected_code not in counts:
        raise ValueError("Operador não encontrado no período e filtros selecionados.")

    to_resolve = ordered if include_all else list(
        dict.fromkeys(ordered[:5] + ([selected_code] if selected_code else []))
    )
    # Exporta todos os operadores; limitar paralelismo para proteger o Portal RH.
    if include_all and len(to_resolve) > 1:
        with ThreadPoolExecutor(max_workers=6) as pool:
            names = list(pool.map(resolve_name, to_resolve))
        name_cache = dict(zip(to_resolve, names))
    else:
        name_cache = {code: resolve_name(code) for code in to_resolve}

    def label(code: str) -> str:
        return name_cache.get(code) or f"Operador {code}"

    def sorted_defects(code: str):
        return sorted(
            defects[code].items(),
            key=lambda item: (
                -item[1]["count"],
                -item[1]["rejected_quantity"],
                item[0].casefold(),
                item[0],
            ),
        )

    def summary(code: str) -> dict:
        desc, main = sorted_defects(code)[0]
        return {
            "operator_code": code,
            "operator_name": label(code),
            "total_ncs": counts[code],
            "total_rejected_quantity": float(quantities[code]),
            "defect_types_count": len(defects[code]),
            "main_defect": desc,
            "main_defect_count": main["count"],
            "main_defect_rejected_quantity": float(main["rejected_quantity"]),
        }

    ranking = [summary(code) for code in ordered[:5]]
    selected = selected_code or (ordered[0] if ordered else None)
    detail = None
    if selected:
        distribution = sorted_defects(selected)
        detail = {
            "operator_code": selected,
            "operator_name": label(selected),
            "total_ncs": counts[selected],
            "total_rejected_quantity": float(quantities[selected]),
            "defect_types_count": len(distribution),
            "defects": [
                {
                    "description": description,
                    "count": values["count"],
                    "rejected_quantity": float(values["rejected_quantity"]),
                }
                for description, values in distribution
            ],
        }

    result = {
        "ranking": ranking,
        "operators": [
            {"operator_code": code, "operator_name": label(code)}
            for code in ordered
        ],
        "detail": detail,
        "total_operators": len(ordered),
    }
    if include_all:
        result["all_rows"] = [summary(code) for code in ordered]
        result["defect_rows"] = [
            {
                "operator_code": code,
                "operator_name": label(code),
                "defect": description,
                "nc_count": values["count"],
                "rejected_quantity": float(values["rejected_quantity"]),
                "is_main_defect": index == 0,
            }
            for code in ordered
            for index, (description, values) in enumerate(sorted_defects(code))
        ]
    return result


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
    include_all: bool = False,
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
        include_all=include_all,
    )
