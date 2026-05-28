import type { DepartmentIndicator } from "../../data/types/departmentDetails";
import type { StrategicIndicatorsViewMode } from "../shared/strategicIndicatorsFilters";
import { IndicatorDetailCard } from "./IndicatorDetailCard";
import "./IndicatorDetailGrid.css";

type IndicatorDetailGridProps = {
  indicators: DepartmentIndicator[];
  competence?: string | null;
  viewMode?: StrategicIndicatorsViewMode;
  branch?: string;
};

export function IndicatorDetailGrid({
  indicators,
  competence,
  viewMode = "consolidated",
  branch = "",
}: IndicatorDetailGridProps) {
  return (
    <div className="si-indicator-grid">
      {indicators.map((indicator) => (
        <IndicatorDetailCard
          key={indicator.id}
          indicator={indicator}
          competence={competence}
          viewMode={viewMode}
          branch={branch}
        />
      ))}
    </div>
  );
}