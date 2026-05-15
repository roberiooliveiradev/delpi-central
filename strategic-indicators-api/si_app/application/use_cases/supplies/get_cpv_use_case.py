from si_app.application.dto.supplies.get_cpv_request import GetCPVRequest
from si_app.application.dto.financial.get_rol_request import GetRolRequest
from si_app.domain.ports.supplies.cpv_query_repository_port import CpvQueryRepositoryPort
from si_app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort


class GetCPVUseCase:

    def __init__(
        self,
        cpv_repository: CpvQueryRepositoryPort,
        financial_repository: FinancialQueryRepositoryPort,
    ):
        self._cpv_repository = cpv_repository
        self._financial_repository = financial_repository

    def execute(self, request: GetCPVRequest) -> dict:
        summary = self._cpv_repository.get_cpv_summary(request)
        by_cfop = self._cpv_repository.get_cpv_by_cfop(request)
        by_tm = self._cpv_repository.get_cpv_by_tm(request)
        top_products = self._cpv_repository.get_cpv_top_products(request)
        top_documents = self._cpv_repository.get_cpv_top_documents(request)

        rol_request = GetRolRequest(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        rol_data = self._financial_repository.get_rol(rol_request)

        cpv_total = float(summary.get("cpv_total") or 0)
        rol_with_ipi = float(rol_data.get("rol_with_ipi") or 0)
        total_movements = int(summary.get("total_movements") or 0)
        total_quantity = float(summary.get("total_quantity") or 0)

        cpv_percentage = (cpv_total / rol_with_ipi * 100) if rol_with_ipi > 0 else 0
        average_cost_per_movement = (cpv_total / total_movements) if total_movements > 0 else 0
        average_cost_per_unit = (cpv_total / total_quantity) if total_quantity > 0 else 0

        return {
            "branch": request.branch or "consolidated",
            "start_date": summary.get("start_date") or request.start_date or "",
            "end_date": summary.get("end_date") or request.end_date or "",
            "summary": {
                "cpv_total": cpv_total,
                "rol_with_ipi": rol_with_ipi,
                "cpv_percentage": cpv_percentage,
                "total_movements": total_movements,
                "total_quantity": total_quantity,
                "average_cost_per_movement": average_cost_per_movement,
                "average_cost_per_unit": average_cost_per_unit,
            },
            "financial_context": {
                "gross_revenue": rol_data.get("gross_revenue", 0),
                "returns": rol_data.get("returns", 0),
                "discounts": rol_data.get("discounts", 0),
                "rol": rol_data.get("rol", 0),
                "rol_with_ipi": rol_data.get("rol_with_ipi", 0),
                "ipi_separated": rol_data.get("ipi_separated", 0),
            },
            "by_cfop": by_cfop,
            "by_tm": by_tm,
            "top_products": top_products,
            "top_documents": top_documents,
        }