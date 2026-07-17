"""Adapter da IR legada v1 para o TransformPlan tipado."""

from __future__ import annotations

from typing import Any

from tv_app.domain.data_query.transform_plan import (
    AddColumnStep,
    AggregationSpec,
    ChangeTypeStep,
    FillDownStep,
    FilterStep,
    GroupByStep,
    MergeStep,
    PivotStep,
    PromoteHeadersStep,
    RenameStep,
    ReplaceStep,
    RowCountStep,
    SelectStep,
    SortStep,
    TransformOperation,
    TransformPlan,
    UnpivotStep,
)

_COMPARATORS = frozenset({"eq", "neq", "gt", "lt", "notNull", "contains", "startsWith"})
_AGGREGATIONS = frozenset({"sum", "avg", "min", "max", "count", "first"})
_STEP_LABELS = {
    "rename": "Colunas renomeadas",
    "select": "Colunas selecionadas",
    "filter": "Linhas filtradas",
    "addColumn": "Coluna adicionada",
    "replace": "Valor substituído",
    "sort": "Linhas ordenadas",
    "keepRows": "Linhas mantidas",
    "removeRows": "Linhas removidas",
    "changeType": "Tipo alterado",
    "fillDown": "Preenchido para baixo",
    "firstRowAsHeader": "Cabeçalhos promovidos",
    "groupBy": "Linhas agrupadas",
    "pivot": "Coluna dinamizada",
    "unpivot": "Colunas anuladas",
    "merge": "Consultas mescladas",
}


