import type { ExecutiveDepartmentSummary } from "../../data/types/executiveSummaryView";
import { DepartmentSummaryCard } from "./DepartmentSummaryCard";

type DepartmentSummaryGridProps = {
  departments: ExecutiveDepartmentSummary[];
};

export function DepartmentSummaryGrid({
  departments,
}: DepartmentSummaryGridProps) {
  return (
    <div className="si-department-grid">
      {departments.map((department) => (
        <DepartmentSummaryCard
          key={department.id}
          department={department}
        />
      ))}
    </div>
  );
}