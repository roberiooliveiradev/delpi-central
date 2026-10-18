"""Serviço de aplicação: resolve o material de cada operação em lote — RS E2.

Owner da etapa de I/O: valida o escopo (filial + CT + identidade), deduplica
OPs, fatia respeitando o teto da api-delpi, paraleliza com pool limitado,
valida integralmente cada resposta e devolve a classificação por operação do
resolvedor de domínio (``sequencing_material_resolution``). Nunca reordena,
nunca grava fila/snapshot, nunca cria/vincula perfil — leitura pura.

Fail-closed:
* escopo inválido → ``ValueError`` antes de qualquer consulta externa;
* lote que falhou (timeout/erro) → SOURCE_UNAVAILABLE;
* resposta malformada, de outra filial ou com registros estranhos às OPs
  pedidas → INCOMPLETE (nunca MISSING — falha de integração não é ausência
  real de cabo);
* OPs acima do teto de janela → INCOMPLETE (sem truncamento silencioso).
"""

from __future__ import annotations

from typing import Any, Sequence

from production_control_app.application.services.integration_batches import (
    commitment_batch_size,
    fan_out,
    max_commitment_batches,
)
from production_control_app.domain.services.line_feeder_requirements import (
    _normalize_operation_code,
)
from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
)
from production_control_app.domain.services.sequencing_material_resolution import (
    RESOLUTION_STATUSES,
    _count,
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
        ``production_order``, ``operation_code``. A filial canônica é a do
        snapshot carregado pelo backend (``branch``); uma operação que declare
        outra filial explicitamente é rejeitada. ``criteria`` é a lista de
        critérios já validada/persistida do perfil.
        """
        scope = self._validate_scope(
            branch=branch, work_center=work_center, operations=operations
        )
        params = material_criterion_params(criteria)
        ops = scope["operations"]
        if params is None:
            return {
                "branch": scope["branch"],
                "work_center": scope["work_center"],
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
            "branch": scope["branch"],
            "work_center": scope["work_center"],
            "material_criterion": True,
            "items": items,
            "summary": self._summary(ops, items),
        }

    @staticmethod
    def _validate_scope(
        *,
        branch: Any,
        work_center: Any,
        operations: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        """Escopo íntegro antes de qualquer I/O — entrada inválida não consulta.

        Cada operação deve pertencer ao CT atual solicitado (operação
        transferida traz o CT de destino, que é o que conta) e não pode
        declarar filial diferente do contexto. OP e operação são obrigatórias
        e preservadas como texto (zeros à esquerda inclusos).
        """
        branch_code = str(branch or "").strip()
        if not branch_code:
            raise ValueError("Filial é obrigatória para resolver materiais.")
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("Centro de trabalho é obrigatório para resolver materiais.")

        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(operations or ()):  # noqa: B007
            if not isinstance(item, dict):
                raise ValueError(f"Operação #{index + 1} inválida para a resolução.")
            declared_branch = str(item.get("branch") or "").strip()
            if declared_branch and declared_branch != branch_code:
                raise ValueError(
                    "Operação de outra filial fora do escopo da resolução."
                )
            op_center = str(item.get("work_center") or "").strip()
            if not op_center or op_center != center:
                raise ValueError(
                    "Operação fora do centro de trabalho solicitado."
                )
            order = normalize_order_code(item.get("production_order"))
            operation = str(item.get("operation_code") or "").strip()
            if not order or not _normalize_operation_code(operation):
                raise ValueError(
                    "Operação sem OP ou código de operação válido."
                )
            normalized.append(
                {**item, "branch": branch_code, "work_center": center}
            )
        return {
            "branch": branch_code,
            "work_center": center,
            "operations": normalized,
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
        items = _validated_items(payload, branch=branch, requested=chunk)
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


def _validated_items(
    payload: Any, *, branch: str, requested: Sequence[str]
) -> list[dict[str, Any]] | None:
    """Extrai ``items`` só se a resposta for íntegra; ``None`` = malformada.

    Validação integral: envelope dict que não declare ``success: false``,
    lista ``items`` coerente com ``summary.returned_count`` quando presente,
    filial do envelope e das linhas coerente com a pedida, toda linha é dict
    com OP presente e pertencente ao conjunto solicitado. ``items: []`` é
    resposta válida (OPs sem empenho), não confundir com resposta quebrada.
    Nenhum registro é descartado silenciosamente — um item estranho invalida
    o lote inteiro, porque não dá para provar qual OP ele representaria.
    """
    if not isinstance(payload, dict):
        return None
    if payload.get("success") is False:
        return None
    data = payload.get("data")
    source = data if isinstance(data, dict) else payload
    rows = source.get("items") if isinstance(source, dict) else None
    if not isinstance(rows, list):
        return None

    summary = source.get("summary")
    if isinstance(summary, dict) and "returned_count" in summary:
        declared = _count(summary.get("returned_count"))
        if declared is None or declared != len(rows):
            return None

    if str(source.get("branch") or "").strip() and (
        str(source.get("branch")).strip() != branch
    ):
        return None

    echoed = source.get("production_orders")
    if isinstance(echoed, list):
        covered = {normalize_order_code(order) for order in echoed}
        if any(normalize_order_code(order) not in covered for order in requested):
            return None

    wanted = {normalize_order_code(order) for order in requested}
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        order = normalize_order_code(row.get("production_order"))
        if not order or order not in wanted:
            return None
        row_branch = str(row.get("branch") or "").strip()
        if row_branch and row_branch != branch:
            return None
        items.append(row)
    return items
