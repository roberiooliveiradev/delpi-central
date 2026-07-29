# app/application/use_cases/ppm/get_ppm_summary_use_case.py

from app.application.dto.production_appointments.produced_quantity_query_request import (
    ProducedQuantityQueryRequest,
)
from app.application.services.quality.ppm_query_cache import (
    get_cached_ppm_summary,
    ppm_summary_cache_key,
    set_cached_ppm_summary,
)
from app.application.use_cases.ppm.get_returned_quantity_use_case import (
    GetReturnedQuantityUseCase,
)
from app.application.use_cases.production_appointments.get_produced_quantity_use_case import (
    GetProducedQuantityUseCase,
)
from app.domain.entities.ppm.ppm_summary import PpmSummary
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort
from app.domain.production.production_appointments.production_appointments_scope import (
    DEFAULT_PRODUCED_PRODUCT_TYPES,
)


class GetPpmSummaryUseCase:

    def __init__(
        self,
        repository: PpmQueryRepositoryPort,
        produced_quantity_use_case: GetProducedQuantityUseCase,
        returned_quantity_use_case: GetReturnedQuantityUseCase | None = None,
    ):
        self._repository = repository
        self._produced_quantity = produced_quantity_use_case
        self._returned_quantity = returned_quantity_use_case or GetReturnedQuantityUseCase(
            repository
        )

    def execute(self, request):
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        if not request.date_start or not request.date_end:
            raise ValueError("date_start e date_end são obrigatórios.")

        cache_key = ppm_summary_cache_key(request)
        cached = get_cached_ppm_summary(cache_key)
        if cached is not None:
            return cached

        returned = self._returned_quantity.get_totals(request)
        produced = self._produced_quantity.get_totals(
            ProducedQuantityQueryRequest.create(
                date_start=request.date_start,
                date_end=request.date_end,
                branch=request.branch,
                product_types=sorted(DEFAULT_PRODUCED_PRODUCT_TYPES),
            )
        )
        milheiro = float(produced.get("qty_produced_milheiro") or 0)
        un = float(produced.get("qty_produced_un") or 0)
        devolvido = float(returned.get("qty_returned_un") or 0)
        ppm = 0.0 if un == 0 else (devolvido / un) * 1_000_000.0

        summary = PpmSummary(
            type=request.type,
            branch=request.branch,
            start_date=request.date_start,
            end_date=request.date_end,
            total_devolvido_un=devolvido,
            total_produzido_milheiro=milheiro,
            total_produzido_un=un,
            ppm=ppm,
        )
        set_cached_ppm_summary(cache_key, summary)
        return summary

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        if ppm_type not in {"internal", "external"}:
            raise ValueError("ppm_type deve ser internal ou external")

        if not hasattr(self._repository, "list_branches"):
            return []

        return self._repository.list_branches(
            ppm_type=ppm_type,
            date_start=date_start,
            date_end=date_end,
        )
