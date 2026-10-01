"""Wave 2 — migração semântica de bindings persistidos SI meta.

`field: "value"` em blocos ligados a `get_si_indicator_*_meta` migra para
`comparable_goal` (campo canônico emitido pelo producer SI para metas).

O motor de scan/migração vive em `value_field_binding_migration` (uma única
fonte para waves de normalização do campo `value`); este módulo preserva a
API pública usada pelo runner e pelos testes da Wave 2.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.value_field_binding_migration import (
    FIELD_REF_KEYS,
    FIELD_REF_LIST_KEYS,
    LEGACY_FIELD,
    SI_META_CANONICAL_FIELD as CANONICAL_FIELD,
    SI_META_PREFIX,
    SI_META_SUFFIX,
    _iter_block_lists,
    _iter_field_refs,
    _resolve_operation_id,
    collect_value_refs,
    migrate_native_config as _migrate_native_config,
    si_meta_canonical_field,
)

__all__ = [
    "FIELD_REF_KEYS",
    "FIELD_REF_LIST_KEYS",
    "LEGACY_FIELD",
    "CANONICAL_FIELD",
    "SI_META_PREFIX",
    "SI_META_SUFFIX",
    "collect_si_meta_value_refs",
    "migrate_native_config",
]


def _is_si_meta_operation(operation_id: str | None) -> bool:
    return si_meta_canonical_field(operation_id) is not None


def collect_si_meta_value_refs(native_config: Any) -> list[dict[str, Any]]:
    """Refs `field == "value"` cujo bloco resolve para `get_si_indicator_*_meta`."""
    return collect_value_refs(native_config, si_meta_canonical_field)


def migrate_native_config(native_config: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Retorna (config migrado, refs aplicadas). Idempotente: rerun retorna 0 refs."""
    return _migrate_native_config(native_config, si_meta_canonical_field)
