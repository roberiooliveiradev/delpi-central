"""Auditoria de consumo OP × operação × componente (GLPI #1353 — C2 detalhe).

Composição read-only: SC2 (ordem) + SG2 (roteiro) + SH8 (alocação) + HZA
(coletor) + SH6 (apontamento) + SG1 histórica (estrutura na data de emissão)
+ SD4 (empenho) + SD3 (movimentos classificados). Nenhuma regra Protheus sai
deste contexto; diferenças nunca viram acusação — ``unknown``/``null``
representam o que não é comprovável.
"""

from __future__ import annotations

import re
from typing import Any

from app.application.dto.supplies.get_consumption_audit_order_request import (
    GetConsumptionAuditOrderRequest,
)
from app.domain.ports.production.consumption_audit_repository_port import (
    ConsumptionAuditRepositoryPort,
)
from app.domain.totvs.protheus_internal_movements import (
    MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT,
    MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION,
    MOVEMENT_CATEGORY_PRODUCTION_RECEIPT,
    MOVEMENT_CATEGORY_UNCLASSIFIED,
    MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER,
    DIRECTION_OUTBOUND,
    WAREHOUSE_TRANSFER_CFS,
    PRODUCTION_CONSUMPTION_TM,
    classify_internal_movement,
)

_PRODUCTION_ORDER_RE = re.compile(r"^[0-9A-Z]{11}$")
_EPSILON = 1e-9
_LABOR_PRODUCT_TYPE = "MO"

# Invariantes pendentes de homologação (D-01/D-03/A1) — sempre declaradas.
_UNRESOLVED_SEMANTICS = (
    "automatic_issue_causality",
    "re0_tm999_transfer_meaning",
    "sh8_row_removal_semantics",
)


