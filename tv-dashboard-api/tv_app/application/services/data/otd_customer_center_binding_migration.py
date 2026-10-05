"""Migração governada do campo sintético `cliente_loja_centro` → `customer_center`.

Contexto: rotas OTD por cliente passaram a emitir `customer_center`
(SA7010.A7_XCENT) no payload. Slides persistidos ainda derivam o centro por
transform sintético (addColumn sobre nome/loja/param de filtro). A migração:

- remove etapas produtoras de `cliente_loja_centro` (addColumn/rename), que
  deixariam de ser authority do centro e poderiam mascarar o campo da API;
- reescreve referências consumidoras `cliente_loja_centro` → `customer_center`
  em field refs, listas de colunas, dataRef e expressões de transform;
- preserva textos de exibição (label/title/description), que não são refs.

Escopo estrito: somente blocos cujo operationId resolve para uma rota OTD que
emite `customer_center` no payload (ou a composta legada que migra para elas).
"""

from __future__ import annotations

import copy
import re
from typing import Any

from tv_app.application.services.data.value_field_binding_migration import (
    _iter_block_lists,
    _resolve_operation_id,
)

LEGACY_FIELD = "cliente_loja_centro"
CANONICAL_FIELD = "customer_center"

# Rotas cujo payload carrega customer_center (grão cliente/loja ou linha) +
# composta legada cujo binding migra para by-customer.
TARGET_OPERATION_IDS = frozenset(
    {
        "get_sales_order_otd_by_customer",
        "get_sales_order_otd_series_by_customer",
        "get_sales_order_otd_panel",
        "get_commercial_sales_order_otd_analysis",
    }
)

_PRODUCER_OUTPUT_KEYS = frozenset({"name", "to", "newColumn", "outputField"})
_DISPLAY_TEXT_KEYS = frozenset(
    {"label", "title", "text", "caption", "description", "message", "whenToUse"}
)
_LEGACY_TOKEN_RE = re.compile(rf"(?<![\w]){re.escape(LEGACY_FIELD)}(?![\w])")


def _is_producer_step(node: Any) -> bool:
    if not isinstance(node, dict) or not str(node.get("op") or "").strip():
        return False
    return any(
        str(node.get(key) or "").strip() == LEGACY_FIELD
        for key in _PRODUCER_OUTPUT_KEYS
    )


def _migrate_block_subtree(
    node: Any,
    path: str,
    refs: list[dict[str, Any]],
) -> Any:
    """Reescreve refs e remove etapas produtoras do campo legado."""
    if isinstance(node, str):
        if node == LEGACY_FIELD:
            refs.append({"kind": "field_ref", "field_path": path})
            return CANONICAL_FIELD
        if _LEGACY_TOKEN_RE.search(node):
            refs.append({"kind": "expression_ref", "field_path": path})
            return _LEGACY_TOKEN_RE.sub(CANONICAL_FIELD, node)
        return node
    if isinstance(node, list):
        next_items: list[Any] = []
        for index, item in enumerate(node):
            child = f"{path}[{index}]"
            if _is_producer_step(item):
                refs.append({"kind": "producer_step", "field_path": child})
                continue
            next_items.append(_migrate_block_subtree(item, child, refs))
        return next_items
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if key in _DISPLAY_TEXT_KEYS:
                out[key] = value
                continue
            out[key] = _migrate_block_subtree(value, child, refs)
        return out
    return node


def collect_customer_center_refs(native_config: Any) -> list[dict[str, Any]]:
    """Refs/produtores de `cliente_loja_centro` em blocos das rotas-alvo."""
    found: list[dict[str, Any]] = []
    for blocks in _iter_block_lists(native_config):
        by_id = {
            str(b.get("id")): b
            for b in blocks
            if isinstance(b, dict) and b.get("id")
        }
        for block in blocks:
            if not isinstance(block, dict):
                continue
            operation_id = _resolve_operation_id(block, by_id)
            if operation_id not in TARGET_OPERATION_IDS:
                continue
            probes: list[dict[str, Any]] = []
            _migrate_block_subtree(block, "", probes)
            for probe in probes:
                probe["block_id"] = block.get("id")
                probe["operationId"] = operation_id
                found.append(probe)
    return found


def migrate_native_config(native_config: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Retorna (config migrado, refs aplicadas). Idempotente: rerun retorna 0 refs."""
    refs = collect_customer_center_refs(native_config)
    if not refs:
        return native_config, []
    migrated = copy.deepcopy(native_config)
    for blocks in _iter_block_lists(migrated):
        by_id = {
            str(b.get("id")): b
            for b in blocks
            if isinstance(b, dict) and b.get("id")
        }
        for index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            operation_id = _resolve_operation_id(block, by_id)
            if operation_id not in TARGET_OPERATION_IDS:
                continue
            applied: list[dict[str, Any]] = []
            blocks[index] = _migrate_block_subtree(block, "", applied)
    applied_refs = [
        {
            "block_id": ref["block_id"],
            "field_path": ref["field_path"],
            "kind": ref["kind"],
            "operationId": ref["operationId"],
            "canonical_field": CANONICAL_FIELD,
        }
        for ref in refs
    ]
    return migrated, applied_refs
