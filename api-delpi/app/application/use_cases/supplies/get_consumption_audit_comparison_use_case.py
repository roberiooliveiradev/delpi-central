"""Comparação batch bounded de OPs — Auditoria de Consumo (GLPI #1353, F4).

Reusa ``GetConsumptionAuditOrderUseCase`` por OP (única fonte dos cálculos
Protheus) e projeta cada detalhe num item comparável: ordem, operações com
componentes (teórico × empenho × consumo classificado × diferença), totais
por unidade de medida e qualidade. OPs não encontradas saem em
``not_found`` — nunca como falha silenciosa nem como erro inventado.

``totals_by_unit`` soma somente componentes com a MESMA unidade de medida;
componentes sem UM reconhecida vão para a chave ``"unknown"`` e nunca são
misturados a UMs reais.
"""

from __future__ import annotations

from app.application.dto.supplies.get_consumption_audit_comparison_request import (
    GetConsumptionAuditComparisonRequest,
)
from app.application.dto.supplies.get_consumption_audit_order_request import (
    GetConsumptionAuditOrderRequest,
)
from app.application.use_cases.supplies.get_consumption_audit_order_use_case import (
    GetConsumptionAuditOrderUseCase,
)

_UNKNOWN_UOM = "unknown"


class GetConsumptionAuditComparisonUseCase:
    def __init__(self, detail_use_case: GetConsumptionAuditOrderUseCase):
        self._detail = detail_use_case

    def execute(self, request: GetConsumptionAuditComparisonRequest) -> dict:
        items: list[dict] = []
        not_found: list[str] = []

        for production_order in request.production_orders:
            detail = self._detail.execute(
                GetConsumptionAuditOrderRequest(
                    production_order=production_order,
                    branch=request.branch,
                )
            )
            if detail is None:
                not_found.append(production_order)
                continue
            items.append(self._project(detail))

        return {
            "branch": request.branch,
            "items": items,
            "not_found": not_found,
            "metadata": {
                "generated_at_source": "api-delpi",
                "comparison_rule": (
                    "per-component arithmetic projection; totals only within "
                    "the same unit_of_measure; no shortage inference"
                ),
                "contract_version": "a2-proposal-1",
            },
        }

    # ------------------------------------------------------------------
    # Projeção — apresentação do detalhe já calculado, sem nova regra
    # ------------------------------------------------------------------

    def _project(self, detail: dict) -> dict:
        operations: list[dict] = []
        totals: dict[str, dict] = {}

        for op in detail.get("operations") or []:
            components: list[dict] = []
            for comp in op.get("components") or []:
                uom = str(comp.get("unit_of_measure") or "").strip() or _UNKNOWN_UOM
                bom = comp.get("bom") or {}
                commitment = comp.get("commitment") or {}
                movements = comp.get("movements") or {}
                discrepancy = comp.get("discrepancy") or {}

                theoretical = bom.get("theoretical_quantity")
                original = float(commitment.get("original_quantity") or 0)
                open_qty = float(commitment.get("open_quantity") or 0)
                derived = float(commitment.get("derived_consumed_quantity") or 0)
                eligible = movements.get("eligible_consumption_quantity")

                bucket = totals.setdefault(
                    uom,
                    {
                        "unit_of_measure": None if uom == _UNKNOWN_UOM else uom,
                        "theoretical_quantity": 0.0,
                        "committed_quantity": 0.0,
                        "open_commitment_quantity": 0.0,
                        "derived_consumption_quantity": 0.0,
                        "eligible_consumption_quantity": 0.0,
                        "components": 0,
                    },
                )
                if theoretical is not None:
                    bucket["theoretical_quantity"] += float(theoretical)
                bucket["committed_quantity"] += original
                bucket["open_commitment_quantity"] += open_qty
                bucket["derived_consumption_quantity"] += derived
                if eligible is not None:
                    bucket["eligible_consumption_quantity"] += float(eligible)
                bucket["components"] += 1

                components.append(
                    {
                        "component_code": comp.get("component_code"),
                        "component_description": comp.get("component_description"),
                        "component_type": comp.get("component_type"),
                        "unit_of_measure": comp.get("unit_of_measure"),
                        "theoretical_quantity": theoretical,
                        "original_commitment_quantity": original,
                        "open_commitment_quantity": open_qty,
                        "derived_consumption_quantity": derived,
                        "eligible_consumption_quantity": eligible,
                        "difference": discrepancy.get("value"),
                        "classification": comp.get("classification"),
                        "quality_flags": comp.get("quality_flags") or [],
                    }
                )

            evidence = op.get("execution_evidence") or {}
            operations.append(
                {
                    "operation": op.get("operation"),
                    "work_center": op.get("work_center"),
                    "execution_state": evidence.get("execution_state"),
                    "components": components,
                }
            )

        return {
            "production_order": detail.get("production_order"),
            "branch": detail.get("branch"),
            "order": detail.get("order"),
            "operations": operations,
            "totals_by_unit": sorted(
                totals.values(),
                key=lambda row: (row["unit_of_measure"] is None, row["unit_of_measure"] or ""),
            ),
            "quality": detail.get("quality"),
            "unmatched_movements_count": len(
                detail.get("unmatched_movements") or []
            ),
            "related_orders_count": len(detail.get("related_orders") or []),
        }
