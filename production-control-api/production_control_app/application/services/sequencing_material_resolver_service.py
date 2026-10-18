"""Serviço de aplicação: resolve o material de cada operação em lote — RS E2.

Owner da etapa de I/O: deduplica OPs por filial, fatia respeitando o teto da
api-delpi, paraleliza com pool limitado e devolve a classificação por operação
do resolvedor de domínio (``sequencing_material_resolution``). Nunca reordena,
nunca grava fila/snapshot, nunca cria/vincula perfil — leitura pura.

Fail-closed: lote que falhou → SOURCE_UNAVAILABLE; resposta malformada →
INCOMPLETE; OPs acima do teto de janela → INCOMPLETE (nunca trunca nem
classifica como ausência real de cabo). Erros de integração propagam como
``DelpiGatewayError`` apenas se o próprio gateway falhar antes do lote.
"""

from __future__ import annotations

from typing import Any, Sequence

from production_control_app.application.services.integration_batches import (
    commitment_batch_size,
    fan_out,
    max_commitment_batches,
)
from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
)
from production_control_app.domain.services.sequencing_material_resolution import (
    RESOLUTION_STATUSES,
    material_criterion_params,
    resolve_operations_materials,
)


class SequencingMaterialResolverService:
    """Resolve materiais de sequenciamento por (filial, CT, OP, operação)."""

    def __init__(self, production_gateway: Any):
        self._gateway = production_gateway

    def resolve_materials(
        self,
        *,
        branch: str,
        work_center: str,
        operations: Sequence[dict[str, Any]],
        criteria: Any,
    ) -> dict[str, Any]:
        """Classifica cada operação pelo critério ``material_code`` do perfil.

        ``operations`` são itens da fila WORKING (leitura): ``work_center``,
        ``production_order``, ``operation_code``. ``criteria`` é a lista de
        critérios já validada/persistida do perfil.
        """
        scope = {
            "branch": str(branch or "").strip(),
            "work_center": str(work_center or "").strip(),
        }
        params = material_criterion_params(criteria)
        ops = list(operations or [])
        if params is None:
            return {
                **scope,
                "material_criterion": False,
                "items": [],
                "summary": self._summary(ops, []),
            }

        orders, overflow = self._dedupe_orders(ops)
        items_by_order, unavailable, incomplete = self._fetch_orders(
            branch=scope["branch"], production_orders=orders
        )
        incomplete |= overflow

        items = resolve_operations_materials(
            operations=ops,
            items_by_order=items_by_order,
            params=params,
            unavailable_orders=unavailable,
            incomplete_orders=incomplete,
        )
        return {
            **scope,
            "material_criterion": True,
            "items": items,
            "summary": self._summary(ops, items),
        }

    @staticmethod
    def _dedupe_orders(
        operations: Sequence[dict[str, Any]],
    ) -> tuple[list[str], set[str]]:
        """OPs distintas preservando a ordem; excedentes vão para INCOMPLETE."""
        ceiling = commitment_batch_size() * max_commitment_batches()
        orders: list[str] = []
        seen: set[str] = set()
        for item in operations:
            order = normalize_order_code(item.get("production_order"))
            if order and order not in seen:
                seen.add(order)
                orders.append(order)
        if len(orders) <= ceiling:
            return orders, set()
        # Não trunca: OPs além do teto são marcadas INCOMPLETE, não MISSING.
        return orders[:ceiling], set(orders[ceiling:])

    def _fetch_orders(
        self,
        *,
        branch: str,
        production_orders: Sequence[str],
    ) -> tuple[dict[str, list[dict[str, Any]]], set[str], set[str]]:
        """Busca empenhos em lotes paralelos; falha isola o próprio lote."""
        size = commitment_batch_size()
        orders = list(production_orders)
        chunks = [orders[start : start + size] for start in range(0, len(orders), size)]

        items_by_order: dict[str, list[dict[str, Any]]] = {}
        unavailable: set[str] = set()
        incomplete: set[str] = set()
        for outcome in fan_out(
            lambda chunk: self._fetch_chunk(branch=branch, chunk=chunk),
            chunks,
            failure="Não foi possível carregar os materiais das ordens de produção.",
        ):
            chunk_orders, chunk_items, state = outcome
            if state == "unavailable":
                unavailable.update(chunk_orders)
                continue
            if state == "incomplete":
                incomplete.update(chunk_orders)
                continue
            for item in chunk_items:
                order = normalize_order_code(item.get("production_order"))
                if order:
                    items_by_order.setdefault(order, []).append(item)
        return items_by_order, unavailable, incomplete

    def _fetch_chunk(
        self, *, branch: str, chunk: list[str]
    ) -> tuple[list[str], list[dict[str, Any]], str]:
        """Um lote: (OPs, itens, ok|unavailable|incomplete). Nunca levanta."""
        try:
            payload = self._gateway.fetch_operation_materials_batch(
                branch=branch,
                production_orders=chunk,
            )
        except Exception:  # noqa: BLE001 — falha externa isola o lote
            return chunk, [], "unavailable"
        items = _items(payload)
        if items is None:
            return chunk, [], "incomplete"
        return chunk, items, "ok"

    @staticmethod
    def _summary(
        operations: Sequence[dict[str, Any]], items: Sequence[dict[str, Any]]
    ) -> dict[str, Any]:
        counts = {status: 0 for status in sorted(RESOLUTION_STATUSES)}
        for item in items:
            status = str(item.get("status"))
            if status in counts:
                counts[status] += 1
        counts["total"] = len(operations)
        return counts


def _items(payload: Any) -> list[dict[str, Any]] | None:
    """Extrai ``items`` do envelope; ``None`` = resposta malformada."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    source = data if isinstance(data, dict) else payload
    rows = source.get("items") if isinstance(source, dict) else None
    if not isinstance(rows, list):
        return None
    return [row for row in rows if isinstance(row, dict)]
