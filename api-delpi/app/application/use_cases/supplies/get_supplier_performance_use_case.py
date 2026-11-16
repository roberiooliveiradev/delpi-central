from datetime import date, datetime
import re
from zoneinfo import ZoneInfo

from app.domain.ports.query_cache_port import QueryCachePort
from app.domain.services.supplies.supplier_performance import (
    SupplierPerformanceReadPort,
    compose_supplier_performance,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES


def validate_supplier_performance_filters(branches, date_from, date_to):
    if not branches or any(
        branch not in PROTHEUS_BRANCH_CODES for branch in branches
    ):
        raise ValueError("Selecione uma filial válida (01 e/ou 02).")
    branches = sorted(set(branches))
    if not all(
        isinstance(value, str)
        and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
        for value in (date_from, date_to)
    ):
        raise ValueError("Informe datas válidas no formato AAAA-MM-DD.")
    try:
        start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
    except (ValueError, TypeError):
        raise ValueError("Informe datas válidas no formato AAAA-MM-DD.") from None
    if start > end or (end - start).days > 366:
        raise ValueError("O período deve ser crescente e ter no máximo 367 dias.")
    return branches, start, end


class GetSupplierPerformanceUseCase:
    def __init__(self, repository: SupplierPerformanceReadPort, cache: QueryCachePort):
        self._repository = repository
        self._cache = cache

    def execute(self, *, branches, date_from, date_to):
        branches, start, end = validate_supplier_performance_filters(branches, date_from, date_to)
        key = f"supplier-idf:v1:{','.join(branches)}:{start}:{end}"
        return self._cache.get_or_set(key, lambda: self._compose(branches, start, end))

    def _compose(self, branches, start, end):
        rows = self._repository.read_counts(
            branches=branches, date_from=start.isoformat(), date_to=end.isoformat()
        )
        result = compose_supplier_performance(rows)
        result.update(
            {
                "period": {"from": start.isoformat(), "to": end.isoformat()},
                "branches": branches,
                "calculated_at": datetime.now(
                    ZoneInfo("America/Sao_Paulo")
                ).isoformat(),
            }
        )
        return result
