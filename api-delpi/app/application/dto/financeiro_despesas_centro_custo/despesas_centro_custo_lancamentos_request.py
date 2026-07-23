from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DespesasCentroCustoQueryRequest,
)

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

DEFAULT_SORT_BY = "data_emissao"
DEFAULT_SORT_DIR = "desc"

VALID_SORT_BY = frozenset(
    {
        "data_emissao",
        "documento",
        "razao_social",
        "centro_custo_codigo",
        "centro_custo_descricao",
        "produto_codigo",
        "produto_descricao",
        "valor_total",
    }
)
VALID_SORT_DIR = frozenset({"asc", "desc"})


@dataclass(frozen=True, slots=True)
class DespesasCentroCustoLancamentosRequest:
    start_date: str
    end_date: str
    branch: str | None = None
    cost_center: str | None = None
    supplier_code: str | None = None
    supplier_store: str | None = None
    search: str | None = None
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str = DEFAULT_SORT_BY
    sort_dir: str = DEFAULT_SORT_DIR

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        search: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort_by: str = DEFAULT_SORT_BY,
        sort_dir: str = DEFAULT_SORT_DIR,
    ) -> DespesasCentroCustoLancamentosRequest:
        base = DespesasCentroCustoQueryRequest.from_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
        )
        normalized_sort_by = str(sort_by or DEFAULT_SORT_BY).strip() or DEFAULT_SORT_BY
        normalized_sort_dir = str(sort_dir or DEFAULT_SORT_DIR).strip().lower() or DEFAULT_SORT_DIR

        if normalized_sort_by not in VALID_SORT_BY:
            raise ValueError(
                "sort_by inválido. Use um dos campos permitidos: "
                + ", ".join(sorted(VALID_SORT_BY))
                + "."
            )
        if normalized_sort_dir not in VALID_SORT_DIR:
            raise ValueError("sort_dir inválido. Use asc ou desc.")

        return cls(
            start_date=base.start_date,
            end_date=base.end_date,
            branch=base.branch,
            cost_center=base.cost_center,
            supplier_code=base.supplier_code,
            supplier_store=base.supplier_store,
            search=cls._normalize_optional_text(search),
            page=page,
            page_size=page_size,
            sort_by=normalized_sort_by,
            sort_dir=normalized_sort_dir,
        )

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    def resolve_protheus_period(self) -> tuple[str, str]:
        return DespesasCentroCustoQueryRequest(
            start_date=self.start_date,
            end_date=self.end_date,
            branch=self.branch,
        ).resolve_protheus_period()

    def resolve_page(self) -> int:
        return max(int(self.page), 1)

    def resolve_page_size(self) -> int:
        return min(max(int(self.page_size), 1), MAX_PAGE_SIZE)

    def periodo_dict(self) -> dict[str, str]:
        from app.application.services.response_date_format_service import (
            ResponseDateFormatService,
        )

        start, end = self.resolve_protheus_period()
        return {
            "data_inicio": ResponseDateFormatService.format_date(start) or start,
            "data_fim": ResponseDateFormatService.format_date(end) or end,
        }
