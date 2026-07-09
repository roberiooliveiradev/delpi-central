import type { ReactNode } from "react";
import { ListFilter, TrendingUp } from "lucide-react";
import type { CommercialFilterUrlState } from "../utils/filterUrl";
import { formatCommercialBranchPrintLabel } from "../utils/commercialClientFilters";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DASHBOARD_SI_DEPARTMENT_ID } from "../constants/siDepartmentId";
import { COMMERCIAL_ROUTES } from "../constants/routes";
import { DepartmentIddBadge } from "./DepartmentIddBadge";
import { CommercialNav } from "./CommercialNav";
import { HelpTooltip } from "@delpi/plugin-ui";
import { PrintReportSummary } from "./PrintReportSummary";

type CommercialPageHeaderProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: CommercialFilterUrlState;
  exportActions?: ReactNode;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function CommercialPageHeader({
  title = "Dashboard Comercial",
  subtitle = "ROL, taxa de conversão e clientes novos (TOTVS)",
  currentPath,
  filterState,
  exportActions,
  onRefresh,
  refreshing = false,
}: CommercialPageHeaderProps) {
  return (
    <>
      <PrintReportSummary
        title={title}
        dateStart={filterState.dateStart}
        dateEnd={filterState.dateEnd}
        branchLabel={formatCommercialBranchPrintLabel(filterState.branches)}
      />

      <header className="dc-page-header dc-screen-only">
        <div className="dc-page-header__brand">
          <div className="dc-header__icon" aria-hidden="true">
            <TrendingUp size={28} strokeWidth={1.75} />
          </div>
          <div>
            <p className="dc-eyebrow">DELPI • Comercial</p>
            <div className="dc-page-header__title-row">
              <h1>{title}</h1>
              <DepartmentIddBadge
                departmentId={DASHBOARD_SI_DEPARTMENT_ID}
                filters={{
                  competence: filterState.competence,
                  dateStart: filterState.dateStart,
                  dateEnd: filterState.dateEnd,
                  branches: filterState.branches,
                }}
              />
            </div>
            <span className="dc-page-subtitle dc-page-subtitle--with-help">
              {subtitle}
              <HelpTooltip
                content={COMMERCIAL_HELP_TOOLTIPS.actions.pageSubtitle}
                ariaLabel="Ajuda: escopo do dashboard"
                className="dc-page-subtitle__help"
              />
            </span>
            <CommercialNav
              currentPath={currentPath ?? COMMERCIAL_ROUTES.home}
              filterState={filterState}
            />
          </div>
        </div>

        <div className="dc-header-actions">
          {exportActions ? (
            <div className="dc-header-action dc-no-print">{exportActions}</div>
          ) : null}
          <div className="dc-header-action">
            <button
              className="dc-primary-btn dc-no-print"
              type="button"
              onClick={onRefresh}
              disabled={refreshing}
            >
              <ListFilter size={16} />
              {refreshing ? "Atualizando…" : "Atualizar"}
            </button>
            <HelpTooltip
              content={COMMERCIAL_HELP_TOOLTIPS.actions.refresh}
              ariaLabel="Ajuda: atualizar dashboard"
              className="dc-header-action__help"
            />
          </div>
        </div>
      </header>
    </>
  );
}
