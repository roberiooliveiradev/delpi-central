from si_app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from si_app.domain.ports.commercial.sales_conversion_rate_repository_port import SalesConversionRateRepositoryPort


class GetSalesConversionRateUseCase:
    def __init__(
        self,
        sales_conversion_rate_repository: SalesConversionRateRepositoryPort
    ):
        self._sales_conversion_rate_repository = sales_conversion_rate_repository

    def execute(self, request: SalesConversionRateRequest) -> dict:
        indicator = self._sales_conversion_rate_repository.get_sales_conversion_rate(request)

        return {
            "branch": indicator.branch,
            "start_date": indicator.start_date,
            "end_date": indicator.end_date,
            "qtd_proposals": indicator.qtd_proposals,
            "qtd_won": indicator.qtd_won,
            "sales_conversion_rate_pct": indicator.sales_conversion_rate_pct,
        }