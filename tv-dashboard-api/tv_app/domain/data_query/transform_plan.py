"""IR tipada e imutável consumida pela fachada tabular canônica."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, TypeAlias

FilterValue: TypeAlias = str | int | float | bool | None


class ExpressionSpecError(ValueError):
    """Spec serializado inválido para CompiledExpression (deny-by-default)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_SPEC_NODE_KINDS = frozenset(
    {
        "literal",
        "identifier",
        "field",
        "type",
        "call",
        "each",
        "if",
        "unary",
        "binary",
        "list",
        "record",
        "recordField",
    }
)

_SPEC_NODE_KEYS = frozenset({"kind", "value", "children"})

_BINARY_OPERATORS = frozenset(
    {"+", "-", "*", "/", "=", "<>", ">", ">=", "<", "<=", "and", "or", "&"}
)

_UNARY_OPERATORS = frozenset({"+", "-", "not"})

_LITERAL_TYPES = (str, int, float, bool)


def _spec_fail(code: str, message: str) -> None:
    raise ExpressionSpecError(code, message)


@dataclass(frozen=True, slots=True)
class CompiledExpression:
    """Expressão segura serializável; nunca contém código Python executável."""

    kind: str
    value: FilterValue | str | None = None
    children: tuple["CompiledExpression", ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"kind": self.kind}
        if self.value is not None:
            payload["value"] = self.value
        if self.children:
            payload["children"] = [child.to_dict() for child in self.children]
        return payload

    @classmethod
    def from_dict(
        cls,
        payload: Any,
        *,
        max_depth: int = 40,
        max_nodes: int = 256,
        max_string_bytes: int = 512,
    ) -> "CompiledExpression":
        """Reconstrói o IR a partir de JSON persistido, com validação estrita.

        Sem fallback permissivo: kind desconhecido, campo extra, aridade ou
        tipo de literal inválidos abortam com ``ExpressionSpecError`` tipado.
        """
        counter = {"count": 0}

        def parse(node: Any, depth: int) -> "CompiledExpression":
            if depth > max_depth:
                _spec_fail(
                    "m.expression_complexity_limit",
                    "A expressão excedeu a profundidade permitida.",
                )
            counter["count"] += 1
            if counter["count"] > max_nodes:
                _spec_fail(
                    "m.expression_complexity_limit",
                    "A expressão excedeu o número de nós permitido.",
                )
            if not isinstance(node, Mapping):
                _spec_fail(
                    "m.expression_schema_invalid",
                    "Nó da expressão deve ser um objeto.",
                )
            unknown_keys = set(node.keys()) - _SPEC_NODE_KEYS
            if unknown_keys:
                _spec_fail(
                    "m.expression_schema_invalid",
                    "Nó da expressão contém campos não permitidos.",
                )
            kind = node.get("kind")
            if not isinstance(kind, str) or kind not in _SPEC_NODE_KINDS:
                _spec_fail(
                    "m.expression_schema_invalid",
                    "Tipo de nó de expressão não permitido.",
                )
            value = node.get("value")
            if isinstance(value, str) and len(value.encode("utf-8")) > max_string_bytes:
                _spec_fail(
                    "m.expression_complexity_limit",
                    "Literal/identificador da expressão excede o tamanho permitido.",
                )
            raw_children = node.get("children")
            if raw_children is None:
                children: tuple["CompiledExpression", ...] = ()
            elif isinstance(raw_children, list):
                children = tuple(
                    parse(child, depth + 1) for child in raw_children
                )
            else:
                _spec_fail(
                    "m.expression_schema_invalid",
                    "children da expressão deve ser uma lista.",
                )

            expected_children = {
                "if": 3,
                "each": 1,
                "unary": 1,
                "recordField": 1,
                "binary": 2,
            }
            if kind in expected_children and len(children) != expected_children[kind]:
                _spec_fail(
                    "m.expression_schema_invalid",
                    f"Nó {kind} exige {expected_children[kind]} filho(s).",
                )
            if kind == "literal":
                if children:
                    _spec_fail(
                        "m.expression_schema_invalid",
                        "Nó literal não aceita filhos.",
                    )
                if value is not None and not isinstance(value, _LITERAL_TYPES):
                    _spec_fail(
                        "m.expression_schema_invalid",
                        "Literal deve ser string, número, booleano ou null.",
                    )
            elif kind in {"identifier", "field", "type", "recordField"}:
                if not isinstance(value, str) or not value.strip():
                    _spec_fail(
                        "m.expression_schema_invalid",
                        f"Nó {kind} exige nome textual não vazio.",
                    )
                if kind != "recordField" and children:
                    _spec_fail(
                        "m.expression_schema_invalid",
                        f"Nó {kind} não aceita filhos.",
                    )
            elif kind == "call":
                if not isinstance(value, str) or not value.strip():
                    _spec_fail(
                        "m.expression_schema_invalid",
                        "Nó call exige nome de função.",
                    )
                if not children:
                    _spec_fail(
                        "m.expression_schema_invalid",
                        "Nó call exige ao menos um argumento.",
                    )
            elif kind == "unary" and str(value) not in _UNARY_OPERATORS:
                _spec_fail(
                    "m.expression_schema_invalid",
                    "Operador unário não permitido.",
                )
            elif kind == "binary" and str(value) not in _BINARY_OPERATORS:
                _spec_fail(
                    "m.expression_schema_invalid",
                    "Operador binário não permitido.",
                )
            return cls(kind=kind, value=value, children=children)

        return parse(payload, 1)


