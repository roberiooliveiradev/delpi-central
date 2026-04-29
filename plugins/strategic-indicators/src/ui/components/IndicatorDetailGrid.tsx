import type { DepartmentIndicator } from "../../data/types/departmentDetails";
import { IndicatorDetailCard } from "./IndicatorDetailCard";
import "./IndicatorDetailGrid.css";

type IndicatorDetailGridProps = {
  indicators: DepartmentIndicator[];
  competence?: string | null;
};

export function IndicatorDetailGrid({
  indicators,
  competence,
}: IndicatorDetailGridProps) {
  return (
    <div className="si-indicator-grid">
      {indicators.map((indicator) => (
        <IndicatorDetailCard
          key={indicator.id}
          indicator={indicator}
          competence={competence}
        />
      ))}
    </div>
  );
}