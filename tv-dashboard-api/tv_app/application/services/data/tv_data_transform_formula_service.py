"""Parse de fórmulas tipadas da barra fx (paridade com dataTransformFormula.ts)."""

from __future__ import annotations

import json
import re
from typing import Any

_ADD_COLUMN_FULL = re.compile(
    r"^=\s*AddColumn\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(.+)\s*\)\s*$",
    re.IGNORECASE,
)
_RENAME_FULL = re.compile(
    r"^=\s*RenameColumns\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*→\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*$",
    re.IGNORECASE,
)
_SELECT_FULL = re.compile(
    r"^=\s*SelectColumns\s*\(\s*Fonte\s*,\s*\[([^\]]*)\]\s*\)\s*$",
    re.IGNORECASE,
)
_FILTER_NOT_NULL = re.compile(
    r"^=\s*FilterRows\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s+is\s+not\s+null\s*\)\s*$",
    re.IGNORECASE,
)
_FILTER_CMP = re.compile(
    r"^=\s*FilterRows\s*\(\s*Fonte\s*,\s*\[([A-Za-z_][A-Za-z0-9_]*)\]\s+"
    r"(eq|neq|gt|lt|contains|startsWith)\s+(.+)\s*\)\s*$",
    re.IGNORECASE,
)
_SORT_FULL = re.compile(
    r"^=\s*Sort\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(asc|desc)\s*\)\s*$",
    re.IGNORECASE,
)
_REPLACE_FULL = re.compile(
    r"^=\s*ReplaceValue\s*\(\s*Fonte\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(.+?)\s*→\s*(.+)\s*\)\s*$",
    re.IGNORECASE,
)

_EDITABLE_OPS = frozenset({"addColumn", "rename", "select", "filter", "sort", "replace"})


def can_edit_formula(step: dict[str, Any] | None) -> bool:
    if not isinstance(step, dict):
        return False
    return str(step.get("op") or "") in _EDITABLE_OPS


def _strip_outer_quotes(raw: str) -> str:
    trimmed = (raw or "").strip()
    if (trimmed.startswith('"') and trimmed.endswith('"')) or (
        trimmed.startswith("'") and trimmed.endswith("'")
    ):
        try:
            return json.loads(trimmed if trimmed.startswith('"') else f'"{trimmed[1:-1]}"')
        except json.JSONDecodeError:
            return trimmed[1:-1]
    try:
        return json.loads(trimmed)
    except json.JSONDecodeError:
        return trimmed


def _ok(step: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "step": step}


def _err(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


def parse_add_column_formula(text: str, *, existing_name: str | None = None) -> dict[str, Any]:
    trimmed = (text or "").strip()
    if not trimmed:
        return _err("Informe a expressão da coluna.")
    full = _ADD_COLUMN_FULL.match(trimmed)
    if full:
        name = full.group(1).strip()
        expr = full.group(2).strip()
        if not name or not expr:
            return _err("AddColumn exige nome e expressão.")
        return _ok({"op": "addColumn", "name": name, "expr": expr})
    if trimmed.startswith("=") and re.search(r"AddColumn", trimmed, re.IGNORECASE):
        return _err("Use = AddColumn(Fonte, nome, expr) ou só a expressão.")
    name = (existing_name or "").strip()
    if name:
        expr = re.sub(r"^=\s*", "", trimmed)
        if not expr:
            return _err("Informe a expressão da coluna.")
        return _ok({"op": "addColumn", "name": name, "expr": expr})
    return _err("Para nova coluna use = AddColumn(Fonte, nome, expr).")


def parse_rename_formula(text: str) -> dict[str, Any]:
    match = _RENAME_FULL.match((text or "").strip())
    if not match:
        return _err("Use = RenameColumns(Fonte, de → para).")
    return _ok({"op": "rename", "from": match.group(1), "to": match.group(2)})


def parse_select_formula(text: str) -> dict[str, Any]:
    match = _SELECT_FULL.match((text or "").strip())
    if not match:
        return _err("Use = SelectColumns(Fonte, [col1, col2]).")
    columns = [
        part.strip().strip("\"'")
        for part in (match.group(1) or "").split(",")
        if part.strip()
    ]
    if not columns:
        return _err("Informe ao menos uma coluna.")
    return _ok({"op": "select", "columns": columns})


def parse_filter_formula(text: str) -> dict[str, Any]:
    trimmed = (text or "").strip()
    not_null = _FILTER_NOT_NULL.match(trimmed)
    if not_null:
        return _ok({"op": "filter", "column": not_null.group(1), "cmp": "notNull"})
    cmp_match = _FILTER_CMP.match(trimmed)
    if not cmp_match:
        return _err('Use = FilterRows(Fonte, [col] eq "valor") ou … is not null.')
    return _ok(
        {
            "op": "filter",
            "column": cmp_match.group(1),
            "cmp": cmp_match.group(2),
            "value": _strip_outer_quotes(cmp_match.group(3) or ""),
        }
    )


def parse_sort_formula(text: str) -> dict[str, Any]:
    match = _SORT_FULL.match((text or "").strip())
    if not match:
        return _err("Use = Sort(Fonte, coluna, asc|desc).")
    return _ok(
        {
            "op": "sort",
            "column": match.group(1),
            "direction": "desc" if match.group(2).lower() == "desc" else "asc",
        }
    )


def parse_replace_formula(text: str) -> dict[str, Any]:
    match = _REPLACE_FULL.match((text or "").strip())
    if not match:
        return _err('Use = ReplaceValue(Fonte, coluna, "a" → "b").')
    return _ok(
        {
            "op": "replace",
            "column": match.group(1),
            "find": _strip_outer_quotes(match.group(2) or ""),
            "replaceWith": _strip_outer_quotes(match.group(3) or ""),
        }
    )


def parse_formula_bar_text(
    text: str,
    *,
    step: dict[str, Any] | None = None,
    new_column_draft: bool = False,
) -> dict[str, Any]:
    if new_column_draft:
        return parse_add_column_formula(text)
    if not can_edit_formula(step):
        return _err("Esta etapa não é editável pela barra fx.")
    assert step is not None
    op = str(step.get("op") or "")
    if op == "addColumn":
        return parse_add_column_formula(text, existing_name=str(step.get("name") or ""))
    if op == "rename":
        return parse_rename_formula(text)
    if op == "select":
        return parse_select_formula(text)
    if op == "filter":
        return parse_filter_formula(text)
    if op == "sort":
        return parse_sort_formula(text)
    if op == "replace":
        return parse_replace_formula(text)
    return _err("Etapa não suportada na barra fx.")
