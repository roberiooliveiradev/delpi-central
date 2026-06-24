from typing import Optional

from app.application.dto.eficiencia_fabril.get_eficiencia_fabril_dashboard_request import (
    GetEficienciaFabrilDashboardRequest,
)
from app.application.services.eficiencia_fabril.eficiencia_fabril_appointments_cache import (
    eficiencia_fabril_appointments_cache_key,
    get_cached_eficiencia_fabril_appointments,
    set_cached_eficiencia_fabril_appointments,
)
from app.domain.ports.eficiencia_fabril.eficiencia_fabril_query_repository_port import (
    EficienciaFabrilQueryRepositoryPort,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.persistence.totvs.eficiencia_fabril.eficiencia_fabril_query_settings import (
    EficienciaFabrilQuerySettings,
)


class GetEficienciaFabrilAppointmentsUseCase:
    def __init__(
        self,
        repository: EficienciaFabrilQueryRepositoryPort,
        settings: EficienciaFabrilQuerySettings | None = None,
    ):
        self._repository = repository
        self._settings = settings or EficienciaFabrilQuerySettings()
        self._utils = Utils()

    def execute(
        self,
        *,
        date_start: Optional[str],
        date_end: Optional[str],
        branch: Optional[str] = None,
        op: Optional[str] = None,
        employee: Optional[str] = None,
        work_center: Optional[str] = None,
        status_ok_only: bool = False,
    ) -> list[dict]:
        if not date_start or not str(date_start).strip():
            raise ValueError("date_start é obrigatório.")
        if not date_end or not str(date_end).strip():
            raise ValueError("date_end é obrigatório.")

        self._utils.validate_date_range(date_start, date_end)

        parsed_start = self._utils.parse_date(date_start)
        parsed_end = self._utils.parse_date(date_end)
        if parsed_start is None or parsed_end is None:
            raise ValueError("Datas inválidas. Use formatos como YYYY-MM-DD ou DD/MM/YYYY.")

        max_days = self._settings.max_date_range_days
        if (parsed_end - parsed_start).days > max_days:
            raise ValueError(f"Intervalo máximo permitido: {max_days} dias.")

        if branch and branch not in self._settings.branches:
            raise ValueError(
                f"branch inválida. Valores aceitos: {', '.join(self._settings.branches)}."
            )

        request = GetEficienciaFabrilDashboardRequest(
            date_start=parsed_start,
            date_end=parsed_end,
            branch=branch.strip() if branch else None,
            op=op.strip() if op else None,
            employee=employee.strip() if employee else None,
            work_center=work_center.strip() if work_center else None,
            status_ok_only=status_ok_only,
            page=1,
            page_size=1,
        )

        cache_key = eficiencia_fabril_appointments_cache_key(
            request,
            status_ok_only=status_ok_only,
        )
        cached = get_cached_eficiencia_fabril_appointments(cache_key)
        if cached is not None:
            return cached

        items = self._repository.get_appointments(request, status_ok_only=status_ok_only)
        result = [item.to_dict() for item in items]
        set_cached_eficiencia_fabril_appointments(cache_key, result)
        return result
