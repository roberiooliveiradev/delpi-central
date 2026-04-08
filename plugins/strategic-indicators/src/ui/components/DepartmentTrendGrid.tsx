import type { DepartmentTrendItem } from "../../data/types/trends";
import { DepartmentTrendCard } from "./DepartmentTrendCard";

type DepartmentTrendGridProps = {
  departments: DepartmentTrendItem[];
};

export function DepartmentTrendGrid({
  departments,
}: DepartmentTrendGridProps) {
  return (
    <div className="si-department-trend-grid">
      {departments.map((department) => (
        <DepartmentTrendCard
          key={department.id}
          department={department}
        />
      ))}
    </div>
  );
}