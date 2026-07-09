import { DEPARTMENT_TREE_SCOPE_OPTIONS } from "../../data/departmentTreeScopes";
import type { DepartmentTreeScopeKey } from "../../data/types/departmentTree";
import {
  STRATEGIC_INDICATORS_BRANCH_OPTIONS,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import {
  ReferenceFilterInputField,
  ReferenceFilterSelectField,
} from "./siFiltersUi";
import "./StrategicIndicatorsReferenceFilters.css";

type StrategicIndicatorsReferenceFiltersProps = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  monthsToCompare?: number;
  showMonthsToCompare?: boolean;
  viewPickerVariant?: "default" | "tree";
  treeScope?: DepartmentTreeScopeKey;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onTreeScopeChange?: (scope: DepartmentTreeScopeKey) => void;
  onMonthsToCompareChange?: (value: number) => void;
  className?: string;
};

const VIEW_MODE_OPTIONS = [
  { value: "consolidated", label: "Consolidado" },
  { value: "branch", label: "Por unidade" },
] as const;

const MONTHS_TO_COMPARE_OPTIONS = [
  { value: "2", label: "2 meses" },
  { value: "3", label: "3 meses" },
  { value: "4", label: "4 meses" },
  { value: "6", label: "6 meses" },
  { value: "12", label: "12 meses" },
];

export function StrategicIndicatorsReferenceFilters({
  referenceMonth,
  viewMode,
  branch,
  monthsToCompare = 3,
  showMonthsToCompare = false,
  viewPickerVariant = "default",
  treeScope = "consolidated",
  onReferenceMonthChange,
  onViewModeChange,
  onBranchChange,
  onTreeScopeChange,
  onMonthsToCompareChange,
  className = "",
}: StrategicIndicatorsReferenceFiltersProps) {
  return (
    <div
      className={`si-reference-filters ${
        showMonthsToCompare ? "si-reference-filters--with-comparison" : ""
      } ${className}`.trim()}
    >
      <ReferenceFilterInputField
        id="si-reference-month"
        label="Mês de referência"
        type="month"
        value={referenceMonth}
        onChange={onReferenceMonthChange}
      />

      {viewPickerVariant === "tree" ? (
        <ReferenceFilterSelectField
          id="si-reference-tree-scope"
          label="Visão"
          value={treeScope}
          onChange={(value) => onTreeScopeChange?.(value as DepartmentTreeScopeKey)}
          options={DEPARTMENT_TREE_SCOPE_OPTIONS.map((item) => ({
            value: item.value,
            label: item.label,
          }))}
        />
      ) : (
        <>
          <ReferenceFilterSelectField
            id="si-reference-view-mode"
            label="Visão"
            value={viewMode}
            onChange={(value) => onViewModeChange(value as StrategicIndicatorsViewMode)}
            options={VIEW_MODE_OPTIONS.map((item) => ({
              value: item.value,
              label: item.label,
            }))}
          />

          {viewMode === "branch" ? (
            <ReferenceFilterSelectField
              id="si-reference-branch"
              label="Unidade"
              value={branch}
              onChange={onBranchChange}
              options={STRATEGIC_INDICATORS_BRANCH_OPTIONS.map((item) => ({
                value: item.value,
                label: item.label,
              }))}
            />
          ) : null}
        </>
      )}

      {showMonthsToCompare ? (
        <ReferenceFilterSelectField
          id="si-reference-months-compare"
          label="Meses de comparação"
          value={String(monthsToCompare)}
          onChange={(value) => onMonthsToCompareChange?.(Number(value))}
          options={MONTHS_TO_COMPARE_OPTIONS}
        />
      ) : null}
    </div>
  );
}
