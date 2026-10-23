"""Portal Home "Atenção" — real pending situations composed from owner services.

Each card requires a proven count from an authoritative producer; navigation
cards without a real pending source were removed (see
HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md). A source failure renders
the card as "unavailable" and registers a partial failure — never as zero.

Cards are compact (name, count, short description, "Abrir" action) — no record
previews are fetched on the Home (HOME-ATTENTION.P2).
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Callable

from app.application.security.supplies_permissions import SAFETY_STOCK_APP_ACCESS
from app.application.services.authorization_service import AuthorizationService
from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.application.services.late_deliveries_composition_service import (
    current_month_bounds,
)
from app.domain.entities import EffectiveUser
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
)
from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads

logger = logging.getLogger("supplies-api.home_attention")

SAFETY_STOCK_APP_HREF = "/apps/estoque-seguranca"

PR_ORDERING_STAGES = ("awaiting_order", "partially_ordered")
PR_RECEIVING_STAGES = ("ordered", "awaiting_receipt", "partially_received")

# Smallest page that still returns the producer summary alongside items.
_COUNT_PAGE_SIZE = 1


def _view_target(view_id: str, query: str | None = None) -> dict[str, Any]:
    target: dict[str, Any] = {"kind": "view", "viewId": view_id}
    if query:
        target["query"] = query
    return target


def _stages_query(stages: tuple[str, ...]) -> str:
    return "&".join(f"overall_stage={stage}" for stage in stages)


def _unavailable(card_id: str, title: str) -> dict[str, Any]:
    return {
        "id": card_id,
        "title": title,
        "description": "Origem de dados temporariamente indisponível.",
        "count": None,
        "countUnit": None,
        "status": "unavailable",
        "target": None,
    }


class HomeAttentionService:
    def __init__(
        self,
        *,
        capabilities: CapabilityResolutionService | None = None,
        authorization: AuthorizationService | None = None,
        delpi_reads: SuppliesDelpiReads | None = None,
        purchase_requests: PurchaseRequestsGateway | None = None,
        today_provider: Callable[[], date] | None = None,
    ) -> None:
        self.capabilities = capabilities or CapabilityResolutionService()
        self.authorization = authorization or AuthorizationService()
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()
        self.purchase_requests = purchase_requests or PurchaseRequestsGateway()
        self._today = today_provider or date.today

    def compose(self, user: EffectiveUser) -> dict[str, Any]:
        caps = self.capabilities.resolve(user)
        if not caps["capabilities"].get("access") and not user.is_superadmin:
            return {"cards": [], "partialFailures": []}

        units = self.authorization.allowed_units(user)
        if not units:
            return {"cards": [], "partialFailures": []}

        token = user.access_token or ""
        # Thread-local buffers keep order deterministic and make one slow
        # source bound total latency instead of summing it.
        failures: list[dict[str, Any]] = []
        cards: list[dict[str, Any]] = []
        stages = (
            lambda fl: self._purchase_requests_cards(token, units, fl),
            lambda fl: [self._purchase_orders_late_card(token, units, fl)],
            lambda fl: [self._late_deliveries_card(token, units, fl)],
            lambda fl: [self._safety_stock_card(token, units, fl, user)],
        )
        with ThreadPoolExecutor(max_workers=len(stages)) as pool:
            futures = []
            for index, fn in enumerate(stages):
                buffer: list[dict[str, Any]] = []
                futures.append((index, pool.submit(fn, buffer), buffer))
            for index, future, buffer in sorted(futures, key=lambda f: f[0]):
                try:
                    produced = future.result()
                except Exception:
                    logger.warning("home_attention_source_failed source=compose")
                    failures.append(
                        {"source": "composition", "code": "source_unavailable"}
                    )
                    continue
                failures.extend(buffer)
                cards.extend(produced)

        # A confirmed zero is not attention; unavailable stays visible.
        visible = [
            card
            for card in cards
            if card["status"] == "unavailable" or (card.get("count") or 0) > 0
        ]
        return {"cards": visible, "partialFailures": failures}

    # --- purchase-requests-api sources -------------------------------------

    def _purchase_requests_cards(
        self,
        token: str,
        units: list[str],
        failures: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        ordering_card = {
            "id": "purchase_requests_ordering",
            "title": "Solicitações aguardando pedido",
            "description": "Solicitações do mês corrente com itens ainda sem pedido de compra ou com pedido parcial.",
            "countUnit": "solicitações",
            "stages": PR_ORDERING_STAGES,
            "bucket": "ordering",
        }
        receiving_card = {
            "id": "purchase_requests_receiving",
            "title": "Solicitações aguardando recebimento",
            "description": "Solicitações do mês corrente com pedido emitido aguardando recebimento total ou parcial.",
            "countUnit": "solicitações",
            "stages": PR_RECEIVING_STAGES,
            "bucket": "receiving",
        }
        start, end = current_month_bounds(self._today())
        try:
            payload = self.purchase_requests.get_summary(
                access_token=token,
                params={
                    "branch": units,
                    "date_from": start,
                    "date_to": end,
                },
            )
        except Exception:
            logger.warning("home_attention_source_failed source=purchase_requests")
            failures.append(
                {"source": "purchase_requests", "code": "source_unavailable"}
            )
            return [
                _unavailable(c["id"], c["title"])
                for c in (ordering_card, receiving_card)
            ]

        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        buckets = data.get("buckets") if isinstance(data, dict) else {}
        if not isinstance(buckets, dict):
            buckets = {}

        cards = []
        for spec in (ordering_card, receiving_card):
            try:
                count = int(buckets.get(spec["bucket"]) or 0)
            except (TypeError, ValueError):
                count = 0
            cards.append(
                {
                    "id": spec["id"],
                    "title": spec["title"],
                    "description": spec["description"],
                    "count": count,
                    "countUnit": spec["countUnit"],
                    "status": "available",
                    "target": _view_target(
                        "purchase_requests", _stages_query(spec["stages"])
                    ),
                }
            )
        return cards

    # --- api-delpi sources --------------------------------------------------

    def _purchase_orders_late_card(
        self,
        token: str,
        units: list[str],
        failures: list[dict[str, Any]],
    ) -> dict[str, Any]:
        card_id = "purchase_orders_late"
        title = "Pedidos de compra em atraso"
        try:
            payload = self.delpi_reads.get_purchase_orders(
                access_token=token,
                branches=units,
                late_only=True,
                page=1,
                page_size=_COUNT_PAGE_SIZE,
            )
        except Exception:
            logger.warning("home_attention_source_failed source=purchase_orders")
            failures.append(
                {"source": "purchase_orders", "code": "source_unavailable"}
            )
            return _unavailable(card_id, title)

        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        try:
            count = int(summary.get("late_lines") or 0)
        except (TypeError, ValueError):
            count = 0

        return {
            "id": card_id,
            "title": title,
            "description": "Linhas de pedidos de compra em aberto com entrega prevista vencida.",
            "count": count,
            "countUnit": "linhas",
            "status": "available",
            "target": _view_target("purchase_orders", "late_only=true"),
        }

    def _late_deliveries_card(
        self,
        token: str,
        units: list[str],
        failures: list[dict[str, Any]],
    ) -> dict[str, Any]:
        card_id = "late_deliveries"
        title = "Recebimentos em atraso"
        start, end = current_month_bounds(self._today())
        count = 0
        try:
            for branch in units:
                panel = self.delpi_reads.get_purchase_order_otd_panel(
                    access_token=token,
                    branch=branch,
                    start_date=start,
                    end_date=end,
                    status="late",
                    page=1,
                    page_size=_COUNT_PAGE_SIZE,
                )
                summary = (
                    panel.get("summary")
                    if isinstance(panel.get("summary"), dict)
                    else {}
                )
                try:
                    count += int(summary.get("late_lines") or 0)
                except (TypeError, ValueError):
                    continue
        except Exception:
            logger.warning("home_attention_source_failed source=late_deliveries")
            failures.append(
                {"source": "late_deliveries", "code": "source_unavailable"}
            )
            return _unavailable(card_id, title)

        return {
            "id": card_id,
            "title": title,
            "description": "Linhas de recebimento digitadas no mês corrente que chegaram após a data prometida.",
            "count": count,
            "countUnit": "linhas",
            "status": "available",
            "target": _view_target("deliveries", "status=late"),
        }

    def _safety_stock_card(
        self,
        token: str,
        units: list[str],
        failures: list[dict[str, Any]],
        user: EffectiveUser,
    ) -> dict[str, Any]:
        card_id = "safety_stock_below"
        title = "Itens abaixo do estoque de segurança"
        try:
            count = 0
            for branch in units:
                summary = self.delpi_reads.get_safety_stock_summary(
                    access_token=token,
                    branch=branch,
                )
                try:
                    count += int(summary.get("below_safety_stock") or 0)
                except (TypeError, ValueError):
                    continue
        except Exception:
            logger.warning("home_attention_source_failed source=safety_stock")
            failures.append(
                {"source": "safety_stock", "code": "source_unavailable"}
            )
            return _unavailable(card_id, title)

        target = None
        if user.has_permission(SAFETY_STOCK_APP_ACCESS):
            target = {"kind": "href", "href": SAFETY_STOCK_APP_HREF}

        return {
            "id": card_id,
            "title": title,
            "description": "Itens com saldo disponível abaixo do estoque de segurança.",
            "count": count,
            "countUnit": "itens",
            "status": "available",
            "target": target,
        }
