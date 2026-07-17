"""Interpretador de CompiledExpression; não recebe texto M nem código Python."""

from __future__ import annotations

import calendar
import math
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

from tv_app.domain.data_query.transform_plan import CompiledExpression


class MExpressionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_SCALAR_FUNCTIONS = frozenset(
    {
        "Text.Trim",
        "Text.Clean",
        "Text.Upper",
        "Text.Lower",
        "Text.Proper",
        "Text.Length",
        "Text.Contains",
        "Text.StartsWith",
        "Text.EndsWith",
        "Text.BeforeDelimiter",
        "Text.AfterDelimiter",
        "Text.BetweenDelimiters",
        "Text.Combine",
        "Text.From",
        "Number.Abs",
        "Number.Round",
        "Number.RoundUp",
        "Number.RoundDown",
        "Number.Mod",
        "Number.From",
        "Date.From",
        "Date.Year",
        "Date.Month",
        "Date.Day",
        "Date.StartOfMonth",
        "Date.EndOfMonth",
        "Date.AddDays",
        "Date.AddMonths",
        "DateTime.From",
        "Duration.Days",
        "List.Sum",
        "List.Average",
        "List.Min",
        "List.Max",
        "List.Count",
        "List.First",
    }
)


def _raise(code: str, message: str) -> None:
    raise MExpressionError(code, message)


def _number(value: Any, culture: str) -> float:
    if isinstance(value, bool) or value is None:
        _raise("m.type_number_expected", "Era esperado um número.")
    if isinstance(value, (int, float, Decimal)):
        result = float(value)
        if math.isfinite(result):
            return result
        _raise("m.number_not_finite", "O número não é finito.")
    if not isinstance(value, str):
        _raise("m.type_number_expected", "Era esperado um número.")
    text = value.strip().replace("\u00a0", "")
    if culture.lower() == "pt-br":
        text = text.replace(".", "").replace(",", ".")
    try:
        result = float(Decimal(text))
    except (InvalidOperation, ValueError):
        _raise("m.number_conversion", "Não foi possível converter o valor em número.")
    if not math.isfinite(result):
        _raise("m.number_not_finite", "O número não é finito.")
    return result


