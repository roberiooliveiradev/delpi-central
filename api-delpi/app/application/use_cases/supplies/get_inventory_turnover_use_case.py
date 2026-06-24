from datetime import date, datetime, timedelta

from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_estimation_payload_service import (
    build_stock_estimation_payload,
)
from app.domain.ports.supplies.inventory_turnover_query_repository_port import (
    InventoryTurnoverQueryRepositoryPort,
)
from app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)


class GetInventoryTurnoverUseCase:

    def __init__(
        self,
        repository: InventoryTurnoverQueryRepositoryPort,
        stock_repository: StockValueQueryRepositoryPort,
    ):
        self._repository = repository
        self._stock_repository = stock_repository

    @staticmethod
    def _to_stock_request(request: GetInventoryTurnoverRequest) -> GetStockValueRequest:
        return GetStockValueRequest(
            branch=request.branch,
            location=request.location,
            start_date=request.start_date,
            end_date=request.end_date,
            summary_only=True,
        )

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None

        value = str(value).strip()
        formats = (
            "%Y%m%d",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        )

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        raise ValueError(
            "Data inválida. Use formatos como YYYYMMDD, YYYY-MM-DD ou DD-MM-YYYY."
        )

    def _last_day_of_month(self, value: date) -> date:
        if value.month == 12:
            return date(value.year + 1, 1, 1) - timedelta(days=1)
        return date(value.year, value.month + 1, 1) - timedelta(days=1)

    def _is_closed_month(self, start: date, end: date) -> bool:
        return (
            start.day == 1
            and end == self._last_day_of_month(end)
            and start.year == end.year
            and start.month == end.month
        )

    def _is_full_month_range(self, start: date, end: date) -> bool:
        current = date(start.year, start.month, 1)

        while current <= end:
            month_start = current
            month_end = self._last_day_of_month(current)

            if month_start < start or month_end > end:
                return False

            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return True

    def _months_in_range(self, start: date, end: date) -> int:
        return ((end.year - start.year) * 12) + (end.month - start.month) + 1

    def _days_in_range(self, start: date, end: date) -> int:
        return (end - start).days + 1

    def _is_valid_idd_period(self, start: date, end: date) -> bool:
        return self._is_closed_month(start, end) or self._is_full_month_range(start, end)

    def _resolve_cpv_average_monthly(
        self,
        cpv_total: float,
        start: date,
        end: date,
    ) -> tuple[float, str, int]:
        if self._is_closed_month(start, end):
            return cpv_total, "closed_month", 1

        if self._is_full_month_range(start, end):
            months = self._months_in_range(start, end)
            average = cpv_total / months if months > 0 else 0
            return average, "full_month_range", months

        days = self._days_in_range(start, end)
        average = (cpv_total / days) * 30 if days > 0 else 0
        return average, "partial_period_monthlyized", days

    def execute(self, request: GetInventoryTurnoverRequest) -> dict:
        stock_request = self._to_stock_request(request)
        stock_bundle = self._stock_repository.get_stock_value_bundle(stock_request)
        stock_context = stock_bundle.get("summary") or {}
        cpv_context = self._repository.get_cpv_context(request)

        total_stock_value = float(stock_context.get("total_stock_value") or 0)
        total_stock_quantity = float(stock_context.get("total_stock_quantity") or 0)
        cpv_total = float(cpv_context.get("cpv_total") or 0)

        start_raw = cpv_context.get("start_date") or request.start_date
        end_raw = cpv_context.get("end_date") or request.end_date

        start_date = self._parse_date(start_raw)
        end_date = self._parse_date(end_raw)

        if not start_date or not end_date:
            raise ValueError("start_date e end_date são obrigatórios para calcular giro de estoque.")

        if start_date > end_date:
            raise ValueError("start_date não pode ser maior que end_date.")

        idd_period_valid = self._is_valid_idd_period(start_date, end_date)

        if request.strict_idd_period and not idd_period_valid:
            raise ValueError(
                "Período inválido para o IDD. Use mês fechado ou intervalo composto apenas por meses completos."
            )

        cpv_average_monthly, calculation_mode, period_reference = self._resolve_cpv_average_monthly(
            cpv_total=cpv_total,
            start=start_date,
            end=end_date,
        )

        inventory_turnover_months = (
            total_stock_value / cpv_average_monthly
            if cpv_average_monthly > 0 else 0
        )

        inventory_turnover_times = (
            cpv_total / total_stock_value
            if total_stock_value > 0 else 0
        )

        average_unit_value = (
            total_stock_value / total_stock_quantity
            if total_stock_quantity > 0 else 0
        )

        payload = {
            "branch": stock_context.get("branch") or request.branch or "consolidated",
            "location": stock_context.get("location") or request.location or "all",
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "summary": {
                "inventory_turnover_months": inventory_turnover_months,
                "inventory_turnover_times": inventory_turnover_times,
                "total_stock_value": total_stock_value,
                "cpv_total": cpv_total,
                "cpv_average_monthly": cpv_average_monthly,
            },
            "calculation_context": {
                "calculation_mode": calculation_mode,
                "idd_period_valid": idd_period_valid,
                "strict_idd_period": request.strict_idd_period,
                "period_reference": period_reference,
            },
            "stock_context": {
                "total_stock_value": total_stock_value,
                "total_stock_quantity": total_stock_quantity,
                "total_records": int(stock_context.get("total_records") or 0),
                "total_products": int(stock_context.get("total_products") or 0),
                "total_locations": int(stock_context.get("total_locations") or 0),
                "average_unit_value": average_unit_value,
            },
            "cpv_context": {
                "cpv_total": cpv_total,
                "total_movements": int(cpv_context.get("total_movements") or 0),
                "total_quantity": float(cpv_context.get("total_quantity") or 0),
                "cpv_average_monthly": cpv_average_monthly,
            },
        }

        if stock_request.uses_historical_estimation:
            payload["stock_estimation"] = build_stock_estimation_payload(
                request=stock_request,
                bundle=stock_bundle,
                period_start=start_date.strftime("%Y%m%d"),
                period_end=end_date.strftime("%Y%m%d"),
                period_end_exclusive=(end_date + timedelta(days=1)).strftime("%Y%m%d"),
            )

        return payload