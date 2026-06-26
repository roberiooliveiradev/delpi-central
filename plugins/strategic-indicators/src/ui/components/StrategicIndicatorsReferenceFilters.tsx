import { DEPARTMENT_TREE_SCOPE_OPTIONS } from "../../data/departmentTreeScopes";
import type { DepartmentTreeScopeKey } from "../../data/types/departmentTree";
import {
  STRATEGIC_INDICATORS_BRANCH_OPTIONS,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
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
      <label className="si-reference-filters__field">
        <span className="si-reference-filters__label">Mês de referência</span>
        <input
          type="month"
          className="si-reference-filters__input"
          value={referenceMonth}
          onChange={(event) => onReferenceMonthChange(event.target.value)}
        />
      </label>

      {viewPickerVariant === "tree" ? (
        <label className="si-reference-filters__field">
          <span className="si-reference-filters__label">Visão</span>
          <select
            className="si-reference-filters__input"
            value={treeScope}
            onChange={(event) =>
              onTreeScopeChange?.(event.target.value as DepartmentTreeScopeKey)
            }
          >
            {DEPARTMENT_TREE_SCOPE_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <>
          <label className="si-reference-filters__field">
            <span className="si-reference-filters__label">Visão</span>
            <select
              className="si-reference-filters__input"
              value={viewMode}
              onChange={(event) =>
                onViewModeChange(
                  event.target.value as StrategicIndicatorsViewMode,
                )
              }
            >
              <option value="consolidated">Consolidado</option>
              <option value="branch">Por unidade</option>
            </select>
          </label>

          {viewMode === "branch" ? (
            <label className="si-reference-filters__field">
              <span className="si-reference-filters__label">Unidade</span>
              <select
                className="si-reference-filters__input"
                value={branch}
                onChange={(event) => onBranchChange(event.target.value)}
              >
                {STRATEGIC_INDICATORS_BRANCH_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </>
      )}

      {showMonthsToCompare ? (
        <label className="si-reference-filters__field">
          <span className="si-reference-filters__label">
            Meses de comparação
          </span>

          <select
            className="si-reference-filters__input"
            value={monthsToCompare}
            onChange={(event) =>
              onMonthsToCompareChange?.(Number(event.target.value))
            }
          >
            <option value={2}>2 meses</option>
            <option value={3}>3 meses</option>
            <option value={4}>4 meses</option>
            <option value={6}>6 meses</option>
            <option value={12}>12 meses</option>
          </select>
        </label>
      ) : null}
    </div>
  );
}