class GetConsumptionAuditOrderUseCase:
    def __init__(self, repository: ConsumptionAuditRepositoryPort):
        self._repository = repository

    def execute(
        self, request: GetConsumptionAuditOrderRequest
    ) -> dict[str, Any] | None:
        production_order = (request.production_order or "").strip().upper()
        if not _PRODUCTION_ORDER_RE.match(production_order):
            raise ValueError(
                "production_order inválida: 11 posições alfanuméricas "
                "(C2_NUM 6 + C2_ITEM 2 + C2_SEQUEN 3)."
            )
        branch = request.branch

        order = self._repository.fetch_order(
            production_order=production_order, branch=branch
        )
        if not order:
            return None

        commitments = self._repository.fetch_commitments(
            production_order=production_order, branch=branch
        )
        movements = self._repository.fetch_movements(
            production_order=production_order, branch=branch
        )
        appointments = self._repository.fetch_appointments(
            production_order=production_order, branch=branch
        )
        events = self._repository.fetch_operation_events(
            production_order=production_order, branch=branch
        )
        allocations = self._repository.fetch_allocations(
            production_order=production_order, branch=branch
        )
        routing = self._repository.fetch_routing(
            product_code=order["product_code"], branch=branch
        )
        reference_date = self._reference_date(order)
        bom_rows = (
            self._repository.fetch_bom_components(
                product_code=order["product_code"],
                branch=branch,
                reference_date=reference_date,
            )
            if reference_date
            else []
        )

        meta = self._repository.fetch_product_metadata(
            codes=self._all_component_codes(commitments, movements, bom_rows)
        )

        warnings: list[str] = []
        operations = self._build_operations(
            order=order,
            commitments=commitments,
            movements=movements,
            appointments=appointments,
            events=events,
            allocations=allocations,
            routing=routing,
            bom_rows=bom_rows,
            meta=meta,
            warnings=warnings,
        )
        unmatched = self._unmatched_movements(
            movements=movements,
            commitments=commitments,
            meta=meta,
            production_order=production_order,
            warnings=warnings,
        )
        related_orders = self._related_orders(
            order=order,
            commitments=commitments,
            branch=branch,
        )
        quality = self._quality(
            order=order,
            operations=operations,
            appointments=appointments,
            warnings=warnings,
        )

        return {
            "branch": branch,
            "production_order": production_order,
            "order": self._order_payload(order),
            "related_orders": related_orders,
            "operations": operations,
            "unmatched_movements": unmatched,
            "quality": quality,
            "metadata": {
                "generated_at_source": "api-delpi",
                "tolerance_policy": {
                    "id": "glpi1353-v0",
                    "absolute": None,
                    "percent": None,
                },
                "contract_version": "a2-proposal-1",
            },
        }

    # ------------------------------------------------------------------
    # Composição por operação
    # ------------------------------------------------------------------

    def _build_operations(
        self,
        *,
        order: dict,
        commitments: list[dict],
        movements: list[dict],
        appointments: list[dict],
        events: list[dict],
        allocations: list[dict],
        routing: list[dict],
        bom_rows: list[dict],
        meta: dict[str, dict],
        warnings: list[str],
    ) -> list[dict]:
        bom_map = self._bom_map(bom_rows)
        routing_map = self._routing_map(routing)
        sh6_by_op = self._group_by_operation(appointments)
        hza_by_op = self._group_by_operation(events)
        sh8_by_op = self._group_by_operation(allocations)
        commitment_codes = {
            str(row.get("component_code") or "").strip() for row in commitments
        }
        for code in sorted(set(bom_map) - commitment_codes):
            warnings.append("sg1_component_not_committed")

        operations: dict[str, dict] = {}
        operation_keys = sorted(
            set(routing_map) | set(sh8_by_op) | set(sh6_by_op) | set(hza_by_op)
            | {
                str(r.get("operation") or "").strip() or "unknown"
                for r in commitments
            }
        )
        if not operation_keys:
            warnings.append("no_operations_found")

        for op_key in operation_keys:
            evidence = self._execution_evidence(
                operation=op_key,
                sh8_rows=sh8_by_op.get(op_key, []),
                hza_rows=hza_by_op.get(op_key, []),
                sh6_rows=sh6_by_op.get(op_key, []),
            )
            work_center = (
                routing_map.get(op_key)
                or next(
                    (
                        str(a.get("work_center") or "").strip()
                        for a in sh8_by_op.get(op_key, [])
                        if str(a.get("work_center") or "").strip()
                    ),
                    "",
                )
                or None
            )
            operations[op_key] = {
                "operation": op_key,
                "work_center": work_center,
                "execution_evidence": evidence,
                "components": [],
            }

        committed_ops = {
            str(r.get("operation") or "").strip() for r in commitments
        }
        for op_key in sorted(set(operations) - committed_ops):
            warnings.append("operation_without_commitment")

        # Entradas de componente agregadas por (operação, código) com lista
        # de origens D4_OPORIG preservadas.
        component_entries: dict[tuple[str, str], dict] = {}
        for row in commitments:
            op_key = str(row.get("operation") or "").strip() or "unknown"
            code = str(row.get("component_code") or "").strip()
            entry = component_entries.setdefault(
                (op_key, code),
                {
                    "operation": op_key,
                    "component_code": code,
                    "component_description": row.get("component_description"),
                    "component_type": row.get("component_type"),
                    "unit_of_measure": row.get("unit_of_measure"),
                    "original_quantity": 0.0,
                    "open_quantity": 0.0,
                    "derived_consumed_quantity": 0.0,
                    "commitment_lines": 0,
                    "origin_orders": [],
                },
            )
            entry["original_quantity"] += float(row.get("original_quantity") or 0)
            entry["open_quantity"] += float(row.get("open_quantity") or 0)
            entry["derived_consumed_quantity"] += float(
                row.get("derived_consumed_quantity") or 0
            )
            entry["commitment_lines"] += int(row.get("commitment_lines") or 0)
            origin = row.get("origin_order")
            if origin and origin not in entry["origin_orders"]:
                entry["origin_orders"].append(origin)

        # Binding de movimentos: cada linha casa com exatamente uma entrada
        # (operação, código) — preferência por entrada com consumo derivado,
        # desempate pela operação mais baixa. Múltiplos candidatos geram flag.
        movement_binding: dict[int, tuple[str, str]] = {}
        for idx, mov in enumerate(movements):
            code = str(mov.get("component_code") or "").strip()
            candidates = [
                key for key in component_entries if key[1] == code
            ]
            if not candidates:
                continue
            target = self._binding_target(candidates, component_entries)
            movement_binding[idx] = target
            if len(candidates) > 1:
                warnings.append("movement_binding_ambiguous")

        for (op_key, code), entry in sorted(component_entries.items()):
            bound = [
                mov
                for idx, mov in enumerate(movements)
                if movement_binding.get(idx) == (op_key, code)
            ]
            component = self._component_payload(
                entry=entry,
                bound_movements=bound,
                bom=bom_map.get(code),
                meta=meta.get(code, {}),
                planned_quantity=float(order.get("planned_quantity") or 0),
                production_order=order["production_order"],
                execution_state=operations[op_key]["execution_evidence"][
                    "execution_state"
                ],
                reference_date=self._reference_date(order),
                warnings=warnings,
            )
            operations[op_key]["components"].append(component)

        return [operations[key] for key in sorted(operations)]

    @staticmethod
    def _binding_target(
        candidates: list[tuple[str, str]],
        entries: dict[tuple[str, str], dict],
    ) -> tuple[str, str]:
        def _score(key: tuple[str, str]) -> tuple[float, str]:
            entry = entries[key]
            return (-float(entry["derived_consumed_quantity"]), key[0])

        return min(candidates, key=_score)

    def _component_payload(
        self,
        *,
        entry: dict,
        bound_movements: list[dict],
        bom: dict | None,
        meta: dict,
        planned_quantity: float,
        production_order: str,
        execution_state: str,
        reference_date: str | None,
        warnings: list[str],
    ) -> dict:
        code = entry["component_code"]
        component_type = (
            entry.get("component_type") or meta.get("product_type") or ""
        ).strip() or None
        is_labor = component_type == _LABOR_PRODUCT_TYPE

        classified: list[dict] = []
        excluded: list[dict] = []
        eligible_qty = 0.0
        for mov in bound_movements:
            payload, eligible = self._movement_payload(
                mov,
                component_type=component_type,
                production_order=production_order,
            )
            if eligible:
                classified.append(payload)
                eligible_qty += float(mov.get("quantity") or 0)
            else:
                excluded.append(payload)

        bom_payload: dict[str, Any] = {
            "structure_as_of": "order_emission_date",
            "reference_date": reference_date,
            "quantity_per_unit": None,
            "valid_from": None,
            "valid_to": None,
            "theoretical_quantity": None,
            "completeness": "missing",
        }
        if bom is not None:
            qty_per_unit = bom.get("quantity_per_unit")
            bom_payload.update(
                {
                    "quantity_per_unit": qty_per_unit,
                    "valid_from": bom.get("valid_from"),
                    "valid_to": bom.get("valid_to"),
                    "theoretical_quantity": (
                        float(qty_per_unit) * planned_quantity
                        if qty_per_unit is not None
                        else None
                    ),
                    "completeness": "complete",
                }
            )
        else:
            warnings.append("commitment_without_bom")

        derived = entry["derived_consumed_quantity"]
        quality_flags: list[str] = []
        if any(
            str(m.get("cf") or "").strip() in WAREHOUSE_TRANSFER_CFS
            and str(m.get("tm") or "").strip() == PRODUCTION_CONSUMPTION_TM
            for m in bound_movements
        ):
            quality_flags.append("ambiguous_cf_semantics")
            warnings.append("re0_tm999_ambiguity")

        # Diferença aritmética só existe entre valores comparáveis: UM do
        # movimento divergente da UM do empenho torna a comparação nula.
        entry_uom = str(
            entry.get("unit_of_measure") or meta.get("unit_of_measure") or ""
        ).strip()
        uom_mismatch = bool(entry_uom) and any(
            str(m.get("unit_of_measure") or "").strip() not in {"", entry_uom}
            for m in bound_movements
        )
        if uom_mismatch:
            quality_flags.append("uom_mismatch")
            warnings.append("movement_uom_differs_from_commitment")

        discrepancy_value = None if uom_mismatch else eligible_qty - derived

        if is_labor:
            classification = "unclassified"
        elif execution_state != "evidenced" or uom_mismatch:
            classification = "requires_investigation"
        elif abs(discrepancy_value) < _EPSILON:
            classification = "reconciled"
        else:
            classification = "arithmetic_difference"

        return {
            "component_code": code,
            "component_description": entry.get("component_description")
            or meta.get("description"),
            "component_type": component_type,
            "unit_of_measure": entry.get("unit_of_measure")
            or meta.get("unit_of_measure"),
            "bom": bom_payload,
            "commitment": {
                "original_quantity": entry["original_quantity"],
                "open_quantity": entry["open_quantity"],
                "derived_consumed_quantity": derived,
                "origin_orders": entry["origin_orders"],
                "lines": entry["commitment_lines"],
            },
            "movements": {
                "eligible_consumption_quantity": eligible_qty,
                "classified": classified,
                "excluded": excluded,
            },
            "discrepancy": {
                "value": discrepancy_value,
                "reference": "derived_commitment",
                "within_tolerance": None,
            },
            "classification": classification,
            "quality_flags": quality_flags,
        }

    def _movement_payload(
        self,
        mov: dict,
        *,
        component_type: str | None,
        production_order: str,
    ) -> tuple[dict, bool]:
        cls = classify_internal_movement(
            cf=mov.get("cf"),
            tm=mov.get("tm"),
            document=mov.get("document"),
            production_order=production_order,
        )
        reversed_flag = str(mov.get("reversed_flag") or "").strip() == "S"
        eligible = (
            cls.category == MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION
            and cls.direction == DIRECTION_OUTBOUND
            and component_type != _LABOR_PRODUCT_TYPE
            and not reversed_flag
        )
        if reversed_flag:
            reason = "reversed"
        elif component_type == _LABOR_PRODUCT_TYPE:
            reason = "labor_not_material"
        elif cls.category != MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION:
            reason = "not_raw_material_consumption"
        elif cls.direction != DIRECTION_OUTBOUND:
            reason = "not_outbound_consumption"
        else:
            reason = None

        payload = {
            "document": mov.get("document"),
            "cf": mov.get("cf"),
            "tm": mov.get("tm"),
            "quantity": mov.get("quantity"),
            "unit_of_measure": mov.get("unit_of_measure"),
            "warehouse": mov.get("warehouse"),
            "issue_date": mov.get("issue_date"),
            "kind": cls.category,
            "direction": cls.direction,
            "reversed": reversed_flag,
            "component_code": mov.get("component_code"),
        }
        if not eligible and reason:
            payload["reason"] = reason
        if component_type == _LABOR_PRODUCT_TYPE:
            payload["component_type"] = _LABOR_PRODUCT_TYPE
        return payload, eligible

    def _unmatched_movements(
        self,
        *,
        movements: list[dict],
        commitments: list[dict],
        meta: dict[str, dict],
        production_order: str,
        warnings: list[str],
    ) -> list[dict]:
        committed_codes = {
            str(r.get("component_code") or "").strip() for r in commitments
        }
        unmatched: list[dict] = []
        for mov in movements:
            code = str(mov.get("component_code") or "").strip()
            if code in committed_codes:
                continue
            component_type = (
                meta.get(code, {}).get("product_type") or ""
            ).strip() or None
            payload, _ = self._movement_payload(
                mov,
                component_type=component_type,
                production_order=production_order,
            )
            payload["binding"] = "no_matching_commitment"
            unmatched.append(payload)
        if unmatched:
            warnings.append("movements_without_commitment")
        return unmatched

    # ------------------------------------------------------------------
    # Evidências de execução — fontes separadas, derivação conservadora
    # ------------------------------------------------------------------

    def _execution_evidence(
        self,
        *,
        operation: str,
        sh8_rows: list[dict],
        hza_rows: list[dict],
        sh6_rows: list[dict],
    ) -> dict:
        appointment_refs = [
            str(r.get("appointment_ref") or "").strip()
            for r in hza_rows
            if str(r.get("appointment_ref") or "").strip()
        ]
        sh6_payload = []
        for row in sh6_rows:
            ident = str(row.get("appointment_id") or "").strip()
            linked = bool(
                ident and any(ident in ref for ref in appointment_refs)
            )
            sh6_payload.append(
                {
                    "appointment_id": ident or None,
                    "reported_quantity": row.get("reported_quantity"),
                    "lost_quantity": row.get("lost_quantity"),
                    "type": row.get("appointment_type"),
                    "product_code": row.get("product_code"),
                    "reported_at": row.get("reported_at"),
                    "started_at": self._merge_dt(
                        row.get("started_on"), row.get("start_time")
                    ),
                    "ended_at": self._merge_dt(
                        row.get("ended_on"), row.get("end_time")
                    ),
                    "resource": row.get("resource"),
                    "linked_hza": linked,
                    "channel": "collector" if linked else "unknown",
                    "source": "SH6010",
                }
            )

        hza_payload = [
            {
                "status": row.get("status"),
                "transaction_type": row.get("transaction_type"),
                "appointment_ref": row.get("appointment_ref") or None,
                "resource": row.get("resource"),
                "started_at": self._merge_dt(
                    row.get("started_on"), row.get("start_time")
                ),
                "ended_at": self._merge_dt(row.get("ended_on"), row.get("end_time")),
                "source": "HZA010",
            }
            for row in hza_rows
        ]

        executed = bool(sh6_payload) or any(
            str(r.get("status") or "").strip() in {"1", "2"} for r in hza_rows
        )
        if executed:
            execution_state = "evidenced"
        elif sh8_rows:
            execution_state = "pending"
        else:
            execution_state = "unknown"

        sh8_payload = None
        if sh8_rows:
            row = sh8_rows[0]
            sh8_payload = {
                "row_present": True,
                "status": row.get("status") or None,
                "quantity": row.get("quantity"),
                "scheduled_start": self._merge_dt(
                    row.get("scheduled_start"), row.get("scheduled_start_time")
                ),
                "scheduled_end": self._merge_dt(
                    row.get("scheduled_end"), row.get("scheduled_end_time")
                ),
                "source": "SH8010",
            }
        else:
            sh8_payload = {
                "row_present": False,
                "status": None,
                "source": "SH8010",
            }

        return {
            "sh8_allocation": sh8_payload,
            "hza_records": hza_payload,
            "sh6_appointments": sh6_payload,
            "execution_state": execution_state,
        }

    # ------------------------------------------------------------------
    # Agregações de apoio
    # ------------------------------------------------------------------

    def _related_orders(
        self,
        *,
        order: dict,
        commitments: list[dict],
        branch: str,
    ) -> list[dict]:
        related: list[dict] = []
        seen: set[tuple[str, str, str | None]] = set()

        def _add(op: str, relationship: str, extra: dict | None = None) -> None:
            key = (op, relationship, (extra or {}).get("component_code"))
            if key in seen or not op:
                return
            seen.add(key)
            related.append(
                {
                    "production_order": op,
                    "relationship": relationship,
                    "confidence": "proven",
                    **(extra or {}),
                }
            )

        for row in self._repository.fetch_family_orders(
            order_number=order.get("order_number") or "",
            branch=branch,
            exclude_production_order=order["production_order"],
        ):
            _add(
                str(row.get("production_order") or "").strip(),
                "same_order_number",
                {
                    "product_code": row.get("product_code"),
                    "product_type": row.get("product_type"),
                    "planned_quantity": row.get("planned_quantity"),
                    "produced_quantity": row.get("produced_quantity"),
                    "status": row.get("status"),
                },
            )

        for row in commitments:
            for origin in [row.get("origin_order")]:
                if origin:
                    _add(
                        str(origin).strip(),
                        "producing_order_for_component",
                        {"component_code": row.get("component_code")},
                    )

        for row in self._repository.fetch_parent_consumers(
            production_order=order["production_order"], branch=branch
        ):
            _add(
                str(row.get("production_order") or "").strip(),
                "parent_commitment_via_d4_oporig",
                {"component_code": row.get("component_code")},
            )

        return related

    def _quality(
        self,
        *,
        order: dict,
        operations: list[dict],
        appointments: list[dict],
        warnings: list[str],
    ) -> dict:
        sh6_qty = sum(
            float(a.get("reported_quantity") or 0)
            for a in appointments
            if str(a.get("appointment_type") or "").strip() == "P"
        )
        produced = float(order.get("produced_quantity") or 0)
        if abs(sh6_qty - produced) > _EPSILON:
            warnings.append("sh6_vs_sc2_quantity_mismatch")

        classes = {
            c["classification"]
            for op in operations
            for c in op["components"]
        }
        if not operations:
            status = "inconclusive"
        elif classes == {"reconciled"} and not warnings:
            status = "complete"
        else:
            status = "partial"

        return {
            "status": status,
            "warnings": sorted(set(warnings)),
            "unresolved_semantics": list(_UNRESOLVED_SEMANTICS),
        }

    @staticmethod
    def _order_payload(order: dict) -> dict:
        return {
            "order_number": order.get("order_number"),
            "order_item": order.get("order_item"),
            "order_sequence": order.get("order_sequence"),
            "product_code": order.get("product_code"),
            "product_description": order.get("product_description"),
            "product_type": order.get("product_type"),
            "unit_of_measure": order.get("unit_of_measure"),
            "planned_quantity": order.get("planned_quantity"),
            "produced_quantity": order.get("produced_quantity"),
            "produced_quantity_basis": "stock_receipt",
            "status": order.get("status"),
            "finished_at": order.get("finished_at"),
            "emission_date": order.get("emission_date"),
            "planned_start_date": order.get("planned_start_date"),
            "due_date": order.get("due_date"),
            "priority": order.get("priority"),
            "order_type": order.get("order_type"),
            "warehouse": order.get("warehouse"),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reference_date(order: dict) -> str | None:
        raw = str(order.get("emission_date") or "").strip()
        return raw.replace("-", "") or None

    @staticmethod
    def _merge_dt(day: str | None, hour: str | None) -> str | None:
        day_token = str(day or "").strip()
        if not day_token:
            return None
        hour_token = str(hour or "").strip()
        return f"{day_token}T{hour_token}" if hour_token else day_token

    @staticmethod
    def _group_by_operation(rows: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for row in rows:
            key = str(row.get("operation") or "").strip() or "unknown"
            grouped.setdefault(key, []).append(row)
        return grouped

    @staticmethod
    def _routing_map(rows: list[dict]) -> dict[str, str]:
        """Operação → centro de trabalho; filial específica prevalece sobre a
        linha compartilhada (filial em branco)."""
        result: dict[str, str] = {}
        for row in sorted(rows, key=lambda r: bool(str(r.get("branch") or "").strip())):
            op = str(row.get("operation") or "").strip()
            center = str(row.get("work_center") or "").strip()
            if op:
                result[op] = center
        return result

    @staticmethod
    def _bom_map(rows: list[dict]) -> dict[str, dict]:
        """Componente → linha SG1; filial específica prevalece sobre a
        compartilhada (filial em branco)."""
        result: dict[str, dict] = {}
        for row in sorted(rows, key=lambda r: bool(str(r.get("branch") or "").strip())):
            code = str(row.get("component_code") or "").strip()
            if code:
                result[code] = row
        return result

    @staticmethod
    def _all_component_codes(
        commitments: list[dict],
        movements: list[dict],
        bom_rows: list[dict],
    ) -> list[str]:
        codes = {
            str(r.get("component_code") or "").strip() for r in commitments
        }
        codes |= {str(r.get("component_code") or "").strip() for r in movements}
        codes |= {str(r.get("component_code") or "").strip() for r in bom_rows}
        codes.discard("")
        return sorted(codes)