class TransformOperation(StrEnum):
    RENAME = "rename"
    SELECT = "select"
    FILTER = "filter"
    ADD_COLUMN = "addColumn"
    REPLACE = "replace"
    SORT = "sort"
    KEEP_ROWS = "keepRows"
    REMOVE_ROWS = "removeRows"
    CHANGE_TYPE = "changeType"
    FILL_DOWN = "fillDown"
    FIRST_ROW_AS_HEADER = "firstRowAsHeader"
    GROUP_BY = "groupBy"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"
    MERGE = "merge"


@dataclass(frozen=True, slots=True)
class AggregationSpec:
    column: str
    function: str
    output_column: str


@dataclass(frozen=True, slots=True)
class PlanStepBase:
    name: str
    input_name: str

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.input_name.strip():
            raise ValueError("Nome e entrada da etapa são obrigatórios.")


@dataclass(frozen=True, slots=True)
class RenameStep(PlanStepBase):
    source_column: str
    target_column: str
    operation = TransformOperation.RENAME


@dataclass(frozen=True, slots=True)
class SelectStep(PlanStepBase):
    columns: tuple[str, ...]
    operation = TransformOperation.SELECT


@dataclass(frozen=True, slots=True)
class FilterStep(PlanStepBase):
    column: str
    comparator: str
    value: FilterValue = None
    operation = TransformOperation.FILTER


@dataclass(frozen=True, slots=True)
class AddColumnStep(PlanStepBase):
    column: str
    legacy_expression: str
    operation = TransformOperation.ADD_COLUMN


@dataclass(frozen=True, slots=True)
class ReplaceStep(PlanStepBase):
    column: str
    find: str
    replacement: str
    operation = TransformOperation.REPLACE


@dataclass(frozen=True, slots=True)
class SortStep(PlanStepBase):
    column: str
    direction: str
    operation = TransformOperation.SORT


@dataclass(frozen=True, slots=True)
class RowCountStep(PlanStepBase):
    count: int
    from_end: bool
    operation: TransformOperation

    def __post_init__(self) -> None:
        PlanStepBase.__post_init__(self)
        if self.operation not in {
            TransformOperation.KEEP_ROWS,
            TransformOperation.REMOVE_ROWS,
        }:
            raise ValueError("RowCountStep aceita somente keepRows/removeRows.")


@dataclass(frozen=True, slots=True)
class ChangeTypeStep(PlanStepBase):
    column: str
    target_type: str
    operation = TransformOperation.CHANGE_TYPE


@dataclass(frozen=True, slots=True)
class FillDownStep(PlanStepBase):
    column: str
    operation = TransformOperation.FILL_DOWN


@dataclass(frozen=True, slots=True)
class PromoteHeadersStep(PlanStepBase):
    operation = TransformOperation.FIRST_ROW_AS_HEADER


@dataclass(frozen=True, slots=True)
class GroupByStep(PlanStepBase):
    keys: tuple[str, ...]
    aggregations: tuple[AggregationSpec, ...]
    operation = TransformOperation.GROUP_BY


@dataclass(frozen=True, slots=True)
class PivotStep(PlanStepBase):
    column: str
    value_column: str
    aggregation: str
    operation = TransformOperation.PIVOT


@dataclass(frozen=True, slots=True)
class UnpivotStep(PlanStepBase):
    columns: tuple[str, ...]
    name_column: str
    value_column: str
    operation = TransformOperation.UNPIVOT


@dataclass(frozen=True, slots=True)
class MergeStep(PlanStepBase):
    source_id: str
    left_key: str
    right_key: str
    columns: tuple[str, ...]
    operation = TransformOperation.MERGE


@dataclass(frozen=True, slots=True)
class CompiledMPlanStep(PlanStepBase):
    """Etapa produzida pelo compilador M; execução pertence à Fase 3."""

    function_name: str
    arguments: tuple[CompiledExpression, ...]

    @property
    def operation(self) -> str:
        return self.function_name


PlanStep: TypeAlias = (
    RenameStep
    | SelectStep
    | FilterStep
    | AddColumnStep
    | ReplaceStep
    | SortStep
    | RowCountStep
    | ChangeTypeStep
    | FillDownStep
    | PromoteHeadersStep
    | GroupByStep
    | PivotStep
    | UnpivotStep
    | MergeStep
    | CompiledMPlanStep
)


@dataclass(frozen=True, slots=True)
class TransformPlan:
    version: int
    profile: str
    steps: tuple[PlanStep, ...]
    output: str
    referenced_queries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValueError("Versão de TransformPlan não suportada.")
        if not self.profile.strip() or not self.output.strip():
            raise ValueError("Profile e output do TransformPlan são obrigatórios.")
        names = [step.name for step in self.steps]
        if len(names) != len(set(names)):
            raise ValueError("Nomes de etapas do TransformPlan devem ser únicos.")
        if self.steps and self.output != self.steps[-1].name:
            raise ValueError("Output deve apontar para a última etapa do plano legado.")
