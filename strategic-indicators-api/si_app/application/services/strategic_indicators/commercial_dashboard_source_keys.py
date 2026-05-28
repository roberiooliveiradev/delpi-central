"""Mapeamento de source_key legado do dashboard → indicador commercial-rol por filial."""

from __future__ import annotations

COMMERCIAL_ROL_SOURCE_KEY = "commercial_rol"

LEGACY_ROL_SOURCE_KEYS = frozenset(
    {
        "commercial_head_office_rol_target",
        "commercial_branch_rol_target",
    }
)

LEGACY_ROL_SOURCE_KEY_BRANCH: dict[str, str] = {
    "commercial_head_office_rol_target": "01",
    "commercial_branch_rol_target": "02",
}


def expand_dashboard_source_keys(source_keys: list[str]) -> list[str]:
    """Inclui commercial_rol quando o dashboard ainda pede chaves ROL legadas."""
    expanded = list(source_keys)
    for key in source_keys:
        if key in LEGACY_ROL_SOURCE_KEYS and COMMERCIAL_ROL_SOURCE_KEY not in expanded:
            expanded.append(COMMERCIAL_ROL_SOURCE_KEY)
    return expanded


def legacy_rol_branch_override(source_key: str, branch: str | None) -> str | None:
    """Filial implícita nas rotas antigas de ROL matriz/filial."""
    if branch:
        return branch
    return LEGACY_ROL_SOURCE_KEY_BRANCH.get(source_key)
