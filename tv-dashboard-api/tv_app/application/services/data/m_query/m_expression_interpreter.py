"""Interpretador de CompiledExpression; não recebe texto M nem código Python."""

from __future__ import annotations

import calendar
import math
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

from tv_app.domain.data_query.transform_plan import CompiledExpression


class MExpressionError(ValueError):
    """Erro tipado de expressão — diagnóstico estruturado para VISTA/UI.

    ``details`` pode conter function/argument/expected/received e
    ``expressionPath`` aponta o nó falho (metadado de máquina, sem internals).
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
        expression_path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details: dict[str, Any] = dict(details) if details else {}
        self.expression_path = expression_path

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": str(self)}
        out.update(self.details)
        if self.expression_path:
            out["expressionPath"] = self.expression_path
        return out


# Enum bounded de dia da semana (contrato de authoring — nunca inteiros mágicos).
WEEKDAY_CONSTANTS: Mapping[str, int] = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

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
        "Text.Replace",
        "Text.Substring",
        "Text.Split",
        "Text.PadStart",
        "Text.PadEnd",
        "Text.IsNullOrEmpty",
        "Text.EqualsIgnoreCase",
        "Number.Abs",
        "Number.Round",
        "Number.RoundUp",
        "Number.RoundDown",
        "Number.Mod",
        "Number.From",
        "Number.Min",
        "Number.Max",
        "Number.Clamp",
        "Number.SafeDivide",
        "Date.From",
        "Date.Year",
        "Date.Month",
        "Date.Day",
        "Date.StartOfMonth",
        "Date.EndOfMonth",
        "Date.StartOfYear",
        "Date.EndOfYear",
        "Date.StartOfQuarter",
        "Date.EndOfQuarter",
        "Date.AddDays",
        "Date.AddMonths",
        "Date.StartOfWeek",
        "Date.EndOfWeek",
        "Date.DayOfWeek",
        "Date.AddWeeks",
        "Date.WeekOfYear",
        "Date.AddYears",
        "Date.DaysInMonth",
        "Date.StartOfDay",
        "Date.EndOfDay",
        "Date.Min",
        "Date.Max",
        "Date.Between",
        "DateTime.From",
        "Duration.Days",
        "List.Sum",
        "List.Average",
        "List.Min",
        "List.Max",
        "List.Count",
        "List.First",
        "List.Contains",
        "List.Distinct",
        "List.Last",
        "List.Nth",
        "List.AnyTrue",
        "List.AllTrue",
        "Value.IsNull",
        "Value.Coalesce",
        "Value.NullIf",
        "Logic.Switch",
        "Logic.Ifs",
        "Splitter.SplitTextByDelimiter",
    }
)

# Funções com avaliação preguiçosa — os filhos não são avaliados de forma eager.
_LAZY_FUNCTIONS = frozenset({"Value.Coalesce", "Logic.Switch", "Logic.Ifs"})

# Teto de saída para funções de texto que expandem (PadStart/PadEnd).
_MAX_TEXT_OUTPUT = 4096


def _raise(code: str, message: str, **kwargs: Any) -> None:
    raise MExpressionError(code, message, **kwargs)


def _type_of(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "logical"
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, date):
        return "date"
    if isinstance(value, (int, float, Decimal)):
        return "number"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list):
        return "list"
    if isinstance(value, timedelta):
        return "duration"
    return "any"


def _weekday_arg(value: Any, name: str) -> int:
    """Weekday bounded enum (identifier Monday..Sunday → 0..6) ou 0..6 válido."""
    if isinstance(value, bool):
        pass
    elif isinstance(value, (int, float)) and float(value).is_integer():
        index = int(value)
        if 0 <= index <= 6:
            return index
    _raise(
        "m.weekday_invalid",
        f"{name} exige um dia da semana (Monday..Sunday).",
        details={"function": name, "expected": "weekday", "received": _type_of(value)},
    )


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(
        value, (str, int, float, bool, date, datetime, timedelta)
    )


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
        if name == "Text.Replace":
            return text.replace(_clean_text(args[1]), _clean_text(args[2]))
        if name == "Text.Substring":
            start = int(_number(args[1], culture))
            if start < 0:
                _raise(
                    "m.argument_out_of_range",
                    "Text.Substring exige start >= 0.",
                    details={"function": name, "argument": 1, "expected": ">=0"},
                )
            if len(args) > 2:
                length = int(_number(args[2], culture))
                return text[start : start + max(length, 0)]
            return text[start:]
        if name == "Text.Split":
            delimiter = _clean_text(args[1])
            if not delimiter:
                _raise(
                    "m.empty_delimiter",
                    "Text.Split exige delimitador não vazio.",
                    details={"function": name},
                )
            return text.split(delimiter)
        if name in {"Text.PadStart", "Text.PadEnd"}:
            length = int(_number(args[1], culture))
            if length < 0 or length > _MAX_TEXT_OUTPUT:
                _raise(
                    "m.argument_out_of_range",
                    f"{name} exige comprimento entre 0 e {_MAX_TEXT_OUTPUT}.",
                    details={"function": name, "argument": 1},
                )
            fill = _clean_text(args[2]) if len(args) > 2 else " "
            if not fill:
                _raise(
                    "m.empty_delimiter",
                    f"{name} exige caractere de preenchimento não vazio.",
                    details={"function": name, "argument": 2},
                )
            return text.rjust(length, fill[0]) if name == "Text.PadStart" else text.ljust(length, fill[0])
        if name == "Text.IsNullOrEmpty":
            return args[0] is None or (isinstance(args[0], str) and args[0] == "")
        if name == "Text.EqualsIgnoreCase":
            return _clean_text(args[0]).casefold() == _clean_text(args[1]).casefold()
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
        if name in {"Number.Min", "Number.Max"}:
            numbers = [_number(item, culture) for item in args]
            return min(numbers) if name == "Number.Min" else max(numbers)
        if name == "Number.Clamp":
            low = _number(args[1], culture)
            high = _number(args[2], culture)
            if low > high:
                _raise(
                    "m.argument_out_of_range",
                    "Number.Clamp exige min <= max.",
                    details={"function": name, "argument": 1},
                )
            return min(max(number, low), high)
        if name == "Number.SafeDivide":
            denominator = _number(args[1], culture)
            fallback = _number(args[2], culture)
            if denominator == 0:
                return fallback
            try:
                result = number / denominator
            except Exception:
                return fallback
            return result if math.isfinite(result) else fallback
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
        if name == "Date.StartOfYear":
            return current.replace(month=1, day=1)
        if name == "Date.EndOfYear":
            return current.replace(month=12, day=31)
        if name == "Date.StartOfQuarter":
            quarter_start = 3 * ((current.month - 1) // 3) + 1
            return current.replace(month=quarter_start, day=1)
        if name == "Date.EndOfQuarter":
            quarter_end = 3 * ((current.month - 1) // 3) + 3
            last_day = calendar.monthrange(current.year, quarter_end)[1]
            return current.replace(month=quarter_end, day=last_day)
        if name == "Date.AddDays":
            return current + timedelta(days=int(_number(args[1], culture)))
        if name == "Date.AddMonths":
            return _add_months(current, int(_number(args[1], culture)))
        if name == "Date.AddWeeks":
            return current + timedelta(days=7 * int(_number(args[1], culture)))
        if name == "Date.AddYears":
            offset = int(_number(args[1], culture))
            target_year = current.year + offset
            last_day = calendar.monthrange(target_year, current.month)[1]
            return current.replace(
                year=target_year, day=min(current.day, last_day)
            )
        if name in {"Date.StartOfWeek", "Date.EndOfWeek"}:
            first = _weekday_arg(args[1], name)
            delta = (current.weekday() - first) % 7
            start = current - timedelta(days=delta)
            return start if name == "Date.StartOfWeek" else start + timedelta(days=6)
        if name == "Date.DayOfWeek":
            first = _weekday_arg(args[1], name)
            return float((current.weekday() - first) % 7)
        if name == "Date.WeekOfYear":
            # ISO-8601: semana 1 contém a primeira quinta-feira do ano civil.
            return float(current.isocalendar().week)
        if name == "Date.DaysInMonth":
            return float(calendar.monthrange(current.year, current.month)[1])
        if name == "Date.StartOfDay":
            return datetime.combine(current, datetime.min.time())
        if name == "Date.EndOfDay":
            return datetime.combine(current, datetime.max.time())
        if name in {"Date.Min", "Date.Max"}:
            other = _date(args[1], culture)
            return min(current, other) if name == "Date.Min" else max(current, other)
        if name == "Date.Between":
            start = _date(args[1], culture)
            end = _date(args[2], culture)
            return start <= current <= end
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
        if name == "List.Contains":
            return any(item == args[1] for item in values)
        if name == "List.Distinct":
            seen: list[Any] = []
            out: list[Any] = []
            for item in values:
                if not _is_scalar(item):
                    _raise(
                        "m.list_item_not_scalar",
                        "List.Distinct exige itens escalares.",
                        details={"function": name},
                    )
                if not any(item == prev for prev in seen):
                    seen.append(item)
                    out.append(item)
            return out
        if name == "List.Last":
            return values[-1] if values else (args[1] if len(args) > 1 else None)
        if name == "List.Nth":
            index = int(_number(args[1], culture))
            if 0 <= index < len(values):
                return values[index]
            return args[2] if len(args) > 2 else None
        if name == "List.AnyTrue":
            return any(item is True for item in values)
        if name == "List.AllTrue":
            return all(item is True for item in values)
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
    if name == "Splitter.SplitTextByDelimiter":
        delimiter = _clean_text(args[0])
        if not delimiter:
            _raise("m.empty_delimiter", "O delimitador não pode ser vazio.")
        return {"kind": "delimiter", "value": delimiter}
    if name == "Value.IsNull":
        return args[0] is None
    if name == "Value.NullIf":
        return None if args[0] == args[1] else args[0]
    _raise("m.function_not_allowed", f"A função {name} não é permitida.")


def _call_lazy(
    name: str,
    children: tuple[CompiledExpression, ...],
    visit: Callable[..., Any],
    depth: int,
    base_path: str,
) -> Any:
    """Funções com short-circuit — avalia apenas os nós necessários.

    Ramos mortos nunca são avaliados: um erro numa branch não selecionada
    não derruba a expressão (semântica determinística, fail-lazy correto).
    """

    def lazy(index: int) -> Any:
        return visit(children[index], depth + 1, f"{base_path}.children[{index}]")

    if name == "Value.Coalesce":
        for index in range(len(children)):
            value = lazy(index)
            if value is not None:
                return value
        return None
    if name == "Logic.Switch":
        # switch(value, case1, res1, case2, res2, ..., default?)
        target = lazy(0)
        pair_count = len(children) - 1
        default_index = None
        if pair_count % 2 == 1:
            pair_count -= 1
            default_index = len(children) - 1
        for index in range(1, 1 + pair_count, 2):
            if lazy(index) == target:
                return lazy(index + 1)
        if default_index is not None:
            return lazy(default_index)
        return None
    if name == "Logic.Ifs":
        # ifs(cond1, res1, cond2, res2, ..., default?)
        pair_count = len(children)
        default_index = None
        if pair_count % 2 == 1:
            pair_count -= 1
            default_index = len(children) - 1
        for index in range(0, pair_count, 2):
            if _truth(lazy(index)):
                return lazy(index + 1)
        if default_index is not None:
            return lazy(default_index)
        return None
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

    def visit(node: CompiledExpression, depth: int, path: str = "") -> Any:
        try:
            return _visit(node, depth, path)
        except MExpressionError as exc:
            if exc.expression_path is None:
                exc.expression_path = path
            raise

    def _visit(node: CompiledExpression, depth: int, path: str) -> Any:
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
            if name in WEEKDAY_CONSTANTS:
                return WEEKDAY_CONSTANTS[name]
            if name in _SCALAR_FUNCTIONS or name in {
                "Order.Ascending",
                "Order.Descending",
                "Replacer.ReplaceText",
                "Replacer.ReplaceValue",
                "JoinKind.LeftOuter",
                "QuoteStyle.Csv",
            }:
                return name
            _raise("m.unknown_identifier", f'O identificador "{name}" não foi encontrado.')
        if node.kind == "type":
            return str(node.value)
        if node.kind == "list":
            return [
                visit(child, depth + 1, f"{path}.children[{index}]")
                for index, child in enumerate(node.children)
            ]
        if node.kind == "record":
            return {
                str(child.value): visit(
                    child.children[0], depth + 1, f"{path}.children[{index}]"
                )
                for index, child in enumerate(node.children)
                if child.kind == "recordField" and child.children
            }
        if node.kind == "each":
            return visit(node.children[0], depth + 1, f"{path}.children[0]")
        if node.kind == "if":
            condition = _truth(visit(node.children[0], depth + 1, f"{path}.children[0]"))
            branch = node.children[1] if condition else node.children[2]
            return visit(branch, depth + 1, f"{path}.children[{1 if condition else 2}]")
        if node.kind == "unary":
            value = visit(node.children[0], depth + 1, f"{path}.children[0]")
            if node.value == "not":
                return not _truth(value)
            number = _number(value, culture)
            return number if node.value == "+" else -number
        if node.kind == "binary":
            operator = str(node.value)
            left = visit(node.children[0], depth + 1, f"{path}.children[0]")
            if operator == "and":
                return (
                    _truth(visit(node.children[1], depth + 1, f"{path}.children[1]"))
                    if _truth(left)
                    else False
                )
            if operator == "or":
                return (
                    True
                    if _truth(left)
                    else _truth(visit(node.children[1], depth + 1, f"{path}.children[1]"))
                )
            right = visit(node.children[1], depth + 1, f"{path}.children[1]")
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
            name = str(node.value)
            if name in _LAZY_FUNCTIONS:
                try:
                    return _call_lazy(name, node.children, visit, depth, path)
                except MExpressionError as exc:
                    exc.details.setdefault("function", name)
                    raise
            args = [
                visit(child, depth + 1, f"{path}.children[{index}]")
                for index, child in enumerate(node.children)
            ]
            try:
                return _call_scalar(name, args, culture)
            except MExpressionError as exc:
                exc.details.setdefault("function", name)
                raise
        _raise("m.expression_not_supported", f"A expressão {node.kind} não é suportada.")

    return visit(expression, 1)
