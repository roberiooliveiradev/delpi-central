import { formatProcedureCount } from "../content/catalog";
import type { DepartmentSummary } from "../types/guide";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";
import { DepartmentIcon } from "./DepartmentIcon";

type DepartmentShortcutProps = {
  department: DepartmentSummary;
};

export function DepartmentShortcut({ department }: DepartmentShortcutProps) {
  const href = GUIAS_PROCEDIMENTOS_ROUTES.department(department.slug);
  const accessibleName = `${department.name}, ${formatProcedureCount(department.guideCount)}`;

  return (
    <a
      className="gp-dept-shortcut"
      href={href}
      aria-label={accessibleName}
      onClick={(event) => {
        event.preventDefault();
        navigateGuiasProcedimentos(href);
      }}
    >
      <span className="gp-dept-shortcut__circle" aria-hidden="true">
        <DepartmentIcon icon={department.icon} size={28} />
      </span>
      <span className="gp-dept-shortcut__name">{department.name}</span>
      <span className="gp-dept-shortcut__count">
        {formatProcedureCount(department.guideCount)}
      </span>
    </a>
  );
}
