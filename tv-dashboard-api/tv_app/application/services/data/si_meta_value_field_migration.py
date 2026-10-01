"""Wave 2 — migração semântica de bindings persistidos SI meta.

`field: "value"` em blocos ligados a `get_si_indicator_*_meta` migra para
`comparable_goal` (campo canônico emitido pelo producer SI para metas).

Blocos de apresentação (`text`, `kpi`, `chart`, `table`) não carregam o
operationId — a resolução segue `dataSourceId` -> bloco `data_source`
-> `dataBinding.operationId`. Um bloco também pode carregar
`dataBinding.operationId` diretamente.

Escopo estrito do predicado:
- a ref de campo tem valor exato "value" (comparação exata, nunca prefixo);
- o operationId resolvido casa `get_si_indicator_*_meta`;
- qualquer outro caso (realized, não-SI, presentation value, domain value)
  permanece intacto.
"""

from __future__ import annotations

import copy
from typing import Any

FIELD_REF_KEYS = frozenset(
    {"valueField", "field", "dataField", "metricField"}
)
FIELD_REF_LIST_KEYS = frozenset({"selectedValueFields"})
LEGACY_FIELD = "value"
CANONICAL_FIELD = "comparable_goal"
SI_META_PREFIX = "get_si_indicator_"
SI_META_SUFFIX = "_meta"


def _is_si_meta_operation(operation_id: str | None) -> bool:
    op = str(operation_id or "").strip()
    return op.startswith(SI_META_PREFIX) and op.endswith(SI_META_SUFFIX)


def _iter_block_lists(node: Any):
    """Yield `blocks` lists wherever they appear in a native_config doc."""
    if isinstance(node, dict):
        blocks = node.get("blocks")
        if isinstance(blocks, list):
            yield blocks
        for value in node.values():
            yield from _iter_block_lists(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_block_lists(item)


def _resolve_operation_id(block: dict[str, Any], blocks_by_id: dict[str, dict]) -> str | None:
    binding = block.get("dataBinding")
    if isinstance(binding, dict):
        op = str(binding.get("operationId") or "").strip()
        if op:
            return op
    source = blocks_by_id.get(str(block.get("dataSourceId") or ""))
    if isinstance(source, dict):
        binding = source.get("dataBinding")
        if isinstance(binding, dict):
            op = str(binding.get("operationId") or "").strip()
            if op:
                return op
    return None


def _iter_field_refs(node: Any, path: str, out: list[tuple[str, Any]]):
    """Collect (path, container) for every field reference equal to 'value'."""
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if key in FIELD_REF_KEYS and value == LEGACY_FIELD:
                out.append((child, node, key, None))
            elif key in FIELD_REF_LIST_KEYS and isinstance(value, list):
                for index, item in enumerate(value):
                    if item == LEGACY_FIELD:
                        out.append((f"{child}[{index}]", value, None, index))
            _iter_field_refs(value, child, out)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _iter_field_refs(item, f"{path}[{index}]", out)


def collect_si_meta_value_refs(native_config: Any) -> list[dict[str, Any]]:
    """Refs `field == "value"` cujo bloco resolve para `get_si_indicator_*_meta`."""
    refs: list[dict[str, Any]] = []
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
            if not _is_si_meta_operation(operation_id):
                continue
            found: list[tuple] = []
            _iter_field_refs(block, "", found)
            for field_path, container, key, index in found:
                refs.append(
                    {
                        "block_id": block.get("id"),
                        "field_path": field_path,
                        "operationId": operation_id,
                        "container": container,
                        "key": key,
                        "index": index,
                    }
                )
    return refs


def migrate_native_config(native_config: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Retorna (config migrado, refs aplicadas). Idempotente: rerun retorna 0 refs."""
    refs = collect_si_meta_value_refs(native_config)
    if not refs:
        return native_config, []
    migrated = copy.deepcopy(native_config)
    # Re-resolve no deepcopy: containers apontam para o doc migrado.
    for migrated_ref in collect_si_meta_value_refs(migrated):
        container = migrated_ref["container"]
        if migrated_ref["index"] is None:
            container[migrated_ref["key"]] = CANONICAL_FIELD
        else:
            container[migrated_ref["index"]] = CANONICAL_FIELD
    applied = [
        {"block_id": r["block_id"], "field_path": r["field_path"], "operationId": r["operationId"]}
        for r in refs
    ]
    return migrated, applied
