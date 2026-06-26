import type { ReactNode } from "react";
import { ListFilter, Users } from "lucide-react";

import { DASHBOARD_SI_DEPARTMENT_ID } from "../constants/siDepartmentId";
import type { DepartmentIddFilterInput } from "../utils/departmentIddFilters";
import { DepartmentIddBadge } from "./DepartmentIddBadge";

type HrPageHeaderProps = {
  title: string;
  subtitle: string;
  iddFilters?: DepartmentIddFilterInput;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function HrPageHeader({
  title,
  subtitle,
  iddFilters,
  onRefresh,
  refreshing = false,
  actions,
}: HrPageHeaderProps) {
  return (
    <header className="dh-page-header">
      <div className="dh-page-header__brand">
        <div className="dh-header__icon" aria-hidden="true">
          <Users size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="dh-eyebrow">DELPI • Recursos Humanos</p>
          <div className="dh-page-header__title-row">
            <h1>{title}</h1>
            {iddFilters ? (
              <DepartmentIddBadge
                departmentId={DASHBOARD_SI_DEPARTMENT_ID}
                filters={iddFilters}
                classPrefix="dh"
              />
            ) : null}
          </div>
          <span className="dh-page-subtitle">{subtitle}</span>
        </div>
      </div>

      {onRefresh ? (
        <div className="dh-header-actions">
          {actions}
          <button
            className="dh-primary-btn"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      ) : null}
    </header>
  );
}
