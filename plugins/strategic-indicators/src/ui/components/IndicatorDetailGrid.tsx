import type { DepartmentIndicator } from "../../data/types/departmentDetails";
import { IndicatorDetailCard } from "./IndicatorDetailCard";

type IndicatorDetailGridProps = {
  indicators: DepartmentIndicator[];
};

export function IndicatorDetailGrid({
  indicators,
}: IndicatorDetailGridProps) {
  return (
    <div className="si-indicator-grid">
      {indicators.map((indicator) => (
        <IndicatorDetailCard
          key={indicator.id}
          indicator={indicator}
        />
      ))}
    </div>
  );
}