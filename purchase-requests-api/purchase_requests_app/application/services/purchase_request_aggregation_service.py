from __future__ import annotations

from typing import Any

from purchase_requests_app.domain.services.purchase_request_domain_service import (
    ScopeResolution,
    derive_delivery_status,
    derive_order_status,
    derive_overall_stage,
    derive_receipt_status,
    map_approval_status,
)


class PurchaseRequestAggregationService:
    def filter_authorized_lines(
        self,
        lines: list[dict[str, Any]],
        *,
        branch: str,
        resolution: ScopeResolution,
    ) -> list[dict[str, Any]]:
        if resolution.view_all:
            return lines
        return [
            line
            for line in lines
            if resolution.allows(branch, line.get("cost_center_code"))
        ]

    def build_list_line_items(self, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Lista operacional no grão item da SC (linha enriquecida, sem agregar cabeçalho)."""
        enriched = [self._enrich_line(line) for line in lines]
        enriched.sort(
            key=lambda item: (
                item.get("request_issue_date") or "",
                item.get("request_number") or "",
                item.get("request_item") or "",
            ),
            reverse=True,
        )
        return enriched

    def aggregate_list_items(self, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for line in lines:
            key = (line["branch"], line["request_number"])
            grouped.setdefault(key, []).append(line)
        items: list[dict[str, Any]] = []
        for (branch, request_number), group in grouped.items():
            items.append(self._aggregate_header(group, branch=branch, request_number=request_number))
        items.sort(
            key=lambda item: (item.get("issue_date") or "", item.get("request_number") or ""),
            reverse=True,
        )
        return items

    def build_detail_payload(
        self,
        lines: list[dict[str, Any]],
        *,
        branch: str,
        request_number: str,
    ) -> dict[str, Any]:
        header = self._aggregate_header(lines, branch=branch, request_number=request_number)
        enriched_lines = [self._enrich_line(line) for line in lines]
        return {
            "header": header,
            "lines": enriched_lines,
            "timeline": self._build_timeline(enriched_lines),
        }

    def _aggregate_header(
        self,
        lines: list[dict[str, Any]],
        *,
        branch: str,
        request_number: str,
    ) -> dict[str, Any]:
        first = lines[0]
        cost_centers = []
        seen_cc: set[str] = set()
        for line in lines:
            code = (line.get("cost_center_code") or "").strip()
            if code and code not in seen_cc:
                seen_cc.add(code)
                cost_centers.append(
                    {
                        "code": code,
                        "description": line.get("cost_center_description"),
                    }
                )
        orders: dict[tuple[str, str], dict[str, Any]] = {}
        suppliers: dict[tuple[str, str], dict[str, Any]] = {}
        issue_dates: list[str] = []
        order_dates: list[str] = []
        receipt_dates: list[str] = []
        requested_total = 0.0
        ordered_total = 0.0
        received_total = 0.0
        has_overdue = False
        max_days_overdue = None
        stages: list[str] = []
        for line in lines:
            enriched = self._enrich_line(line)
            stages.append(enriched["derived"]["overall_stage"])
            if line.get("request_issue_date"):
                issue_dates.append(line["request_issue_date"])
            requested_total += float(line.get("requested_quantity") or 0)
            ordered_total += float(line.get("ordered_quantity") or 0)
            for order in line.get("purchase_orders") or []:
                key = (order.get("order_number"), order.get("order_item"))
                orders[key] = {
                    "branch": order.get("branch"),
                    "order_number": order.get("order_number"),
                    "order_item": order.get("order_item"),
                    "supplier_code": order.get("supplier_code"),
                    "supplier_store": order.get("supplier_store"),
                    "supplier_name": order.get("supplier_name"),
                }
                supplier_key = (order.get("supplier_code"), order.get("supplier_store"))
                suppliers[supplier_key] = {
                    "code": order.get("supplier_code"),
                    "store": order.get("supplier_store"),
                    "name": order.get("supplier_name"),
                }
                if order.get("issue_date"):
                    order_dates.append(order["issue_date"])
                received_total += float(order.get("received_quantity") or 0)
                delivery = order.get("derived", {}).get("delivery_status")
                if delivery == "overdue":
                    has_overdue = True
                    days = order.get("derived", {}).get("days_overdue")
                    if days is not None:
                        max_days_overdue = max(max_days_overdue or 0, days)
                for receipt in order.get("receipts") or []:
                    if receipt.get("entry_date"):
                        receipt_dates.append(receipt["entry_date"])
        return {
            "branch": branch,
            "request_number": request_number,
            "issue_date": min(issue_dates) if issue_dates else first.get("request_issue_date"),
            "requester": {
                "protheus_user_id": first.get("requester_protheus_user_id"),
                "code": first.get("requester_code"),
                "name": first.get("requester_name"),
            },
            "visible_items_count": len(lines),
            "cost_centers": cost_centers,
            "approval_summary": {
                "status": map_approval_status(first.get("approval_raw")),
            },
            "overall_stage": self._conservative_stage(stages),
            "purchase_orders": list(orders.values()),
            "suppliers": list(suppliers.values()),
            "first_order_date": min(order_dates) if order_dates else None,
            "last_order_date": max(order_dates) if order_dates else None,
            "first_receipt_date": min(receipt_dates) if receipt_dates else None,
            "last_receipt_date": max(receipt_dates) if receipt_dates else None,
            "requested_quantity": requested_total,
            "ordered_quantity": ordered_total,
            "received_quantity": received_total,
            "has_overdue_order": has_overdue,
            "max_days_overdue": max_days_overdue,
        }

    def _enrich_line(self, line: dict[str, Any]) -> dict[str, Any]:
        requested = float(line.get("requested_quantity") or 0)
        ordered_sc = float(line.get("ordered_quantity") or 0)
        orders = line.get("purchase_orders") or []
        has_orders = bool(orders)
        max_received = max((float(o.get("received_quantity") or 0) for o in orders), default=0.0)
        max_order_qty = max((float(o.get("ordered_quantity") or 0) for o in orders), default=0.0)
        enriched_orders = [self._enrich_order(order) for order in orders]
        return {
            **line,
            "approval": {
                "status": line.get("approval_status") or map_approval_status(line.get("approval_raw")),
                "approver_name": line.get("approver_name"),
            },
            "requester": {
                "protheus_user_id": line.get("requester_protheus_user_id"),
                "code": line.get("requester_code"),
                "name": line.get("requester_name"),
            },
            "cost_center": {
                "code": line.get("cost_center_code"),
                "description": line.get("cost_center_description"),
            },
            "suggested_supplier": {
                "code": line.get("suggested_supplier_code"),
                "store": line.get("suggested_supplier_store"),
                "name": line.get("suggested_supplier_name"),
            },
            "purchase_orders": enriched_orders,
            "derived": {
                "order_status": derive_order_status(
                    ordered_quantity=ordered_sc,
                    requested_quantity=requested,
                    has_orders=has_orders,
                ),
                "receipt_status": derive_receipt_status(
                    has_orders=has_orders,
                    received_quantity=max_received,
                    ordered_quantity=max_order_qty or requested,
                ),
                "overall_stage": derive_overall_stage(
                    residual=bool(line.get("residual")),
                    requested_quantity=requested,
                    ordered_quantity=ordered_sc,
                    has_orders=has_orders,
                    max_received_quantity=max_received,
                    max_order_quantity=max_order_qty,
                ),
            },
        }

    def _enrich_order(self, order: dict[str, Any]) -> dict[str, Any]:
        from datetime import date

        today = date.today().isoformat()
        open_qty = float(order.get("open_quantity") or 0)
        received = float(order.get("received_quantity") or 0)
        delivery_status = derive_delivery_status(
            expected_delivery_date=order.get("expected_delivery_date"),
            open_quantity=open_qty,
            received_quantity=received,
            today_iso=today,
        )
        days_overdue = None
        days_until_due = None
        expected = order.get("expected_delivery_date")
        if expected:
            from datetime import datetime

            exp = datetime.strptime(expected, "%Y-%m-%d").date()
            delta = (exp - date.today()).days
            if delta >= 0:
                days_until_due = delta
            else:
                days_overdue = abs(delta)
        buyer = order.get("buyer")
        return {
            **order,
            "derived": {
                "delivery_status": delivery_status,
                "days_until_due": days_until_due,
                "days_overdue": days_overdue,
                "receipt_status": derive_receipt_status(
                    has_orders=True,
                    received_quantity=received,
                    ordered_quantity=float(order.get("ordered_quantity") or 0),
                ),
            },
            "buyer": buyer,
        }

    @staticmethod
    def _conservative_stage(stages: list[str]) -> str:
        precedence = [
            "awaiting_order",
            "partially_ordered",
            "awaiting_receipt",
            "partially_received",
            "completed",
            "residual_closed",
        ]
        for stage in precedence:
            if stage in stages:
                return stage
        return stages[0] if stages else "awaiting_order"

    @staticmethod
    def _build_timeline(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for line in lines:
            if line.get("request_issue_date"):
                events.append(
                    {
                        "type": "request_created",
                        "date": line["request_issue_date"],
                        "label": "Solicitação criada",
                        "reference": {
                            "request_number": line.get("request_number"),
                            "request_item": line.get("request_item"),
                        },
                        "metadata": {},
                    }
                )
            for order in line.get("purchase_orders") or []:
                if order.get("issue_date"):
                    events.append(
                        {
                            "type": "purchase_order_created",
                            "date": order["issue_date"],
                            "label": "Pedido de compra criado",
                            "reference": {
                                "order_number": order.get("order_number"),
                                "order_item": order.get("order_item"),
                            },
                            "metadata": {},
                        }
                    )
                if order.get("expected_delivery_date"):
                    events.append(
                        {
                            "type": "expected_delivery",
                            "date": order["expected_delivery_date"],
                            "label": "Previsão de entrega",
                            "reference": {
                                "order_number": order.get("order_number"),
                            },
                            "metadata": {},
                        }
                    )
                for receipt in order.get("receipts") or []:
                    if receipt.get("entry_date"):
                        events.append(
                            {
                                "type": "receipt",
                                "date": receipt["entry_date"],
                                "label": "Entrada NF",
                                "reference": {
                                    "invoice_number": receipt.get("invoice_number"),
                                    "order_number": receipt.get("purchase_order_number"),
                                },
                                "metadata": {},
                            }
                        )
        events.sort(key=lambda item: item.get("date") or "")
        return events
