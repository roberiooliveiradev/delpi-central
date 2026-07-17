"""Transformações tipo Power Query sobre payload tabular (antes da View)."""

from __future__ import annotations

import ast
import hashlib
import operator
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from tv_app.application.services.data.data_transform_contract import read_data_transform
from tv_app.application.services.data.m_query.m_legacy_adapter import (
    normalize_legacy_transform,
    plan_to_legacy_steps,
)
from tv_app.application.services.data.m_query.m_expression_interpreter import (
    MExpressionError,
    convert_m_value,
    evaluate_compiled_expression,
)
from tv_app.application.services.tv_dashboard_content_service import m_query_setting
from tv_app.application.services.series_points_extractor import unwrap_operational_data
from tv_app.domain.data_query.m_execution import MExecutionError, MRuntimeError
from tv_app.domain.data_query.transform_plan import CompiledExpression, CompiledMPlanStep, TransformPlan

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


@dataclass(frozen=True, slots=True)
class TransformExecutionResult:
    table: dict[str, Any]
    schema: tuple[dict[str, Any], ...]
    runtime_errors: tuple[MRuntimeError, ...]
    execution_ms: int
    selected_step_name: str

    def runtime_errors_dict(self) -> dict[str, Any]:
        limit = int(m_query_setting("diagnosticSampleLimit", 20))
        return {
            "count": len(self.runtime_errors),
            "sample": [item.to_dict() for item in self.runtime_errors[:limit]],
        }


def _copy_table(table: dict[str, Any]) -> dict[str, Any]:
    return {
        "columns": [str(item) for item in (table.get("columns") or [])],
        "rows": [dict(row) for row in (table.get("rows") or []) if isinstance(row, dict)],
    }


def _table_schema(
    table: dict[str, Any],
    declared_types: dict[str, str],
) -> tuple[dict[str, Any], ...]:
    rows = table["rows"]
    result: list[dict[str, Any]] = []
    for column in table["columns"]:
        values = [row.get(column) for row in rows]
        nullable = any(value is None for value in values) or not values
        declared = declared_types.get(column)
        inferred = "any"
        if declared:
            inferred = declared
            source = "declared"
        else:
            present = [value for value in values if value is not None]
            kinds: set[str] = set()
            for value in present:
                if isinstance(value, bool):
                    kinds.add("logical")
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    kinds.add("number")
                elif isinstance(value, datetime):
                    kinds.add("datetime")
                elif isinstance(value, date):
                    kinds.add("date")
                elif isinstance(value, timedelta):
                    kinds.add("duration")
                elif isinstance(value, str):
                    kinds.add("text")
                else:
                    kinds.add("any")
            inferred = next(iter(kinds)) if len(kinds) == 1 else "any"
            source = "inferred" if present else "unknown"
        result.append(
            {
                "key": column,
                "label": column,
                "type": inferred,
                "nullable": nullable,
                "typeSource": source,
            }
        )
    return tuple(result)


class _ExecutionLimits:
    def __init__(self) -> None:
        self.deadline = time.monotonic() + int(m_query_setting("executionTimeoutMs", 2000)) / 1000
        self.max_rows = int(m_query_setting("maxExecutionRows", 10000))
        self.max_columns = int(m_query_setting("maxExecutionColumns", 500))
        self.max_cells = int(m_query_setting("maxExecutionCells", 1000000))
        self.max_join_input = int(m_query_setting("maxJoinInputRows", 5000))
        self.max_join_output = int(m_query_setting("maxJoinOutputRows", 10000))
        self.max_pivot_columns = int(m_query_setting("maxPivotColumns", 200))
        self.max_depth = int(m_query_setting("maxExpressionDepth", 40))

    def check(self) -> None:
        if time.monotonic() > self.deadline:
            raise MExecutionError("m.execution_timeout", "O tempo limite da transformação foi excedido.")

    def guard_table(self, table: dict[str, Any]) -> None:
        self.check()
        rows = len(table["rows"])
        columns = len(table["columns"])
        if rows > self.max_rows:
            raise MExecutionError("m.limit_rows", "A transformação excedeu o limite de linhas.")
        if columns > self.max_columns:
            raise MExecutionError("m.limit_columns", "A transformação excedeu o limite de colunas.")
        if rows * columns > self.max_cells:
            raise MExecutionError("m.limit_cells", "A transformação excedeu o limite de células.")


