import type { ReactNode } from "react";
import { StrategicIndicatorsReferenceFilters } from "./StrategicIndicatorsReferenceFilters";
import type { StrategicIndicatorsViewMode } from "../shared/strategicIndicatorsFilters";
import "./TreeMapFloatingControls.css";

type TreeMapFloatingControlsProps = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  monthsToCompare: number;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onMonthsToCompareChange: (value: number) => void;
  actions?: ReactNode;
  status?: ReactNode;
};

export function TreeMapFloatingControls({
  referenceMonth,
  viewMode,
  branch,
  monthsToCompare,
  onReferenceMonthChange,
  onViewModeChange,
  onBranchChange,
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
          monthsToCompare={monthsToCompare}
          showMonthsToCompare
          onReferenceMonthChange={onReferenceMonthChange}
          onViewModeChange={onViewModeChange}
          onBranchChange={onBranchChange}
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
