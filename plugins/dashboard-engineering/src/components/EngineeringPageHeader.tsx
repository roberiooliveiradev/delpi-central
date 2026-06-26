import type { ReactNode } from "react";
import { DraftingCompass, ListFilter } from "lucide-react";
import { DASHBOARD_SI_DEPARTMENT_ID } from "../constants/siDepartmentId";
import type { EngineeringFilterUrlState } from "../utils/filterUrl";
import { DepartmentIddBadge } from "./DepartmentIddBadge";
import { EngineeringNav } from "./EngineeringNav";

type EngineeringPageHeaderProps = {
  title: string;
  subtitle: string;
  currentPath?: string;
  filterState?: EngineeringFilterUrlState;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function EngineeringPageHeader({
  title,
  subtitle,
  currentPath,
  filterState,
  onRefresh,
  refreshing = false,
  actions,
}: EngineeringPageHeaderProps) {
  return (
    <header className="ds-page-header">
      <div className="ds-page-header__brand">
        <div className="ds-header__icon" aria-hidden="true">
          <DraftingCompass size={28} strokeWidth={1.75} />
        </div>
        <div>
          <p className="ds-eyebrow">DELPI • Engenharia</p>
          <div className="ds-page-header__title-row">
            <h1>{title}</h1>
            {filterState ? (
              <DepartmentIddBadge
                departmentId={DASHBOARD_SI_DEPARTMENT_ID}
                filters={{
                  competence: filterState.competence,
                  dateStart: filterState.dateStart,
                  dateEnd: filterState.dateEnd,
                  branches: filterState.branches,
                }}
                classPrefix="ds"
              />
            ) : null}
          </div>
          <span className="ds-page-subtitle">{subtitle}</span>
          <EngineeringNav currentPath={currentPath} filterState={filterState} />
        </div>
      </div>

      <div className="ds-header-actions">
        {actions}
        {onRefresh ? (
          <button
            className="ds-primary-btn"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        ) : null}
      </div>
    </header>
  );
}