def _strings(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [value for item in raw if (value := str(item).strip())]


def normalize_legacy_transform(raw: Any) -> dict[str, Any] | None:
    """Normaliza somente o contrato v1; ignora campos desconhecidos."""

    if not isinstance(raw, dict):
        return None
    source = raw.get("steps")
    if not isinstance(source, list) or not source:
        return None
    steps: list[dict[str, Any]] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        op = str(item.get("op") or "").strip()
        if op == "rename":
            source_column = str(item.get("from") or "").strip()
            target_column = str(item.get("to") or "").strip()
            if source_column and target_column:
                steps.append({"op": op, "from": source_column, "to": target_column})
        elif op == "select":
            columns = _strings(item.get("columns"))
            if columns:
                steps.append({"op": op, "columns": columns})
        elif op == "filter":
            column = str(item.get("column") or "").strip()
            comparator = str(item.get("cmp") or "").strip()
            if column and comparator in _COMPARATORS:
                step = {"op": op, "column": column, "cmp": comparator}
                if "value" in item:
                    step["value"] = item.get("value")
                steps.append(step)
        elif op == "addColumn":
            name = str(item.get("name") or "").strip()
            expression = str(item.get("expr") or "").strip()
            if name and expression:
                steps.append({"op": op, "name": name, "expr": expression})
        elif op == "replace":
            column = str(item.get("column") or "").strip()
            if column:
                steps.append(
                    {
                        "op": op,
                        "column": column,
                        "find": str(item.get("find") if item.get("find") is not None else ""),
                        "replaceWith": str(
                            item.get("replaceWith")
                            if item.get("replaceWith") is not None
                            else item.get("replace")
                            if item.get("replace") is not None
                            else ""
                        ),
                    }
                )
        elif op == "sort":
            column = str(item.get("column") or "").strip()
            if column:
                steps.append(
                    {
                        "op": op,
                        "column": column,
                        "direction": "desc"
                        if str(item.get("direction") or "").strip() == "desc"
                        else "asc",
                    }
                )
        elif op in {"keepRows", "removeRows"}:
            try:
                count = max(0, int(item.get("count") or 0))
            except (TypeError, ValueError):
                count = 0
            if count:
                steps.append(
                    {
                        "op": op,
                        "count": count,
                        "from": "bottom"
                        if str(item.get("from") or "").strip() == "bottom"
                        else "top",
                    }
                )
        elif op == "changeType":
            column = str(item.get("column") or "").strip()
            if column:
                steps.append(
                    {
                        "op": op,
                        "column": column,
                        "to": "number"
                        if str(item.get("to") or "").strip() == "number"
                        else "string",
                    }
                )
        elif op == "fillDown":
            column = str(item.get("column") or "").strip()
            if column:
                steps.append({"op": op, "column": column})
        elif op == "firstRowAsHeader":
            steps.append({"op": op})
        elif op == "groupBy":
            keys = _strings(item.get("keys"))
            aggregations: list[dict[str, str]] = []
            for raw_aggregation in item.get("aggregations") or []:
                if not isinstance(raw_aggregation, dict):
                    continue
                column = str(raw_aggregation.get("column") or "").strip()
                function = str(raw_aggregation.get("fn") or "").strip()
                if column and function in _AGGREGATIONS:
                    aggregations.append(
                        {
                            "column": column,
                            "fn": function,
                            "as": str(raw_aggregation.get("as") or "").strip()
                            or f"{column}_{function}",
                        }
                    )
            if keys and aggregations:
                steps.append({"op": op, "keys": keys, "aggregations": aggregations})
        elif op == "pivot":
            column = str(item.get("column") or "").strip()
            value_column = str(item.get("valueColumn") or "").strip()
            aggregation = str(item.get("aggregation") or "").strip()
            if column and value_column:
                steps.append(
                    {
                        "op": op,
                        "column": column,
                        "valueColumn": value_column,
                        "aggregation": aggregation if aggregation in _AGGREGATIONS else "sum",
                    }
                )
        elif op == "unpivot":
            columns = _strings(item.get("columns"))
            if columns:
                steps.append(
                    {
                        "op": op,
                        "columns": columns,
                        "nameColumn": str(item.get("nameColumn") or "").strip() or "atributo",
                        "valueColumn": str(item.get("valueColumn") or "").strip() or "valor",
                    }
                )
        elif op == "merge":
            source_id = str(item.get("sourceId") or "").strip()
            left_key = str(item.get("leftKey") or "").strip()
            right_key = str(item.get("rightKey") or "").strip()
            if source_id and left_key and right_key:
                step = {
                    "op": op,
                    "sourceId": source_id,
                    "leftKey": left_key,
                    "rightKey": right_key,
                    "join": "left",
                }
                columns = _strings(item.get("columns"))
                if columns:
                    step["columns"] = columns
                steps.append(step)
    return {"steps": steps} if steps else None


def _unique_step_name(op: str, counts: dict[str, int]) -> str:
    base = _STEP_LABELS[op]
    counts[base] = counts.get(base, 0) + 1
    return base if counts[base] == 1 else f"{base} {counts[base]}"


def legacy_steps_to_plan(raw: Any) -> TransformPlan | None:
    normalized = normalize_legacy_transform(raw)
    if normalized is None:
        return None
    plan_steps = []
    previous = "Fonte"
    counts: dict[str, int] = {}
    referenced_queries: list[str] = []
    for step in normalized["steps"]:
        op = step["op"]
        name = _unique_step_name(op, counts)
        common = {"name": name, "input_name": previous}
        if op == "rename":
            typed = RenameStep(
                **common,
                source_column=step["from"],
                target_column=step["to"],
            )
        elif op == "select":
            typed = SelectStep(**common, columns=tuple(step["columns"]))
        elif op == "filter":
            value = step.get("value")
            if not isinstance(value, (str, int, float, bool, type(None))):
                value = str(value)
            typed = FilterStep(
                **common,
                column=step["column"],
                comparator=step["cmp"],
                value=value,
            )
        elif op == "addColumn":
            typed = AddColumnStep(
                **common,
                column=step["name"],
                legacy_expression=step["expr"],
            )
        elif op == "replace":
            typed = ReplaceStep(
                **common,
                column=step["column"],
                find=step["find"],
                replacement=step["replaceWith"],
            )
        elif op == "sort":
            typed = SortStep(**common, column=step["column"], direction=step["direction"])
        elif op in {"keepRows", "removeRows"}:
            typed = RowCountStep(
                **common,
                count=step["count"],
                from_end=step["from"] == "bottom",
                operation=(
                    TransformOperation.KEEP_ROWS
                    if op == "keepRows"
                    else TransformOperation.REMOVE_ROWS
                ),
            )
        elif op == "changeType":
            typed = ChangeTypeStep(
                **common,
                column=step["column"],
                target_type=step["to"],
            )
        elif op == "fillDown":
            typed = FillDownStep(**common, column=step["column"])
        elif op == "firstRowAsHeader":
            typed = PromoteHeadersStep(**common)
        elif op == "groupBy":
            typed = GroupByStep(
                **common,
                keys=tuple(step["keys"]),
                aggregations=tuple(
                    AggregationSpec(
                        column=aggregation["column"],
                        function=aggregation["fn"],
                        output_column=aggregation["as"],
                    )
                    for aggregation in step["aggregations"]
                ),
            )
        elif op == "pivot":
            typed = PivotStep(
                **common,
                column=step["column"],
                value_column=step["valueColumn"],
                aggregation=step["aggregation"],
            )
        elif op == "unpivot":
            typed = UnpivotStep(
                **common,
                columns=tuple(step["columns"]),
                name_column=step["nameColumn"],
                value_column=step["valueColumn"],
            )
        else:
            typed = MergeStep(
                **common,
                source_id=step["sourceId"],
                left_key=step["leftKey"],
                right_key=step["rightKey"],
                columns=tuple(step.get("columns") or ()),
            )
            if step["sourceId"] not in referenced_queries:
                referenced_queries.append(step["sourceId"])
        plan_steps.append(typed)
        previous = name
    return TransformPlan(
        version=1,
        profile="m-delpi-v1",
        steps=tuple(plan_steps),
        output=previous,
        referenced_queries=tuple(referenced_queries),
    )


def plan_to_legacy_steps(plan: TransformPlan) -> list[dict[str, Any]]:
    """Ponte temporária para o executor existente; não é formato persistido v2."""

    steps: list[dict[str, Any]] = []
    for step in plan.steps:
        if isinstance(step, RenameStep):
            payload = {
                "op": "rename",
                "from": step.source_column,
                "to": step.target_column,
            }
        elif isinstance(step, SelectStep):
            payload = {"op": "select", "columns": list(step.columns)}
        elif isinstance(step, FilterStep):
            payload = {
                "op": "filter",
                "column": step.column,
                "cmp": step.comparator,
                "value": step.value,
            }
        elif isinstance(step, AddColumnStep):
            payload = {
                "op": "addColumn",
                "name": step.column,
                "expr": step.legacy_expression,
            }
        elif isinstance(step, ReplaceStep):
            payload = {
                "op": "replace",
                "column": step.column,
                "find": step.find,
                "replaceWith": step.replacement,
            }
        elif isinstance(step, SortStep):
            payload = {
                "op": "sort",
                "column": step.column,
                "direction": step.direction,
            }
        elif isinstance(step, RowCountStep):
            payload = {
                "op": step.operation.value,
                "count": step.count,
                "from": "bottom" if step.from_end else "top",
            }
        elif isinstance(step, ChangeTypeStep):
            payload = {
                "op": "changeType",
                "column": step.column,
                "to": step.target_type,
            }
        elif isinstance(step, FillDownStep):
            payload = {"op": "fillDown", "column": step.column}
        elif isinstance(step, PromoteHeadersStep):
            payload = {"op": "firstRowAsHeader"}
        elif isinstance(step, GroupByStep):
            payload = {
                "op": "groupBy",
                "keys": list(step.keys),
                "aggregations": [
                    {
                        "column": aggregation.column,
                        "fn": aggregation.function,
                        "as": aggregation.output_column,
                    }
                    for aggregation in step.aggregations
                ],
            }
        elif isinstance(step, PivotStep):
            payload = {
                "op": "pivot",
                "column": step.column,
                "valueColumn": step.value_column,
                "aggregation": step.aggregation,
            }
        elif isinstance(step, UnpivotStep):
            payload = {
                "op": "unpivot",
                "columns": list(step.columns),
                "nameColumn": step.name_column,
                "valueColumn": step.value_column,
            }
        elif isinstance(step, MergeStep):
            payload = {
                "op": "merge",
                "sourceId": step.source_id,
                "leftKey": step.left_key,
                "rightKey": step.right_key,
                "join": "left",
            }
            if step.columns:
                payload["columns"] = list(step.columns)
        else:  # pragma: no cover - união fechada protegida pelo domínio
            raise TypeError(f"Etapa desconhecida: {type(step).__name__}")
        steps.append(payload)
    return steps
