"""Comparação JWT MyWEG entre dois lotes + faturamento indicativo opcional."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_02,
    can,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    MyWegNeedsBatchNotFound,
    MyWegNeedsValidationFailed,
)
from production_control_app.domain.myweg_needs_contract import ALLOWED_BRANCH
from production_control_app.domain.services.myweg_needs_comparison import (
    aggregate_needs,
    build_product_fifo_scenarios,
    compare_aggregated,
)
from production_control_app.infrastructure.gateways.delpi_production_gateway import (
    DelpiProductionGateway,
)

logger = logging.getLogger(__name__)

WEG_CUSTOMER_CODE = "000001"
WEG_CUSTOMER_STORE = "09"
DEFAULT_BILLING_LOOKBACK_DAYS = 45


class MyWegNeedsCompareService:
    def __init__(
        self,
        repository: Any,
        gateway: DelpiProductionGateway | None = None,
    ) -> None:
        self._repository = repository
        self._gateway = gateway or DelpiProductionGateway(
            caller_app="production-control-myweg-compare"
        )

    def compare(
        self,
        user: object | None,
        *,
        from_batch_id: str | None,
        to_batch_id: str | None,
        billing_mode: str = "none",
        product_search: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        self._assert_can_view(user)
        mode = (billing_mode or "none").strip().lower()
        if mode not in {"none", "indicative"}:
            raise MyWegNeedsValidationFailed(
                "billingMode inválido. Use none|indicative.",
                issues=[{"code": "invalid_record", "message": "billingMode", "path": "billingMode"}],
            )

        from_batch, to_batch = self._resolve_pair(from_batch_id, to_batch_id)
        from_rows = self._repository.list_batch_records_for_compare(batch_id=from_batch["id"])
        to_rows = self._repository.list_batch_records_for_compare(batch_id=to_batch["id"])

        previous = aggregate_needs(from_rows)
        current = aggregate_needs(to_rows)
        reference_date = self._collection_date(to_batch)
        observed = compare_aggregated(
            previous, current, reference_date=reference_date
        )

        billing_block = self._empty_billing(mode)
        if mode == "indicative":
            billing_block = self._load_indicative_billing(
                previous=previous,
                current=current,
                reference_date=reference_date,
            )

        changes = observed["changes"]
        needle = (product_search or "").strip().lower()
        if needle:
            changes = [
                row
                for row in changes
                if needle in str(row.get("productKey") or "").lower()
                or needle in str(row.get("materialWegTratado") or "").lower()
                or needle in str(row.get("verifiedProductCode") or "").lower()
                or needle in str(row.get("codigoReferenciaWeg") or "").lower()
            ]
        # priorizar mudanças e horizonte
        changes = sorted(
            changes,
            key=lambda row: (
                0 if row.get("movement") != "unchanged" else 1,
                0 if row.get("inHorizon14d") else 1,
                str(row.get("productKey") or ""),
                str(row.get("remessa") or ""),
            ),
        )
        total = len(changes)
        page = max(1, int(page))
        page_size = min(200, max(1, int(page_size)))
        offset = (page - 1) * page_size
        page_items = changes[offset : offset + page_size]

        return {
            "branch": ALLOWED_BRANCH,
            "scope": {
                "customerName": "WEG Linhares Equipamentos Elétricos Ltda.",
                "protheusCustomerCode": WEG_CUSTOMER_CODE,
                "protheusCustomerStore": WEG_CUSTOMER_STORE,
                "mywegCompanyCode": "1009",
                "mywegWorkCenter": "1106",
            },
            "fromBatch": self._batch_summary(from_batch),
            "toBatch": self._batch_summary(to_batch),
            "observed": {
                "summary": observed["summary"],
                "probableDateShifts": observed["probableDateShifts"],
                "horizonDays": observed["horizonDays"],
                "referenceDate": observed["referenceDate"],
                "disclaimer": (
                    "Variação observada entre snapshots. Não comprova pedido cancelado, "
                    "demanda atendida nem abatimento reconhecido pela WEG."
                ),
            },
            "billing": billing_block,
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": page_items,
            "dataFreshness": {
                "comparedAt": datetime.now(timezone.utc).isoformat(),
                "billingMode": mode,
            },
        }

    def _resolve_pair(
        self,
        from_batch_id: str | None,
        to_batch_id: str | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if from_batch_id and to_batch_id:
            from_batch = self._repository.find_by_id(from_batch_id)
            to_batch = self._repository.find_by_id(to_batch_id)
            if from_batch is None or to_batch is None:
                raise MyWegNeedsBatchNotFound("Uma ou ambas as coletas não foram encontradas.")
            return from_batch, to_batch

        # Default: duas últimas coletas por collected_at em dias distintos quando possível.
        listing = self._repository.list_batches(page=1, page_size=50)
        items = list(listing.get("items") or [])
        if len(items) < 2:
            raise MyWegNeedsValidationFailed(
                "Dados insuficientes: é necessário pelo menos duas coletas aceitas.",
                issues=[
                    {
                        "code": "insufficient_batches",
                        "message": "Apenas uma coleta válida (ou nenhuma).",
                        "path": "batches",
                    }
                ],
            )
        to_batch = items[0]
        from_batch = None
        to_day = self._collection_date(to_batch)
        for candidate in items[1:]:
            if self._collection_date(candidate) != to_day:
                from_batch = candidate
                break
        if from_batch is None:
            from_batch = items[1]
        return from_batch, to_batch

    def _load_indicative_billing(
        self,
        *,
        previous: dict,
        current: dict,
        reference_date: date,
    ) -> dict[str, Any]:
        product_codes = sorted(
            {
                (need.verified_product_code or "").strip()
                for need in list(previous.values()) + list(current.values())
                if (need.verified_product_code or "").strip()
                and need.key.identity_kind == "verified_code"
            }
        )
        start = (reference_date - timedelta(days=DEFAULT_BILLING_LOOKBACK_DAYS)).isoformat()
        end = reference_date.isoformat()
        if not product_codes:
            return {
                "status": "unavailable",
                "reason": "no_verified_product_codes",
                "disclaimer": (
                    "Faturamento indicativo indisponível: nenhum código DELPI verificado "
                    "nas coletas. Não interpretar como faturamento zero."
                ),
                "totalsByProduct": [],
                "fifoScenarios": [],
                "coverage": None,
            }
        try:
            payload = self._gateway.list_customer_outbound_invoice_line_items(
                branch=ALLOWED_BRANCH,
                customer_code=WEG_CUSTOMER_CODE,
                customer_store=WEG_CUSTOMER_STORE,
                issue_date_start=start,
                issue_date_end=end,
                product_codes=product_codes,
                exclude_returns=True,
            )
            data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            totals_raw = list(data.get("totals_by_product") or [])
            billing_by_product = {
                f"code:{row['product_code']}": Decimal(str(row.get("quantity") or "0"))
                for row in totals_raw
                if row.get("product_code")
            }
            scenarios = build_product_fifo_scenarios(
                previous, current, billing_by_product
            )
            return {
                "status": "indicative",
                "period": {"start": start, "end": end},
                "totalsByProduct": [
                    {
                        "productCode": row.get("product_code"),
                        "quantityUn": str(row.get("quantity") or "0"),
                    }
                    for row in totals_raw
                ],
                "itemCount": int(data.get("returned_item_count") or 0),
                "coverage": data.get("coverage"),
                "fifoScenarios": scenarios,
                "disclaimer": (
                    "Faturamento candidato obtido na api-delpi. Pode ainda não ter sido "
                    "reconhecido pela WEG. O cenário FIFO é hipotético e não altera a "
                    "programação observada."
                ),
            }
        except DelpiGatewayError as exc:
            logger.warning("Faturamento indicativo indisponível: %s", exc)
            return {
                "status": "unavailable",
                "reason": "api_delpi_error",
                "message": str(exc),
                "disclaimer": (
                    "Consulta fiscal falhou. A comparação observada permanece válida. "
                    "Não interpretar como faturamento zero."
                ),
                "totalsByProduct": [],
                "fifoScenarios": [],
                "coverage": None,
            }

    @staticmethod
    def _empty_billing(mode: str) -> dict[str, Any]:
        return {
            "status": "skipped" if mode == "none" else "unavailable",
            "reason": "billing_mode_none" if mode == "none" else None,
            "totalsByProduct": [],
            "fifoScenarios": [],
            "disclaimer": (
                "Modo fiscal desligado (billingMode=none)."
                if mode == "none"
                else "Faturamento indicativo não carregado."
            ),
        }

    @staticmethod
    def _batch_summary(batch: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": batch["id"],
            "collectionId": batch["collection_id"],
            "collectedAt": batch.get("collected_at"),
            "collectionDate": batch.get("collection_date"),
            "importedAt": batch.get("imported_at"),
            "recordCount": int(batch.get("record_count") or 0),
            "payloadSha256": batch.get("payload_sha256"),
        }

    @staticmethod
    def _collection_date(batch: dict[str, Any]) -> date:
        value = batch.get("collection_date")
        if isinstance(value, date):
            return value
        text = str(value or "").strip()
        if text:
            return date.fromisoformat(text[:10])
        collected = batch.get("collected_at")
        if isinstance(collected, datetime):
            return collected.date()
        return date.fromisoformat(str(collected)[:10])

    @staticmethod
    def _assert_can_view(user: object | None) -> None:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        if not can(user, PC_MYWEG_NEEDS_VIEW):
            raise PermissionError("Você não tem permissão para consultar Necessidades WEG.")
        if not can(user, PC_VIEW_FILIAL_02):
            raise BranchAccessDenied("Sem permissão para a filial 02.")
