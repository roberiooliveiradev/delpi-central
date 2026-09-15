from typing import Optional

from app.application.use_cases.eficiencia_fabril.get_eficiencia_fabril_appointments_use_case import (
    GetEficienciaFabrilAppointmentsUseCase,
)
from app.domain.production.eficiencia_fabril_efficiency_by_work_center import (
    aggregate_efficiency_by_work_center_and_day,
)

_GRANULARITY_DAY = "day"


class GetEficienciaFabrilEfficiencySeriesUseCase:
    """Série diária de eficiência por CT — mesma regra da média por CT (OK + faixa 0–199%)."""

    def __init__(self, appointments_use_case: GetEficienciaFabrilAppointmentsUseCase):
        self._appointments = appointments_use_case

    def execute(
        self,
        *,
        date_start: Optional[str],
        date_end: Optional[str],
        branch: Optional[str] = None,
        op: Optional[str] = None,
        employee: Optional[str] = None,
        work_center: Optional[str] = None,
        shift: Optional[str] = None,
        granularity: str = _GRANULARITY_DAY,
    ) -> list[dict]:
        normalized = str(granularity or _GRANULARITY_DAY).strip().lower()
        if normalized != _GRANULARITY_DAY:
            raise ValueError('granularity inválida. Valor aceito: "day".')

        items = self._appointments.execute(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            op=op,
            employee=employee,
            work_center=work_center,
            status_ok_only=True,
            shift=shift,
        )
        return aggregate_efficiency_by_work_center_and_day(items)
