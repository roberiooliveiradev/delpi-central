import type { ReactNode } from "react";
import type { DepartmentTreeScopeKey } from "../../data/types/departmentTree";
import { StrategicIndicatorsReferenceFilters } from "./StrategicIndicatorsReferenceFilters";
import type { StrategicIndicatorsViewMode } from "../shared/strategicIndicatorsFilters";
import "./TreeMapFloatingControls.css";

type TreeMapFloatingControlsProps = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  treeScope: DepartmentTreeScopeKey;
  monthsToCompare: number;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onTreeScopeChange: (scope: DepartmentTreeScopeKey) => void;
  onMonthsToCompareChange: (value: number) => void;
  actions?: ReactNode;
  status?: ReactNode;
};

export function TreeMapFloatingControls({
  referenceMonth,
  viewMode,
  branch,
  treeScope,
  monthsToCompare,
  onReferenceMonthChange,
  onViewModeChange,
  onBranchChange,
  onTreeScopeChange,
  onMonthsToCompareChange,
  actions,
  status,
}: TreeMapFloatingControlsProps) {
  return (
    <div className="si-tree-map-floating" data-pan-zoom-lock="true">
      <div className="si-tree-map-floating__panel">
        <StrategicIndicatorsReferenceFilters
          referenceMonth={referenceMonth}
          viewMode={viewMode}
          branch={branch}
          treeScope={treeScope}
          monthsToCompare={monthsToCompare}
          showMonthsToCompare
          viewPickerVariant="tree"
          onReferenceMonthChange={onReferenceMonthChange}
          onViewModeChange={onViewModeChange}
          onBranchChange={onBranchChange}
          onTreeScopeChange={onTreeScopeChange}
          onMonthsToCompareChange={onMonthsToCompareChange}
          className="si-tree-map-floating__filters"
        />

        {actions ? (
          <div className="si-tree-map-floating__actions">{actions}</div>
        ) : null}
      </div>

      {status ? <div className="si-tree-map-floating__status">{status}</div> : null}
    </div>
  );
}
