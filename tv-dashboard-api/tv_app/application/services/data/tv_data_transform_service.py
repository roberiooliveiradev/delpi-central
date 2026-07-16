"""Transformações tipo Power Query sobre payload tabular (antes da View)."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CMPS = frozenset({"eq", "neq", "gt", "lt", "notNull"})
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def normalize_data_transform(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list) or not steps_raw:
        return None
    steps: list[dict[str, Any]] = []
    for item in steps_raw:
        if not isinstance(item, dict):
            continue
        op = str(item.get("op") or "").strip()
        if op == "rename":
            frm = str(item.get("from") or "").strip()
            to = str(item.get("to") or "").strip()
            if frm and to:
                steps.append({"op": "rename", "from": frm, "to": to})
        elif op == "select":
            columns = [
                str(col).strip()
                for col in (item.get("columns") or [])
                if str(col).strip()
            ]
            if columns:
                steps.append({"op": "select", "columns": columns})
        elif op == "filter":
            column = str(item.get("column") or "").strip()
            cmp_ = str(item.get("cmp") or "").strip()
            if column and cmp_ in _CMPS:
                step: dict[str, Any] = {"op": "filter", "column": column, "cmp": cmp_}
                if "value" in item:
                    step["value"] = item.get("value")
                steps.append(step)
        elif op == "addColumn":
            name = str(item.get("name") or "").strip()
            expr = str(item.get("expr") or "").strip()
            if name and expr:
                steps.append({"op": "addColumn", "name": name, "expr": expr})
    return {"steps": steps} if steps else None


def coerce_payload_to_table(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        rows = [dict(row) for row in data if isinstance(row, dict)]
        columns: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for key in row.keys():
                key_s = str(key)
                if key_s not in seen:
                    seen.add(key_s)
                    columns.append(key_s)
        return {"columns": columns, "rows": rows}
    if isinstance(data, dict):
        for key in ("items", "rows", "data", "results", "values"):
            inner = data.get(key)
            if isinstance(inner, list):
                nested = coerce_payload_to_table(inner)
                if nested is not None:
                    return nested
    return None


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value == value:  # noqa: PLR0124
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def _compare_filter(cell: Any, cmp_: str, value: Any) -> bool:
    if cmp_ == "notNull":
        return cell is not None and str(cell).strip() != ""
    if cmp_ == "eq":
        return str(cell if cell is not None else "") == str(value if value is not None else "")
    if cmp_ == "neq":
        return str(cell if cell is not None else "") != str(value if value is not None else "")
    left = _as_number(cell)
    right = _as_number(value)
    if left is None or right is None:
        return False
    if cmp_ == "gt":
        return left > right
    if cmp_ == "lt":
        return left < right
    return False


def evaluate_safe_arithmetic_expr(expr: str, row: dict[str, Any]) -> float | None:
    trimmed = (expr or "").strip()
    if not trimmed:
        return None
    try:
        tree = ast.parse(trimmed, mode="eval")
    except SyntaxError:
        return None

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(
            node.value, bool
        ):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return float(_OPS[type(node.op)](_eval(node.operand)))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError
            return float(_OPS[type(node.op)](left, right))
        if isinstance(node, ast.Name):
            if not _IDENT_RE.match(node.id) or node.id not in row:
                raise ValueError("col")
            num = _as_number(row.get(node.id))
            if num is None:
                raise ValueError("nan")
            return num
        raise ValueError("node")

    try:
        value = _eval(tree)
        return value if value == value else None  # noqa: PLR0124
    except (ValueError, ZeroDivisionError, TypeError, KeyError):
        return None


def apply_data_transform_steps(
    table: dict[str, Any],
    steps: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    columns = [str(col) for col in (table.get("columns") or [])]
    rows = [dict(row) for row in (table.get("rows") or []) if isinstance(row, dict)]
    if not steps:
        return {"columns": columns, "rows": rows}

    for step in steps:
        op = str(step.get("op") or "")
        if op == "rename":
            frm = str(step.get("from") or "")
            to = str(step.get("to") or "")
            columns = [to if col == frm else col for col in columns]
            next_rows: list[dict[str, Any]] = []
            for row in rows:
                if frm not in row:
                    next_rows.append(row)
                    continue
                new_row = dict(row)
                new_row[to] = new_row.pop(frm)
                next_rows.append(new_row)
            rows = next_rows
        elif op == "select":
            keep = [str(col) for col in (step.get("columns") or []) if str(col).strip()]
            keep = [col for col in keep if col in columns or any(col in row for row in rows)]
            if keep:
                columns = keep
            rows = [{col: row.get(col) for col in columns} for row in rows]
        elif op == "filter":
            column = str(step.get("column") or "")
            cmp_ = str(step.get("cmp") or "")
            value = step.get("value")
            rows = [row for row in rows if _compare_filter(row.get(column), cmp_, value)]
        elif op == "addColumn":
            name = str(step.get("name") or "").strip()
            expr = str(step.get("expr") or "").strip()
            if not name or not expr:
                continue
            if name not in columns:
                columns.append(name)
            rows = [{**row, name: evaluate_safe_arithmetic_expr(expr, row)} for row in rows]

    return {"columns": columns, "rows": rows}


def apply_data_transform_to_payload(
    data: Any,
    transform: Any,
) -> tuple[Any, bool, dict[str, Any] | None]:
    normalized = normalize_data_transform(transform)
    steps = normalized.get("steps") if normalized else None
    if not steps:
        return data, False, coerce_payload_to_table(data)
    table = coerce_payload_to_table(data)
    if table is None:
        return data, False, None
    next_table = apply_data_transform_steps(table, steps)
    return next_table["rows"], True, next_table
