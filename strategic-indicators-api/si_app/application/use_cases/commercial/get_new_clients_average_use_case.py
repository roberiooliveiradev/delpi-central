from datetime import datetime

from si_app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from si_app.domain.ports.commercial.new_clients_average_repository_port import NewClientsAverageRepositoryPort


class GetNewClientsAverageUseCase:
    def __init__(
        self,
        new_clients_average_repository: NewClientsAverageRepositoryPort
    ):
        self._new_clients_average_repository = new_clients_average_repository

    def execute(self, request: NewClientsAverageRequest) -> dict:
        if (request.start_date and not request.end_date) or (request.end_date and not request.start_date):
            raise ValueError("start_date and end_date must be informed together.")

        if request.start_date and request.end_date:
            start = self._parse_date(request.start_date)
            end = self._parse_date(request.end_date)

            if start > end:
                raise ValueError("start_date cannot be greater than end_date.")

        indicator = self._new_clients_average_repository.get_new_clients_total(request)

        qtd_months = self._resolve_month_count(
            request=request,
            first_date=indicator.first_date,
            last_date=indicator.last_date,
            total_new_clients=indicator.total_new_clients,
        )

        monthly_average = round(indicator.total_new_clients / qtd_months, 2) if qtd_months > 0 else 0

        return {
            "branch": indicator.branch,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "total_new_clients": indicator.total_new_clients,
            "qtd_months": qtd_months,
            "monthly_average": monthly_average,
        }

    def _resolve_month_count(
        self,
        request: NewClientsAverageRequest,
        first_date: str | None,
        last_date: str | None,
        total_new_clients: int,
    ) -> int:
        if request.start_date and request.end_date:
            start = self._parse_date(request.start_date)
            end = self._parse_date(request.end_date)
            return self._calculate_months_in_range(start, end)

        if total_new_clients == 0 or not first_date or not last_date:
            return 0

        first = self._parse_date(first_date)
        last = self._parse_date(last_date)

        return self._calculate_months_in_range(first, last)

    def _calculate_months_in_range(self, start_date: datetime, end_date: datetime) -> int:
        return ((end_date.year - start_date.year) * 12) + (end_date.month - start_date.month) + 1

    def _parse_date(self, value: str) -> datetime:
        known_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y%m%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in known_formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception as exc:
            raise ValueError(f"Invalid date format: {value}") from exc