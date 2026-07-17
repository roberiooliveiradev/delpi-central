"""Transformações tipo Power Query sobre payload tabular (antes da View)."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any

from tv_app.application.services.data.data_transform_contract import read_data_transform
from tv_app.application.services.data.m_query.m_legacy_adapter import (
    normalize_legacy_transform,
    plan_to_legacy_steps,
)
from tv_app.application.services.series_points_extractor import unwrap_operational_data
from tv_app.domain.data_query.transform_plan import TransformPlan

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CMPS = frozenset({"eq", "neq", "gt", "lt", "notNull", "contains", "startsWith"})
_AGGS = frozenset({"sum", "avg", "min", "max", "count", "first"})
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}
_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
}
_FUNC_WHITELIST = frozenset(
    {"iff", "concat", "abs", "min", "max", "coalesce", "len", "lower", "upper", "trim"}
)
_IF_CALL_RE = re.compile(r"\bif\s*\(", re.IGNORECASE)


def _as_agg(raw: Any) -> str | None:
    value = str(raw or "").strip()
    return value if value in _AGGS else None


def normalize_data_transform(raw: Any) -> dict[str, Any] | None:
    result = read_data_transform(raw)
    return result.normalized


def coerce_payload_to_table(data: Any) -> dict[str, Any] | None:
    data = unwrap_operational_data(data)
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
        for key in ("items", "rows", "data", "results", "values", "records", "entries", "flow", "history"):
            inner = data.get(key)
            if isinstance(inner, list):
                nested = coerce_payload_to_table(inner)
                if nested is not None:
                    return nested
        scalar_rows: list[dict[str, Any]] = []
        for key, value in data.items():
            if value is None or value == "":
                continue
            if isinstance(value, (dict, list)):
                continue
            scalar_rows.append({"campo": key, "valor": value})
        if scalar_rows:
            return {"columns": ["campo", "valor"], "rows": scalar_rows}
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
    left = str(cell if cell is not None else "")
    right = str(value if value is not None else "")
    if cmp_ == "eq":
        return left == right
    if cmp_ == "neq":
        return left != right
    if cmp_ == "contains":
        return right in left
    if cmp_ == "startsWith":
        return left.startswith(right)
    ln = _as_number(cell)
    rn = _as_number(value)
    if ln is None or rn is None:
        return False
    if cmp_ == "gt":
        return ln > rn
    if cmp_ == "lt":
        return ln < rn
    return False


def _aggregate(values: list[Any], fn: str) -> Any:
    if fn == "count":
        return len(values)
    if fn == "first":
        return values[0] if values else None
    nums = [n for n in (_as_number(v) for v in values) if n is not None]
    if not nums:
        return None
    if fn == "sum":
        return float(sum(nums))
    if fn == "avg":
        return float(sum(nums) / len(nums))
    if fn == "min":
        return float(min(nums))
    if fn == "max":
        return float(max(nums))
    return None


def evaluate_safe_arithmetic_expr(expr: str, row: dict[str, Any]) -> float | None:
    """Compat: retorna só número; preferir evaluate_safe_column_expr."""
    return _as_number(evaluate_safe_column_expr(expr, row))


def evaluate_safe_column_expr(expr: str, row: dict[str, Any]) -> Any:
    """
    DSL segura de coluna calculada (sandbox AST).
    if(cond, a, b), concat(...), abs/min/max/coalesce/len/lower/upper/trim,
    aritmética e comparadores == != > >= < <=.
    """
    trimmed = (expr or "").strip()
    if not trimmed:
        return None
    rewritten = _IF_CALL_RE.sub("iff(", trimmed)
    try:
        tree = ast.parse(rewritten, mode="eval")
    except SyntaxError:
        return None

    def _truthy(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0 and value == value  # noqa: PLR0124
        return str(value).strip() != ""

    def _num(value: Any) -> float:
        num = _as_number(value)
        if num is None:
            raise ValueError("nan")
        return num

    def _eval(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return node.value
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return float(node.value)
            if isinstance(node.value, str):
                return node.value
            if node.value is None:
                return None
            raise ValueError("const")
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return float(_OPS[type(node.op)](_num(_eval(node.operand))))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            left = _num(_eval(node.left))
            right = _num(_eval(node.right))
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError
            return float(_OPS[type(node.op)](left, right))
        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("cmp")
            op_type = type(node.ops[0])
            if op_type not in _CMP_OPS:
                raise ValueError("cmpop")
            left = _eval(node.left)
            right = _eval(node.comparators[0])
            ln = _as_number(left)
            rn = _as_number(right)
            if ln is not None and rn is not None:
                return bool(_CMP_OPS[op_type](ln, rn))
            return bool(
                _CMP_OPS[op_type](
                    str(left if left is not None else ""),
                    str(right if right is not None else ""),
                )
            )
        if isinstance(node, ast.Name):
            if not _IDENT_RE.match(node.id) or node.id not in row:
                raise ValueError("col")
            cell = row.get(node.id)
            if cell is None or (isinstance(cell, str) and cell.strip() == ""):
                return None
            return cell
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("call")
            fname = node.func.id
            if fname not in _FUNC_WHITELIST:
                raise ValueError("fn")
            if node.keywords:
                raise ValueError("kw")
            args = [_eval(arg) for arg in node.args]
            if fname == "iff":
                if len(args) != 3:
                    raise ValueError("iff")
                return args[1] if _truthy(args[0]) else args[2]
            if fname == "concat":
                return "".join("" if a is None else str(a) for a in args)
            if fname == "abs":
                if len(args) != 1:
                    raise ValueError("abs")
                return abs(_num(args[0]))
            if fname in {"min", "max"}:
                if len(args) < 1:
                    raise ValueError(fname)
                nums = [_num(a) for a in args]
                return float(min(nums) if fname == "min" else max(nums))
            if fname == "coalesce":
                for arg in args:
                    if arg is not None and not (isinstance(arg, str) and arg.strip() == ""):
                        return arg
                return None
            if fname == "len":
                if len(args) != 1:
                    raise ValueError("len")
                if args[0] is None:
                    return 0.0
                return float(len(str(args[0])))
            if fname in {"lower", "upper", "trim"}:
                if len(args) != 1:
                    raise ValueError(fname)
                text = "" if args[0] is None else str(args[0])
                if fname == "lower":
                    return text.lower()
                if fname == "upper":
                    return text.upper()
                return text.strip()
            raise ValueError("fn")
        raise ValueError("node")

    try:
        value = _eval(tree)
        if isinstance(value, float) and value != value:  # noqa: PLR0124
            return None
        return value
    except (ValueError, ZeroDivisionError, TypeError, KeyError, OverflowError):
        return None


def _safe_header(value: Any, index: int) -> str:
    raw = str(value or "").strip() or f"coluna_{index + 1}"
    cleaned = re.sub(r"[^\w]+", "_", raw)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned


def apply_data_transform_steps(
    table: dict[str, Any],
    steps: list[dict[str, Any]] | None,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    columns = [str(col) for col in (table.get("columns") or [])]
    rows = [dict(row) for row in (table.get("rows") or []) if isinstance(row, dict)]
    siblings = sibling_tables or {}
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
            rows = [{**row, name: evaluate_safe_column_expr(expr, row)} for row in rows]
        elif op == "replace":
            column = str(step.get("column") or "")
            find = str(step.get("find") if step.get("find") is not None else "")
            replace_with = str(step.get("replaceWith") if step.get("replaceWith") is not None else "")
            rows = [
                {**row, column: str(row.get(column) if row.get(column) is not None else "").replace(find, replace_with)}
                for row in rows
            ]
        elif op == "sort":
            column = str(step.get("column") or "")
            reverse = str(step.get("direction") or "") == "desc"

            def _sort_key(row: dict[str, Any]) -> tuple[int, float | str]:
                value = row.get(column)
                num = _as_number(value)
                if num is not None:
                    return (0, num)
                return (1, str(value if value is not None else ""))

            rows = sorted(rows, key=_sort_key, reverse=reverse)
        elif op == "keepRows":
            count = int(step.get("count") or 0)
            if str(step.get("from") or "") == "bottom":
                rows = rows[-count:] if count else rows
            else:
                rows = rows[:count]
        elif op == "removeRows":
            count = int(step.get("count") or 0)
            if str(step.get("from") or "") == "bottom":
                rows = rows[:-count] if count else rows
            else:
                rows = rows[count:]
        elif op == "changeType":
            column = str(step.get("column") or "")
            to = str(step.get("to") or "string")
            if to == "number":
                rows = [{**row, column: _as_number(row.get(column))} for row in rows]
            else:
                rows = [
                    {
                        **row,
                        column: "" if row.get(column) is None else str(row.get(column)),
                    }
                    for row in rows
                ]
        elif op == "fillDown":
            column = str(step.get("column") or "")
            last: Any = None
            next_rows = []
            for row in rows:
                cell = row.get(column)
                if cell is not None and str(cell).strip() != "":
                    last = cell
                    next_rows.append(row)
                else:
                    next_rows.append({**row, column: last})
            rows = next_rows
        elif op == "firstRowAsHeader":
            if not rows:
                continue
            header_row = rows[0]
            next_columns = [_safe_header(header_row.get(col), i) for i, col in enumerate(columns)]
            next_rows = []
            for row in rows[1:]:
                next_row = {next_columns[i]: row.get(col) for i, col in enumerate(columns)}
                next_rows.append(next_row)
            columns = next_columns
            rows = next_rows
        elif op == "groupBy":
            keys = [str(k) for k in (step.get("keys") or [])]
            aggregations = [a for a in (step.get("aggregations") or []) if isinstance(a, dict)]
            groups: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                key = "\u0001".join(str(row.get(k) if row.get(k) is not None else "") for k in keys)
                groups.setdefault(key, []).append(row)
            next_rows = []
            for group_rows in groups.values():
                next_row: dict[str, Any] = {k: group_rows[0].get(k) for k in keys}
                for agg in aggregations:
                    column = str(agg.get("column") or "")
                    fn = str(agg.get("fn") or "sum")
                    as_name = str(agg.get("as") or f"{column}_{fn}")
                    next_row[as_name] = _aggregate([r.get(column) for r in group_rows], fn)
                next_rows.append(next_row)
            columns = keys + [str(a.get("as") or "") for a in aggregations if a.get("as")]
            rows = next_rows
        elif op == "pivot":
            column = str(step.get("column") or "")
            value_column = str(step.get("valueColumn") or "")
            aggregation = str(step.get("aggregation") or "sum")
            stay = [c for c in columns if c not in {column, value_column}]
            pivot_values = sorted(
                {str(row.get(column) if row.get(column) is not None else "") for row in rows} - {""}
            )
            groups: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                key = "\u0001".join(str(row.get(k) if row.get(k) is not None else "") for k in stay)
                groups.setdefault(key, []).append(row)
            next_columns = stay + [_safe_header(v, 0) for v in pivot_values]
            next_rows = []
            for group_rows in groups.values():
                next_row = {k: group_rows[0].get(k) for k in stay}
                for pivot in pivot_values:
                    matched = [
                        r for r in group_rows if str(r.get(column) if r.get(column) is not None else "") == pivot
                    ]
                    next_row[_safe_header(pivot, 0)] = _aggregate(
                        [r.get(value_column) for r in matched], aggregation
                    )
                next_rows.append(next_row)
            columns = next_columns
            rows = next_rows
        elif op == "unpivot":
            unpivot_cols = [str(c) for c in (step.get("columns") or [])]
            stay = [c for c in columns if c not in unpivot_cols]
            name_col = str(step.get("nameColumn") or "atributo")
            value_col = str(step.get("valueColumn") or "valor")
            next_rows = []
            for row in rows:
                for col in unpivot_cols:
                    next_row = {k: row.get(k) for k in stay}
                    next_row[name_col] = col
                    next_row[value_col] = row.get(col)
                    next_rows.append(next_row)
            columns = stay + [name_col, value_col]
            rows = next_rows
        elif op == "merge":
            source_id = str(step.get("sourceId") or "")
            other = siblings.get(source_id)
            if not isinstance(other, dict):
                continue
            left_key = str(step.get("leftKey") or "")
            right_key = str(step.get("rightKey") or "")
            other_cols = [str(c) for c in (other.get("columns") or [])]
            other_rows = [dict(r) for r in (other.get("rows") or []) if isinstance(r, dict)]
            take_cols = [str(c) for c in (step.get("columns") or []) if str(c).strip()]
            if not take_cols:
                take_cols = [c for c in other_cols if c != right_key]
            right_index = {
                str(r.get(right_key) if r.get(right_key) is not None else ""): r for r in other_rows
            }
            for col in take_cols:
                if col not in columns:
                    columns.append(col)
            next_rows = []
            for row in rows:
                match = right_index.get(str(row.get(left_key) if row.get(left_key) is not None else ""))
                if not match:
                    next_rows.append(row)
                    continue
                merged = dict(row)
                for col in take_cols:
                    merged[col] = match.get(col)
                next_rows.append(merged)
            rows = next_rows

    return {"columns": columns, "rows": rows}


def apply_transform_plan(
    table: dict[str, Any],
    plan: TransformPlan,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Executa a IR tipada pela fachada existente, sem engine paralela."""

    return apply_data_transform_steps(
        table,
        plan_to_legacy_steps(plan),
        sibling_tables=sibling_tables,
    )


def apply_data_transform_to_payload_result(
    data: Any,
    transform: Any,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    read_result = read_data_transform(transform)
    table = coerce_payload_to_table(data)
    if not read_result.executable or read_result.plan is None or table is None:
        return {
            "data": data,
            "applied": False,
            "table": table,
            "transform": read_result.public_metadata(),
        }
    next_table = apply_transform_plan(
        table,
        read_result.plan,
        sibling_tables=sibling_tables,
    )
    return {
        "data": next_table["rows"],
        "applied": True,
        "table": next_table,
        "transform": read_result.public_metadata(),
    }


def apply_data_transform_to_payload(
    data: Any,
    transform: Any,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
) -> tuple[Any, bool, dict[str, Any] | None]:
    result = apply_data_transform_to_payload_result(
        data,
        transform,
        sibling_tables=sibling_tables,
    )
    return result["data"], result["applied"], result["table"]
