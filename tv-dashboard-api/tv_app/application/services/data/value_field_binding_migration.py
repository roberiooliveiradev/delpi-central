"""Motor genérico de migração semântica de bindings persistidos `field=="value"`.

Cada wave declara um *spec* operação -> campo canônico:

- SI meta (Wave 2): `get_si_indicator_*_meta` -> `comparable_goal`;
- parity alias (Wave 3): `PARITY_ALIAS_FIELD_MAP` mapeia operationIds
  exatos para o campo semântico já emitido pelo producer.

Blocos de apresentação (`text`, `kpi`, `chart`, `table`) não carregam o
operationId — a resolução segue `dataSourceId` -> bloco `data_source`
-> `dataBinding.operationId`. Um bloco também pode carregar
`dataBinding.operationId` diretamente.

Escopo estrito do predicado:
- a ref de campo tem valor exato "value" (comparação exata, nunca prefixo);
- o operationId resolvido está no spec da wave;
- qualquer outro caso (realized, meta já migrado, presentation value,
  domain value) permanece intacto.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Mapping

FIELD_REF_KEYS = frozenset(
    {"valueField", "field", "dataField", "metricField"}
)
FIELD_REF_LIST_KEYS = frozenset({"selectedValueFields"})
LEGACY_FIELD = "value"

SI_META_PREFIX = "get_si_indicator_"
SI_META_SUFFIX = "_meta"
SI_META_CANONICAL_FIELD = "comparable_goal"

# Wave 3 — operationId exato -> campo semântico canônico emitido pelo producer.
PARITY_ALIAS_FIELD_MAP: dict[str, str] = {
    "get_nonconformity_streak": "current_days_without_nc",
    "get_audit_5s_summary": "average_score",
    "get_quality_scrap_cost_pct": "scrap_cost_pct",
    "get_quality_rework_cost_pct": "rework_cost_pct",
}


def si_meta_canonical_field(operation_id: str | None) -> str | None:
    op = str(operation_id or "").strip()
    if op.startswith(SI_META_PREFIX) and op.endswith(SI_META_SUFFIX):
        return SI_META_CANONICAL_FIELD
    return None


def parity_alias_canonical_field(operation_id: str | None) -> str | None:
    return PARITY_ALIAS_FIELD_MAP.get(str(operation_id or "").strip())


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


def collect_value_refs(
    native_config: Any,
    canonical_field_for: Callable[[str | None], str | None],
) -> list[dict[str, Any]]:
    """Refs `field == "value"` cujo bloco resolve para uma op do spec."""
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
            canonical = canonical_field_for(operation_id)
            if canonical is None:
                continue
            found: list[tuple] = []
            _iter_field_refs(block, "", found)
            for field_path, container, key, index in found:
                refs.append(
                    {
                        "block_id": block.get("id"),
                        "field_path": field_path,
                        "operationId": operation_id,
                        "canonical_field": canonical,
                        "container": container,
                        "key": key,
                        "index": index,
                    }
                )
    return refs


def migrate_native_config(
    native_config: Any,
    canonical_field_for: Callable[[str | None], str | None] | Mapping[str, str],
) -> tuple[Any, list[dict[str, Any]]]:
    """Retorna (config migrado, refs aplicadas). Idempotente: rerun retorna 0 refs."""
    if isinstance(canonical_field_for, Mapping):
        mapping = dict(canonical_field_for)
        resolver = lambda op: mapping.get(str(op or "").strip())
    else:
        resolver = canonical_field_for
    refs = collect_value_refs(native_config, resolver)
    if not refs:
        return native_config, []
    migrated = copy.deepcopy(native_config)
    # Re-resolve no deepcopy: containers apontam para o doc migrado.
    for migrated_ref in collect_value_refs(migrated, resolver):
        container = migrated_ref["container"]
        if migrated_ref["index"] is None:
            container[migrated_ref["key"]] = migrated_ref["canonical_field"]
        else:
            container[migrated_ref["index"]] = migrated_ref["canonical_field"]
    applied = [
        {
            "block_id": r["block_id"],
            "field_path": r["field_path"],
            "operationId": r["operationId"],
            "canonical_field": r["canonical_field"],
        }
        for r in refs
    ]
    return migrated, applied
