# app/application/use_cases/lmp/get_lmp_use_case.py
from app.application.services.lmp_business_rules import LMPBusinessRules
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.application.dto.lmp.get_lmp_request import GetLMPRequest


class GetLMPUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetLMPRequest) -> dict:
        item = self._repository.get_lmp(request)
        payload = item.to_dict()

        nivel, sla_days, sla_minutes, data_limite, lead_time_util, status = (
            LMPBusinessRules.get_dashboard_status(
                start_date_str=item.start_date,
                end_date_str=item.end_date,
                qtd_pi=item.qtd_pi,
                engineering_status=item.engineering_status,
                engineering_total_minutes=item.engineering_total_minutes,
            )
        )

        payload["nivel"] = nivel
        payload["dias_uteis_sla"] = sla_days
        payload["sla_minutos"] = sla_minutes
        payload["data_limite"] = data_limite
        payload["lead_time_util"] = lead_time_util
        payload["status"] = status
        payload["list_history"] = []

        return payload