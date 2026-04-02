import type { DepartmentSummary } from "../../data/mocks/executiveDashboardMock";
import { DepartmentSummaryCard } from "./DepartmentSummaryCard";

type DepartmentSummaryGridProps = {
  departments: DepartmentSummary[];
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