from datetime import date, datetime, timedelta

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)


class GetStockValueUseCase:

    def __init__(self, repository: StockValueQueryRepositoryPort):
        self._repository = repository

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

    def _resolve_period(self, request: GetStockValueRequest) -> tuple[str, str] | None:
        if not request.uses_historical_estimation:
            return None

        if not request.start_date or not request.end_date:
            raise ValueError(
                "Para consultar estoque em uma data passada, informe start_date e end_date."
            )

        start = self._parse_date(request.start_date)
        end = self._parse_date(request.end_date)

        if not start or not end:
            raise ValueError(
                "Para consultar estoque em uma data passada, informe start_date e end_date válidos."
            )

        if start > end:
            raise ValueError("start_date não pode ser maior que end_date.")

        period_start = start.strftime("%Y%m%d")
        period_end_exclusive = (end + timedelta(days=1)).strftime("%Y%m%d")
        return period_start, period_end_exclusive

    def execute(self, request: GetStockValueRequest) -> dict:
        period = self._resolve_period(request)
        bundle = self._repository.get_stock_value_bundle(request)

        summary = bundle.get("summary") or {}
        by_branch = bundle.get("by_branch") or []
        by_location = bundle.get("by_location") or []
        top_products = bundle.get("top_products") or []

        total_stock_value = float(summary.get("total_stock_value") or 0)
        total_stock_quantity = float(summary.get("total_stock_quantity") or 0)

        average_unit_value = (
            total_stock_value / total_stock_quantity
            if total_stock_quantity > 0
            else 0
        )

        payload = {
            "branch": summary.get("branch") or request.branch or "consolidated",
            "location": summary.get("location") or request.location or "all",
            "summary": {
                "total_stock_value": total_stock_value,
                "total_stock_quantity": total_stock_quantity,
                "total_records": int(summary.get("total_records") or 0),
                "total_products": int(summary.get("total_products") or 0),
                "total_locations": int(summary.get("total_locations") or 0),
                "average_unit_value": average_unit_value,
            },
            "by_branch": by_branch,
            "by_location": by_location,
            "top_products": top_products,
        }

        if period:
            period_start, period_end_exclusive = period
            end_date = self._parse_date(request.end_date)
            period_end = end_date.strftime("%Y%m%d") if end_date else None
            estimation_meta = bundle.get("estimation_meta") or {}
            stock_method_resolved = bundle.get("stock_method_resolved") or "estimated"
            stock_method_requested = (request.stock_method or "auto").strip().lower()

            if stock_method_resolved == "official_closure":
                method = "sb9_closure_on_end_date"
                note = (
                    "Valor do fechamento oficial SB9010 na data final do período. "
                    "Corresponde ao inventário contábil quando registrado na SB9."
                )
                data_quality_warning = None
            else:
                method = "sb9_last_closure_plus_sd3_movements"
                note = (
                    "Valor estimado a partir do último fechamento real em SB9010 "
                    "somado às movimentações líquidas em SD3010 (entrada se D3_TM < '500', "
                    "saída caso contrário). Não substitui fechamento oficial da SB9."
                )
                data_quality_warning = None
                stale_closure = False
                if period_end and estimation_meta.get("closing_base_date"):
                    stale_closure = str(estimation_meta.get("closing_base_date")) < period_end
                if stale_closure and not estimation_meta.get("official_closure_on_period_end"):
                    data_quality_warning = (
                        "Último fechamento SB9 anterior ao fim do período; a estimativa SD3 pode "
                        "divergir do Registro de Inventário até existir fechamento SB9 na data."
                    )

            payload["estimation"] = {
                "enabled": True,
                "method": method,
                "stock_method": stock_method_requested,
                "stock_method_resolved": stock_method_resolved,
                "start_date": period_start,
                "end_date": period_end,
                "end_date_exclusive": period_end_exclusive,
                "closing_base_date": estimation_meta.get("closing_base_date"),
                "closing_base_value": estimation_meta.get("closing_base_value"),
                "bridge_value": estimation_meta.get("bridge_value"),
                "period_net_value": estimation_meta.get("period_net_value"),
                "official_closure_available": estimation_meta.get(
                    "official_closure_available", False
                ),
                "official_closure_date": estimation_meta.get("official_closure_date"),
                "official_closure_value": estimation_meta.get("official_closure_value"),
                "official_closure_on_period_end": estimation_meta.get(
                    "official_closure_on_period_end", False
                ),
                "note": note,
            }
            if data_quality_warning:
                payload["estimation"]["data_quality_warning"] = data_quality_warning

        return payload
