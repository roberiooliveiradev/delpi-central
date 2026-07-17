"""IR tipada e imutável consumida pela fachada tabular canônica."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

FilterValue: TypeAlias = str | int | float | bool | None


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
