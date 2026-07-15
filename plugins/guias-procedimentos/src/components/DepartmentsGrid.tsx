import { DepartmentShortcut } from "./DepartmentShortcut";
import type { DepartmentSummary } from "../types/guide";
import { DEPARTMENTS_SECTION_TITLE } from "../content/catalog";

type DepartmentsGridProps = {
  departments: DepartmentSummary[];
};

export function DepartmentsGrid({ departments }: DepartmentsGridProps) {
  if (departments.length === 0) return null;

  return (
    <section className="gp-departments" aria-labelledby="gp-departments-title">
      <h2 className="gp-departments__title" id="gp-departments-title">
        {DEPARTMENTS_SECTION_TITLE}
      </h2>
      <div className="gp-departments__grid" role="list">
        {departments.map((department) => (
          <div key={department.id} className="gp-departments__item" role="listitem">
            <DepartmentShortcut department={department} />
          </div>
        ))}
      </div>
    </section>
  );
}