def _argument(
    expression: CompiledExpression,
    *,
    row: dict[str, Any] | None,
    environment: dict[str, Any],
    culture: str,
    limits: _ExecutionLimits,
) -> Any:
    return evaluate_compiled_expression(
        expression,
        row=row,
        environment=environment,
        culture=culture,
        check_deadline=limits.check,
        max_depth=limits.max_depth,
    )


def _column_list(value: Any, operation: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise MExecutionError("m.literal_column_list_required", f"{operation} exige uma lista de colunas.")
    return list(value)


def _require_column(table: dict[str, Any], column: str, operation: str) -> None:
    if column not in table["columns"]:
        raise MExecutionError("m.unknown_column", f'A coluna "{column}" não existe em {operation}.')


def _aggregate_m(values: list[Any], function_name: str, culture: str) -> Any:
    expression = CompiledExpression(
        "call",
        function_name,
        (CompiledExpression("literal", value=values),),
    )
    return evaluate_compiled_expression(expression, culture=culture)


def _execute_m_step(
    step: CompiledMPlanStep,
    source: dict[str, Any],
    *,
    environment: dict[str, Any],
    culture: str,
    limits: _ExecutionLimits,
    runtime_errors: list[MRuntimeError],
    declared_types: dict[str, str],
) -> dict[str, Any]:
    table = _copy_table(source)
    name = step.function_name
    args = step.arguments
    if name == "#identity":
        return table

    def value(index: int, row: dict[str, Any] | None = None) -> Any:
        if index >= len(args):
            return None
        return _argument(
            args[index],
            row=row,
            environment=environment,
            culture=culture,
            limits=limits,
        )

    if name == "Table.RenameColumns":
        pairs = value(0)
        if not isinstance(pairs, list):
            raise MExecutionError("m.invalid_rename_spec", "Renames deve ser uma lista.")
        for pair in pairs:
            if not isinstance(pair, list) or len(pair) != 2:
                raise MExecutionError("m.invalid_rename_spec", "Rename inválido.")
            old, new = str(pair[0]), str(pair[1])
            _require_column(table, old, name)
            table["columns"] = [new if column == old else column for column in table["columns"]]
            table["rows"] = [
                {new if key == old else key: cell for key, cell in row.items()} for row in table["rows"]
            ]
            if old in declared_types:
                declared_types[new] = declared_types.pop(old)
    elif name in {"Table.SelectColumns", "Table.RemoveColumns"}:
        selected = _column_list(value(0), name)
        for column in selected:
            _require_column(table, column, name)
        columns = (
            selected
            if name == "Table.SelectColumns"
            else [column for column in table["columns"] if column not in selected]
        )
        table = {"columns": columns, "rows": [{column: row.get(column) for column in columns} for row in table["rows"]]}
    elif name == "Table.SelectRows":
        predicate = args[0]
        rows = []
        for index, row in enumerate(table["rows"]):
            limits.check()
            try:
                predicate_value = _argument(
                    predicate,
                    row=row,
                    environment=environment,
                    culture=culture,
                    limits=limits,
                )
                if not isinstance(predicate_value, bool):
                    raise MExpressionError(
                        "m.logical_expected",
                        "O predicado de Table.SelectRows deve produzir logical.",
                    )
                if predicate_value:
                    rows.append(row)
            except MExpressionError as exc:
                runtime_errors.append(MRuntimeError(step.name, exc.code, str(exc), index))
        table["rows"] = rows
    elif name == "Table.Sort":
        criteria = value(0)
        if not isinstance(criteria, list):
            raise MExecutionError("m.invalid_sort_spec", "Critérios de ordenação inválidos.")
        for criterion in reversed(criteria):
            column, direction = criterion
            _require_column(table, str(column), name)
            table["rows"].sort(
                key=lambda row: (row.get(str(column)) is None, row.get(str(column))),
                reverse=direction == "Order.Descending",
            )
    elif name == "Table.ReplaceValue":
        old, new, replacer = value(0), value(1), value(2)
        columns = _column_list(value(3), name)
        for column in columns:
            _require_column(table, column, name)
        for row in table["rows"]:
            for column in columns:
                current = row.get(column)
                row[column] = (
                    str(current).replace(str(old), str(new))
                    if replacer == "Replacer.ReplaceText" and current is not None
                    else (new if current == old else current)
                )
    elif name in {"Table.FirstN", "Table.LastN", "Table.Skip", "Table.RemoveLastN"}:
        count = int(value(0))
        if name == "Table.FirstN":
            table["rows"] = table["rows"][:count]
        elif name == "Table.LastN":
            table["rows"] = table["rows"][-count:] if count else []
        elif name == "Table.Skip":
            table["rows"] = table["rows"][count:]
        else:
            table["rows"] = table["rows"][:-count] if count else list(table["rows"])
    elif name == "Table.TransformColumnTypes":
        transformations = value(0)
        step_culture = str(value(1) or culture) if len(args) > 1 else culture
        for column, target_type in transformations:
            column = str(column)
            target_type = str(target_type)
            _require_column(table, column, name)
            declared_types[column] = target_type
            for index, row in enumerate(table["rows"]):
                limits.check()
                try:
                    row[column] = convert_m_value(row.get(column), target_type, step_culture)
                except MExpressionError as exc:
                    error = MRuntimeError(step.name, exc.code, str(exc), index, column)
                    runtime_errors.append(error)
                    row[column] = {"error": error.to_dict()}
    elif name == "Table.FillDown":
        columns = _column_list(value(0), name)
        for column in columns:
            _require_column(table, column, name)
            previous = None
            for row in table["rows"]:
                limits.check()
                if row.get(column) is None:
                    row[column] = previous
                else:
                    previous = row[column]
    elif name == "Table.PromoteHeaders":
        if table["rows"]:
            first = table["rows"][0]
            columns = [str(first.get(column) if first.get(column) is not None else column) for column in table["columns"]]
            table = {
                "columns": columns,
                "rows": [
                    {columns[index]: row.get(old) for index, old in enumerate(source["columns"])}
                    for row in table["rows"][1:]
                ],
            }
            declared_types.clear()
    elif name == "Table.AddColumn":
        column = str(value(0))
        generator = args[1]
        target_type = str(value(2)) if len(args) > 2 else "any"
        if column not in table["columns"]:
            table["columns"].append(column)
        if target_type != "any":
            declared_types[column] = target_type
        for index, row in enumerate(table["rows"]):
            limits.check()
            try:
                generated = _argument(
                    generator,
                    row=row,
                    environment=environment,
                    culture=culture,
                    limits=limits,
                )
                row[column] = convert_m_value(generated, target_type, culture)
            except MExpressionError as exc:
                error = MRuntimeError(step.name, exc.code, str(exc), index, column)
                runtime_errors.append(error)
                row[column] = {"error": error.to_dict()}
    elif name == "Table.Group":
        keys = _column_list(value(0), name)
        aggregation_nodes = args[1].children
        for key in keys:
            _require_column(table, key, name)
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in table["rows"]:
            limits.check()
            groups[tuple(row.get(key) for key in keys)].append(row)
        output_rows = []
        output_columns = list(keys)
        for key_values, grouped_rows in groups.items():
            out = dict(zip(keys, key_values))
            for aggregation_node in aggregation_nodes:
                if aggregation_node.kind != "list" or len(aggregation_node.children) < 2:
                    raise MExecutionError("m.invalid_group_spec", "Agregação de Group inválida.")
                output_name = str(
                    _argument(
                        aggregation_node.children[0],
                        row=None,
                        environment=environment,
                        culture=culture,
                        limits=limits,
                    )
                )
                generator = aggregation_node.children[1]
                group_context = {
                    column: [row.get(column) for row in grouped_rows] for column in table["columns"]
                }
                try:
                    out[output_name] = _argument(
                        generator,
                        row=group_context,
                        environment=environment,
                        culture=culture,
                        limits=limits,
                    )
                except MExpressionError as exc:
                    error = MRuntimeError(step.name, exc.code, str(exc), len(output_rows), output_name)
                    runtime_errors.append(error)
                    out[output_name] = {"error": error.to_dict()}
                if len(aggregation_node.children) > 2:
                    declared_types[output_name] = str(
                        _argument(
                            aggregation_node.children[2],
                            row=None,
                            environment=environment,
                            culture=culture,
                            limits=limits,
                        )
                    )
                if output_name not in output_columns:
                    output_columns.append(output_name)
            output_rows.append(out)
        table = {"columns": output_columns, "rows": output_rows}
    elif name == "Table.Pivot":
        pivot_values = value(0)
        attribute_column = str(value(1))
        value_column = str(value(2))
        aggregate = str(value(3) or "List.First") if len(args) > 3 else "List.First"
        for column in (attribute_column, value_column):
            _require_column(table, column, name)
        if not isinstance(pivot_values, list):
            raise MExecutionError("m.invalid_pivot_spec", "Valores de pivot devem ser uma lista.")
        if len(pivot_values) > limits.max_pivot_columns:
            raise MExecutionError("m.limit_pivot_columns", "O pivot excedeu o limite de colunas.")
        stay = [column for column in table["columns"] if column not in {attribute_column, value_column}]
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in table["rows"]:
            grouped[tuple(row.get(column) for column in stay)].append(row)
        output_rows = []
        for keys, grouped_rows in grouped.items():
            out = dict(zip(stay, keys))
            for pivot in pivot_values:
                matches = [row.get(value_column) for row in grouped_rows if row.get(attribute_column) == pivot]
                out[str(pivot)] = _aggregate_m(matches, aggregate, culture)
            output_rows.append(out)
        table = {"columns": stay + [str(item) for item in pivot_values], "rows": output_rows}
    elif name in {"Table.Unpivot", "Table.UnpivotOtherColumns"}:
        selected = _column_list(value(0), name)
        attribute_column, value_column = str(value(1)), str(value(2))
        unpivot = (
            selected
            if name == "Table.Unpivot"
            else [column for column in table["columns"] if column not in selected]
        )
        stay = [column for column in table["columns"] if column not in unpivot]
        output_rows = []
        for row in table["rows"]:
            for column in unpivot:
                limits.check()
                output_rows.append(
                    {
                        **{key: row.get(key) for key in stay},
                        attribute_column: column,
                        value_column: row.get(column),
                    }
                )
        table = {"columns": stay + [attribute_column, value_column], "rows": output_rows}
    elif name == "Table.NestedJoin":
        left_keys = _column_list(value(0), name)
        right = value(1)
        right_keys = _column_list(value(2), name)
        nested_column = str(value(3))
        join_kind = value(4) if len(args) > 4 else "JoinKind.LeftOuter"
        if join_kind != "JoinKind.LeftOuter" or not isinstance(right, dict):
            raise MExecutionError("m.join_kind_not_allowed", "Somente JoinKind.LeftOuter é permitido.")
        if len(table["rows"]) > limits.max_join_input or len(right.get("rows") or []) > limits.max_join_input:
            raise MExecutionError("m.limit_join_input_rows", "O join excedeu o limite de entrada.")
        index: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for right_row in right["rows"]:
            limits.check()
            index[tuple(right_row.get(key) for key in right_keys)].append(dict(right_row))
        for row in table["rows"]:
            row[nested_column] = index.get(tuple(row.get(key) for key in left_keys), [])
        table["columns"].append(nested_column)
    elif name == "Table.ExpandTableColumn":
        nested_column = str(value(0))
        nested_columns = _column_list(value(1), name)
        aliases = _column_list(value(2), name) if len(args) > 2 else nested_columns
        if len(aliases) != len(nested_columns):
            raise MExecutionError("m.invalid_expand_spec", "A lista de aliases deve ter o mesmo tamanho.")
        output_rows = []
        for row in table["rows"]:
            matches = row.get(nested_column)
            matches = matches if isinstance(matches, list) else []
            for match in matches or [None]:
                limits.check()
                out = {key: cell for key, cell in row.items() if key != nested_column}
                for source_column, alias in zip(nested_columns, aliases):
                    out[alias] = match.get(source_column) if isinstance(match, dict) else None
                output_rows.append(out)
                if len(output_rows) > limits.max_join_output:
                    raise MExecutionError("m.limit_join_output_rows", "A expansão do join excedeu o limite.")
        table = {
            "columns": [column for column in table["columns"] if column != nested_column] + aliases,
            "rows": output_rows,
        }
    else:
        raise MExecutionError("m.function_not_allowed", f"A função {name} não pode ser executada.")
    limits.guard_table(table)
    return table


def execute_transform_plan(
    table: dict[str, Any],
    plan: TransformPlan,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
    culture: str = "pt-BR",
) -> TransformExecutionResult:
    """Único ponto de execução de TransformPlan na fachada canônica."""

    started = time.monotonic()
    if not plan.steps or not all(isinstance(step, CompiledMPlanStep) for step in plan.steps):
        legacy_table = apply_data_transform_steps(
            table,
            plan_to_legacy_steps(plan),
            sibling_tables=sibling_tables,
        )
        return TransformExecutionResult(
            legacy_table,
            _table_schema(legacy_table, {}),
            (),
            int((time.monotonic() - started) * 1000),
            plan.output,
        )
    limits = _ExecutionLimits()
    source = _copy_table(table)
    limits.guard_table(source)
    environment: dict[str, Any] = {"Fonte": source, **(sibling_tables or {})}
    runtime_errors: list[MRuntimeError] = []
    declared_types: dict[str, str] = {}
    for step in plan.steps:
        limits.check()
        input_table = environment.get(step.input_name)
        if not isinstance(input_table, dict):
            raise MExecutionError(
                "m.table_input_unavailable",
                f'A entrada "{step.input_name}" não está disponível.',
                step_name=step.name,
            )
        try:
            environment[step.name] = _execute_m_step(
                step,
                input_table,
                environment=environment,
                culture=culture,
                limits=limits,
                runtime_errors=runtime_errors,
                declared_types=declared_types,
            )
        except MExecutionError as exc:
            if not exc.step_name:
                exc.step_name = step.name
            raise
        except MExpressionError as exc:
            raise MExecutionError(exc.code, str(exc), step_name=step.name) from exc
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise MExecutionError(
                "m.execution_error",
                f'A etapa "{step.name}" não pôde ser executada.',
                step_name=step.name,
            ) from exc
    output = environment.get(plan.output)
    if not isinstance(output, dict):
        raise MExecutionError("m.output_table_required", "A saída do plano não é uma tabela.")
    return TransformExecutionResult(
        output,
        _table_schema(output, declared_types),
        tuple(runtime_errors),
        int((time.monotonic() - started) * 1000),
        plan.output,
    )


def apply_transform_plan(
    table: dict[str, Any],
    plan: TransformPlan,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
    culture: str = "pt-BR",
) -> dict[str, Any]:
    return execute_transform_plan(
        table,
        plan,
        sibling_tables=sibling_tables,
        culture=culture,
    ).table


def apply_data_transform_to_payload_result(
    data: Any,
    transform: Any,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
    query_bindings: tuple[dict[str, Any], ...] = (),
    target_step_name: str | None = None,
    culture: str | None = None,
) -> dict[str, Any]:
    selected_culture = culture or str(m_query_setting("defaultCulture", "pt-BR"))
    read_result = read_data_transform(
        transform,
        query_bindings=query_bindings,
        target_step_name=target_step_name,
        culture=selected_culture,
    )
    table = coerce_payload_to_table(data)
    script_hash = (
        "sha256:"
        + hashlib.sha256((read_result.canonical_script or "").encode("utf-8")).hexdigest()
        if read_result.version == 2 and read_result.canonical_script
        else None
    )
    if not read_result.executable or read_result.plan is None or table is None:
        return {
            "data": data,
            "applied": False,
            "table": table,
            "transform": read_result.public_metadata(),
            "scriptHash": script_hash,
        }
    started = time.monotonic()
    try:
        execution = execute_transform_plan(
            table,
            read_result.plan,
            sibling_tables=sibling_tables,
            culture=selected_culture,
        )
    except MExecutionError as exc:
        runtime_error = MRuntimeError(exc.step_name, exc.code, str(exc))
        return {
            "data": data,
            "applied": False,
            "failed": True,
            "table": table,
            "transform": read_result.public_metadata(),
            "scriptHash": script_hash,
            "schema": list(_table_schema(table, {})),
            "runtimeErrors": {"count": 1, "sample": [runtime_error.to_dict()]},
            "executionMs": int((time.monotonic() - started) * 1000),
            "selectedStepName": read_result.plan.output,
        }
    return {
        "data": execution.table["rows"],
        "applied": True,
        "table": execution.table,
        "transform": read_result.public_metadata(),
        "scriptHash": script_hash,
        "schema": list(execution.schema),
        "runtimeErrors": execution.runtime_errors_dict(),
        "executionMs": execution.execution_ms,
        "selectedStepName": execution.selected_step_name,
    }


def apply_data_transform_to_payload(
    data: Any,
    transform: Any,
    *,
    sibling_tables: dict[str, dict[str, Any]] | None = None,
    query_bindings: tuple[dict[str, Any], ...] = (),
    target_step_name: str | None = None,
    culture: str | None = None,
) -> tuple[Any, bool, dict[str, Any] | None]:
    result = apply_data_transform_to_payload_result(
        data,
        transform,
        sibling_tables=sibling_tables,
        query_bindings=query_bindings,
        target_step_name=target_step_name,
        culture=culture,
    )
    return result["data"], result["applied"], result["table"]
