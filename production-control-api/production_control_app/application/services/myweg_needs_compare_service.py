"""Comparação JWT MyWEG entre dois lotes + faturamento indicativo opcional."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

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
SAO_PAULO = ZoneInfo("America/Sao_Paulo")
LIST_PAGE_SIZE = 100
LIST_MAX_PAGES = 20


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
        changes_only: bool = True,
    ) -> dict[str, Any]:
        self._assert_can_view(user)
        mode = (billing_mode or "none").strip().lower()
        if mode not in {"none", "indicative"}:
            raise MyWegNeedsValidationFailed(
                "billingMode inválido. Use none|indicative.",
                issues=[{"code": "invalid_record", "message": "billingMode", "path": "billingMode"}],
            )

        from_batch, to_batch = self._resolve_pair(from_batch_id, to_batch_id)
        self._assert_chronological_order(from_batch, to_batch)

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
                from_batch=from_batch,
                to_batch=to_batch,
            )

        changes = observed["changes"]
        total_compared = len(changes)
        total_changes = sum(1 for row in changes if row.get("movement") != "unchanged")

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

        if changes_only:
            changes = [row for row in changes if row.get("movement") != "unchanged"]

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
            "totalCompared": total_compared,
            "totalChanges": total_changes,
            "changesOnly": bool(changes_only),
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

        # Default: duas últimas datas operacionais distintas (não o mesmo dia).
        items = self._list_batches_for_pairing()
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
        to_day = self._collection_date(to_batch)
        from_batch = None
        for candidate in items[1:]:
            if self._collection_date(candidate) != to_day:
                from_batch = candidate
                break
        if from_batch is None:
            raise MyWegNeedsValidationFailed(
                "Dados insuficientes para comparação diária automática: "
                "só há coletas na mesma data operacional. "
                "Selecione manualmente duas coletas (mesmo dia permitido).",
                issues=[
                    {
                        "code": "insufficient_operational_days",
                        "message": "Sem datas operacionais distintas para o par automático.",
                        "path": "batches",
                    }
                ],
            )
        return from_batch, to_batch

    def _list_batches_for_pairing(self) -> list[dict[str, Any]]:
        """Percorre páginas suficientes — não limita a 50 registros históricos."""
        collected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for page in range(1, LIST_MAX_PAGES + 1):
            listing = self._repository.list_batches(page=page, page_size=LIST_PAGE_SIZE)
            items = list(listing.get("items") or [])
            if not items:
                break
            for item in items:
                batch_id = str(item.get("id") or "")
                if not batch_id or batch_id in seen_ids:
                    continue
                seen_ids.add(batch_id)
                collected.append(item)
            total = int(listing.get("total") or 0)
            if len(collected) >= total or len(items) < LIST_PAGE_SIZE:
                break
        return collected

    def _assert_chronological_order(
        self,
        from_batch: dict[str, Any],
        to_batch: dict[str, Any],
    ) -> None:
        if str(from_batch.get("id")) == str(to_batch.get("id")):
            raise MyWegNeedsValidationFailed(
                "Coleta anterior e atual não podem ser a mesma.",
                issues=[
                    {
                        "code": "same_batch",
                        "message": "fromBatchId e toBatchId são iguais.",
                        "path": "fromBatchId",
                    }
                ],
            )
        from_at = self._collected_at(from_batch)
        to_at = self._collected_at(to_batch)
        if from_at >= to_at:
            raise MyWegNeedsValidationFailed(
                "Ordem cronológica inválida: a coleta anterior deve ser "
                "estritamente anterior à coleta atual (collected_at).",
                issues=[
                    {
                        "code": "chronological_order_invalid",
                        "message": (
                            f"from collected_at={from_at.isoformat()} "
                            f"não é anterior a to collected_at={to_at.isoformat()}"
                        ),
                        "path": "fromBatchId",
                    }
                ],
            )

    def _load_indicative_billing(
        self,
        *,
        previous: dict,
        current: dict,
        from_batch: dict[str, Any],
        to_batch: dict[str, Any],
    ) -> dict[str, Any]:
        window = self.resolve_fiscal_window(from_batch, to_batch)
        product_codes = sorted(
            {
                (need.verified_product_code or "").strip()
                for need in list(previous.values()) + list(current.values())
                if (need.verified_product_code or "").strip()
                and need.key.identity_kind == "verified_code"
            }
        )
        base_meta = {
            "period": {"start": window["start"], "end": window["end"]},
            "periodCriterion": window["criterion"],
            "periodTimezone": window["timezone"],
            "periodGranularity": window["granularity"],
            "cutoffUncertainty": window["cutoffUncertainty"],
            "periodLimitations": window["limitations"],
        }
        if not product_codes:
            return {
                **base_meta,
                "status": "unavailable",
                "reason": "no_verified_product_codes",
                "disclaimer": (
                    "Faturamento indicativo indisponível: nenhum código DELPI verificado "
                    "nas coletas. Não interpretar como faturamento zero."
                ),
                "totalsByProduct": [],
                "incompatibleProducts": [],
                "fifoScenarios": [],
                "indicativeProducts": [],
                "coverage": None,
            }
        try:
            payload = self._gateway.list_customer_outbound_invoice_line_items(
                branch=ALLOWED_BRANCH,
                customer_code=WEG_CUSTOMER_CODE,
                customer_store=WEG_CUSTOMER_STORE,
                issue_date_start=window["start"],
                issue_date_end=window["end"],
                product_codes=product_codes,
                exclude_returns=True,
            )
            data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            totals_raw = list(data.get("totals_by_product") or [])
            billing_by_product: dict[str, Decimal] = {}
            totals_out: list[dict[str, Any]] = []
            incompatible: list[dict[str, Any]] = []
            for row in totals_raw:
                code = str(row.get("product_code") or "").strip()
                if not code:
                    continue
                unit = self._normalize_unit(row.get("unit") or row.get("invoice_unit"))
                original_units = [
                    self._normalize_unit(u)
                    for u in (row.get("original_units") or ([unit] if unit else []))
                    if self._normalize_unit(u)
                ]
                raw_quantity = row.get("quantity")
                raw_quantity_str = (
                    None if raw_quantity is None or raw_quantity == "" else str(raw_quantity)
                )
                # Autoridade FIFO: quantity_un do owner fiscal (já normalizado). Sem reconversão.
                quantity_un_raw = row.get("quantity_un")
                if quantity_un_raw is not None and str(quantity_un_raw).strip() != "":
                    quantity_un = str(quantity_un_raw).strip()
                    contract_comparable = bool(row.get("comparable", True))
                elif unit in {"UN", "UN."} and raw_quantity_str is not None:
                    # Fallback legado pré-normalização MI (somente UN bruto).
                    quantity_un = raw_quantity_str
                    contract_comparable = True
                else:
                    quantity_un = None
                    contract_comparable = bool(row.get("comparable", False))
                comparable = contract_comparable and quantity_un is not None
                entry = {
                    "productCode": code,
                    "quantityUn": quantity_un if comparable else None,
                    "quantity": raw_quantity_str,
                    "unit": unit or (original_units[0] if original_units else None),
                    "originalUnits": original_units or None,
                    "normalizedUnit": row.get("normalized_unit") or ("UN" if comparable else None),
                    "conversionFactor": (
                        str(row.get("conversion_factor"))
                        if row.get("conversion_factor") is not None
                        else None
                    ),
                    "comparable": comparable,
                    "reason": None
                    if comparable
                    else (
                        str(row.get("incompatibility_reason") or "").strip()
                        or (
                            "quantity_un ausente no contrato fiscal; "
                            "não usar quantity bruto em MI."
                            if unit == "MI"
                            else f"Unidade fiscal '{unit or '?'}' incompatível com necessidade em UN."
                        )
                    ),
                }
                if comparable:
                    # Nunca multiplicar de novo — quantity_un já está em UN.
                    billing_by_product[f"code:{code}"] = Decimal(quantity_un)
                    totals_out.append(entry)
                else:
                    incompatible.append(entry)

            scenarios = [
                scenario
                for scenario in build_product_fifo_scenarios(
                    previous, current, billing_by_product
                )
                if Decimal(str(scenario.get("candidateQuantityUn") or "0")) > 0
            ]
            indicative = self._build_indicative_products(
                previous=previous,
                current=current,
                totals_out=totals_out,
                scenarios=scenarios,
                incompatible=incompatible,
            )

            if not totals_out and not incompatible:
                status = "empty"
                disclaimer = (
                    "Nenhum faturamento candidato no período fiscal das coletas. "
                    "Não interpretar como zero de faturamento histórico amplo."
                )
            elif totals_out and incompatible:
                status = "partial"
                disclaimer = (
                    "Faturamento candidato parcial: alguns produtos com unidade "
                    "incompatível foram excluídos do FIFO. Cenário hipotético — "
                    "não comprova abatimento reconhecido pela WEG."
                )
            elif incompatible and not totals_out:
                status = "incompatible_units"
                disclaimer = (
                    "Itens fiscais encontrados, mas unidades incompatíveis com a "
                    "necessidade em UN. FIFO não aplicado. Não interpretar como zero."
                )
            else:
                status = "indicative"
                disclaimer = (
                    "Faturamento candidato obtido na api-delpi para a janela das coletas. "
                    "Pode ainda não ter sido reconhecido pela WEG. O cenário FIFO é "
                    "hipotético e não altera a programação observada."
                )

            return {
                **base_meta,
                "status": status,
                "totalsByProduct": totals_out,
                "incompatibleProducts": incompatible,
                "itemCount": int(data.get("returned_item_count") or 0),
                "coverage": data.get("coverage"),
                "fifoScenarios": scenarios,
                "indicativeProducts": indicative,
                "disclaimer": disclaimer,
            }
        except DelpiGatewayError as exc:
            logger.warning("Faturamento indicativo indisponível: %s", exc)
            return {
                **base_meta,
                "status": "unavailable",
                "reason": "api_delpi_error",
                "message": str(exc),
                "disclaimer": (
                    "Consulta fiscal falhou. A comparação observada permanece válida. "
                    "Não interpretar como faturamento zero."
                ),
                "totalsByProduct": [],
                "incompatibleProducts": [],
                "fifoScenarios": [],
                "indicativeProducts": [],
                "coverage": None,
            }

    @classmethod
    def resolve_fiscal_window(
        cls,
        from_batch: dict[str, Any],
        to_batch: dict[str, Any],
    ) -> dict[str, Any]:
        """Janela fiscal candidata determinada pelo par de coletas (não por 'hoje').

        Conservadora / dia de emissão:
        - WEG atualiza à tarde; DELPI costuma coletar na manhã seguinte.
        - Cutoff WEG exato desconhecido → granularidade diária + incerteza explícita.
        - Dias distintos: [collection_date(from), collection_date(to) - 1 dia].
        - Mesmo dia (manual): apenas aquele dia.
        - Sem lookback fixo de 45 dias; sem notas após o fim do ciclo analisado.
        """
        from_date = cls._collection_date(from_batch)
        to_date = cls._collection_date(to_batch)
        if from_date == to_date:
            start = end = from_date
            criterion = "same_day_manual_pair_day_granularity"
        else:
            start = from_date
            end = to_date - timedelta(days=1)
            if end < start:
                end = start
            criterion = (
                "pair_bound_from_collection_date_to_day_before_to_collection"
            )
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "criterion": criterion,
            "timezone": "America/Sao_Paulo",
            "granularity": "issue_date_day",
            "cutoffUncertainty": (
                "Cutoff exato do fechamento da programação WEG (tarde) é desconhecido. "
                "Aproximação temporal: collection_date das coletas DELPI (manhã típica) "
                "em America/Sao_Paulo; não confundir horário de coleta com fechamento WEG."
            ),
            "limitations": [
                "Não presume que todas as notas do intervalo foram reconhecidas pela WEG.",
                "Não inclui emissão fora da janela do par (sem lookback fixo de 45 dias).",
                "Diferença residual FIFO não é alteração confirmada da demanda.",
            ],
        }

    @staticmethod
    def _build_indicative_products(
        *,
        previous: dict,
        current: dict,
        totals_out: list[dict[str, Any]],
        scenarios: list[dict[str, Any]],
        incompatible: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        scenario_by_product = {s["productKey"]: s for s in scenarios}
        rows: list[dict[str, Any]] = []

        def _sum_need(bucket: dict, product_key: str) -> Decimal:
            return sum(
                (
                    need.quantity_un
                    for key, need in bucket.items()
                    if key.product_key == product_key
                ),
                Decimal("0"),
            )

        for entry in totals_out:
            product_key = f"code:{entry['productCode']}"
            scenario = scenario_by_product.get(product_key)
            prev_total = _sum_need(previous, product_key)
            curr_total = _sum_need(current, product_key)
            applied = Decimal(str((scenario or {}).get("appliedQuantityUn") or "0"))
            hyp_total = sum(
                (
                    Decimal(str(r.get("hypotheticalQuantityUn") or "0"))
                    for r in (scenario or {}).get("rows") or []
                ),
                Decimal("0"),
            )
            residual = curr_total - hyp_total
            original_label = None
            if entry.get("quantity") is not None and entry.get("unit"):
                original_label = f"{entry['quantity']} {entry['unit']}"
            elif entry.get("originalUnits"):
                original_label = ", ".join(entry["originalUnits"])
            rows.append(
                {
                    "productCode": entry["productCode"],
                    "unit": entry.get("normalizedUnit") or "UN",
                    "originalUnit": entry.get("unit"),
                    "originalQuantity": entry.get("quantity"),
                    "originalFiscalLabel": original_label,
                    "conversionFactor": entry.get("conversionFactor"),
                    "candidateQuantityUn": entry.get("quantityUn"),
                    "previousNeedUn": str(prev_total),
                    "currentNeedUn": str(curr_total),
                    "hypotheticallyAbatedUn": str(applied),
                    "fifoExpectedBalanceUn": str(hyp_total),
                    "residualVsCurrentUn": str(residual),
                    "comparable": True,
                    "fifoAvailable": scenario is not None,
                }
            )

        for entry in incompatible:
            product_key = f"code:{entry['productCode']}"
            rows.append(
                {
                    "productCode": entry["productCode"],
                    "unit": entry.get("unit"),
                    "originalUnit": entry.get("unit"),
                    "originalQuantity": entry.get("quantity"),
                    "originalFiscalLabel": (
                        f"{entry['quantity']} {entry['unit']}"
                        if entry.get("quantity") is not None and entry.get("unit")
                        else None
                    ),
                    "conversionFactor": entry.get("conversionFactor"),
                    "candidateQuantityUn": None,
                    "previousNeedUn": str(_sum_need(previous, product_key)),
                    "currentNeedUn": str(_sum_need(current, product_key)),
                    "hypotheticallyAbatedUn": None,
                    "fifoExpectedBalanceUn": None,
                    "residualVsCurrentUn": None,
                    "comparable": False,
                    "fifoAvailable": False,
                    "reason": entry.get("reason"),
                }
            )

        rows.sort(
            key=lambda row: (
                0 if row.get("comparable") else 1,
                -abs(Decimal(str(row.get("residualVsCurrentUn") or "0"))),
                str(row.get("productCode") or ""),
            )
        )
        return rows

    @staticmethod
    def _normalize_unit(value: Any) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def _empty_billing(mode: str) -> dict[str, Any]:
        return {
            "status": "skipped" if mode == "none" else "unavailable",
            "reason": "billing_mode_none" if mode == "none" else None,
            "totalsByProduct": [],
            "incompatibleProducts": [],
            "fifoScenarios": [],
            "indicativeProducts": [],
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

    @classmethod
    def _collection_date(cls, batch: dict[str, Any]) -> date:
        value = batch.get("collection_date")
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        text = str(value or "").strip()
        if text:
            return date.fromisoformat(text[:10])
        return cls._collected_at(batch).astimezone(SAO_PAULO).date()

    @staticmethod
    def _collected_at(batch: dict[str, Any]) -> datetime:
        collected = batch.get("collected_at")
        if isinstance(collected, datetime):
            if collected.tzinfo is None:
                return collected.replace(tzinfo=SAO_PAULO)
            return collected.astimezone(SAO_PAULO)
        text = str(collected or "").strip()
        if not text:
            # fallback: collection_date at midnight SP
            day = batch.get("collection_date")
            day_text = day.isoformat()[:10] if isinstance(day, date) else str(day or "")[:10]
            return datetime.fromisoformat(f"{day_text}T00:00:00").replace(tzinfo=SAO_PAULO)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=SAO_PAULO)
        return parsed.astimezone(SAO_PAULO)

    @staticmethod
    def _assert_can_view(user: object | None) -> None:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        if not can(user, PC_MYWEG_NEEDS_VIEW):
            raise PermissionError("Você não tem permissão para consultar Necessidades WEG.")
        if not can(user, PC_VIEW_FILIAL_02):
            raise BranchAccessDenied("Sem permissão para a filial 02.")