def _date(value: Any, culture: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        _raise("m.date_conversion", "Não foi possível converter o valor em data.")
    text = value.strip()
    formats = ("%d/%m/%Y", "%Y-%m-%d") if culture.lower() == "pt-br" else ("%Y-%m-%d",)
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    _raise("m.date_conversion", "Não foi possível converter o valor em data.")


def _datetime(value: Any, culture: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if not isinstance(value, str):
        _raise("m.datetime_conversion", "Não foi possível converter o valor em data e hora.")
    text = value.strip()
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    _raise("m.datetime_conversion", "Não foi possível converter o valor em data e hora.")


def convert_m_value(value: Any, target_type: str, culture: str) -> Any:
    if value is None or target_type == "any":
        return value
    if target_type == "text":
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return str(value)
    if target_type == "number":
        return _number(value, culture)
    if target_type == "logical":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
        _raise("m.logical_conversion", "Não foi possível converter o valor em logical.")
    if target_type == "date":
        return _date(value, culture)
    if target_type == "datetime":
        return _datetime(value, culture)
    if target_type == "duration":
        if isinstance(value, timedelta):
            return value
        return timedelta(days=_number(value, culture))
    _raise("m.type_not_supported", f"O tipo {target_type} não é suportado.")


def _truth(value: Any) -> bool:
    if not isinstance(value, bool):
        _raise("m.logical_expected", "A condição deve produzir logical.")
    return value


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _add_months(value: date, months: int) -> date:
    offset = value.month - 1 + months
    year = value.year + offset // 12
    month = offset % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _call_scalar(name: str, args: list[Any], culture: str) -> Any:
    if name not in _SCALAR_FUNCTIONS:
        _raise("m.function_not_allowed", f"A função {name} não é permitida.")
    if name.startswith("Text."):
        if name == "Text.Combine":
            values = args[0]
            if not isinstance(values, list):
                _raise("m.list_expected", "Text.Combine exige uma lista.")
            return (str(args[1]) if len(args) > 1 else "").join(_clean_text(item) for item in values)
        text = _clean_text(args[0])
        if name == "Text.Trim":
            return text.strip()
        if name == "Text.Clean":
            return "".join(char for char in text if char.isprintable())
        if name == "Text.Upper":
            return text.upper()
        if name == "Text.Lower":
            return text.lower()
        if name == "Text.Proper":
            return text.title()
        if name == "Text.Length":
            return float(len(text))
        needle = _clean_text(args[1]) if len(args) > 1 else ""
        if name == "Text.Contains":
            return needle in text
        if name == "Text.StartsWith":
            return text.startswith(needle)
        if name == "Text.EndsWith":
            return text.endswith(needle)
        if name == "Text.BeforeDelimiter":
            return text.split(needle, 1)[0]
        if name == "Text.AfterDelimiter":
            return text.split(needle, 1)[1] if needle in text else ""
        if name == "Text.BetweenDelimiters":
            after = text.split(needle, 1)[1] if needle in text else ""
            end = _clean_text(args[2])
            return after.split(end, 1)[0]
        if name == "Text.From":
            return convert_m_value(args[0], "text", str(args[1]) if len(args) > 1 else culture)
    if name.startswith("Number."):
        if name == "Number.From":
            return _number(args[0], str(args[1]) if len(args) > 1 else culture)
        number = _number(args[0], culture)
        if name == "Number.Abs":
            return abs(number)
        digits = int(_number(args[1], culture)) if len(args) > 1 else 0
        factor = 10**digits
        if name == "Number.Round":
            return round(number, digits)
        if name == "Number.RoundUp":
            return math.ceil(number * factor) / factor
        if name == "Number.RoundDown":
            return math.floor(number * factor) / factor
        if name == "Number.Mod":
            divisor = _number(args[1], culture)
            if divisor == 0:
                _raise("m.division_by_zero", "Divisão por zero.")
            return number % divisor
    if name.startswith("Date."):
        if name == "Date.From":
            return _date(args[0], str(args[1]) if len(args) > 1 else culture)
        current = _date(args[0], culture)
        if name == "Date.Year":
            return float(current.year)
        if name == "Date.Month":
            return float(current.month)
        if name == "Date.Day":
            return float(current.day)
        if name == "Date.StartOfMonth":
            return current.replace(day=1)
        if name == "Date.EndOfMonth":
            return current.replace(day=calendar.monthrange(current.year, current.month)[1])
        if name == "Date.AddDays":
            return current + timedelta(days=int(_number(args[1], culture)))
        if name == "Date.AddMonths":
            return _add_months(current, int(_number(args[1], culture)))
    if name == "DateTime.From":
        return _datetime(args[0], str(args[1]) if len(args) > 1 else culture)
    if name == "Duration.Days":
        if not isinstance(args[0], timedelta):
            _raise("m.duration_expected", "Era esperada uma duração.")
        return args[0].total_seconds() / 86400
    if name.startswith("List."):
        values = args[0]
        if not isinstance(values, list):
            _raise("m.list_expected", f"{name} exige uma lista.")
        present = [item for item in values if item is not None]
        if name == "List.Count":
            return float(len(values))
        if name == "List.First":
            return values[0] if values else (args[1] if len(args) > 1 else None)
        if not present:
            return None
        if name in {"List.Sum", "List.Average"}:
            numbers = [_number(item, culture) for item in present]
            total = sum(numbers)
            return total if name == "List.Sum" else total / len(numbers)
        if name == "List.Min":
            return min(present)
        if name == "List.Max":
            return max(present)
    _raise("m.function_not_allowed", f"A função {name} não é permitida.")


def evaluate_compiled_expression(
    expression: CompiledExpression,
    *,
    row: Mapping[str, Any] | None = None,
    environment: Mapping[str, Any] | None = None,
    culture: str = "pt-BR",
    check_deadline: Callable[[], None] | None = None,
    max_depth: int = 40,
) -> Any:
    """Avalia somente a árvore fechada produzida pelo compilador."""

    env = environment or {}
    current_row = row or {}

    def visit(node: CompiledExpression, depth: int) -> Any:
        if check_deadline is not None:
            check_deadline()
        if depth > max_depth:
            _raise("m.limit_expression_depth", "A expressão excedeu a profundidade permitida.")
        if node.kind == "literal":
            return node.value
        if node.kind == "field":
            if str(node.value) not in current_row:
                _raise("m.unknown_column", f'A coluna "{node.value}" não foi encontrada.')
            return current_row[str(node.value)]
        if node.kind == "identifier":
            name = str(node.value)
            if name in env:
                return env[name]
            if name in _SCALAR_FUNCTIONS or name in {
                "Order.Ascending",
                "Order.Descending",
                "Replacer.ReplaceText",
                "Replacer.ReplaceValue",
                "JoinKind.LeftOuter",
            }:
                return name
            _raise("m.unknown_identifier", f'O identificador "{name}" não foi encontrado.')
        if node.kind == "type":
            return str(node.value)
        if node.kind == "list":
            return [visit(child, depth + 1) for child in node.children]
        if node.kind == "record":
            return {
                str(child.value): visit(child.children[0], depth + 1)
                for child in node.children
                if child.kind == "recordField" and child.children
            }
        if node.kind == "each":
            return visit(node.children[0], depth + 1)
        if node.kind == "if":
            condition = _truth(visit(node.children[0], depth + 1))
            return visit(node.children[1] if condition else node.children[2], depth + 1)
        if node.kind == "unary":
            value = visit(node.children[0], depth + 1)
            if node.value == "not":
                return not _truth(value)
            number = _number(value, culture)
            return number if node.value == "+" else -number
        if node.kind == "binary":
            operator = str(node.value)
            left = visit(node.children[0], depth + 1)
            if operator == "and":
                return _truth(visit(node.children[1], depth + 1)) if _truth(left) else False
            if operator == "or":
                return True if _truth(left) else _truth(visit(node.children[1], depth + 1))
            right = visit(node.children[1], depth + 1)
            if operator in {"=", "<>"}:
                equal = left == right
                return equal if operator == "=" else not equal
            if operator in {">", ">=", "<", "<="}:
                if left is None or right is None:
                    _raise("m.null_comparison", "Não é possível ordenar um valor null.")
                if operator == ">":
                    return left > right
                if operator == ">=":
                    return left >= right
                if operator == "<":
                    return left < right
                return left <= right
            if operator == "&":
                return _clean_text(left) + _clean_text(right)
            if operator in {"+", "-", "*", "/"}:
                lhs = _number(left, culture)
                rhs = _number(right, culture)
                if operator == "/" and rhs == 0:
                    _raise("m.division_by_zero", "Divisão por zero.")
                if operator == "+":
                    return lhs + rhs
                if operator == "-":
                    return lhs - rhs
                if operator == "*":
                    return lhs * rhs
                return lhs / rhs
            _raise("m.operator_not_allowed", f"O operador {operator} não é permitido.")
        if node.kind == "call":
            args = [visit(child, depth + 1) for child in node.children]
            return _call_scalar(str(node.value), args, culture)
        _raise("m.expression_not_supported", f"A expressão {node.kind} não é suportada.")

    return visit(expression, 1)
