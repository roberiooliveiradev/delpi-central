import type { ReactNode } from "react";
import { ListFilter, TrendingUp } from "lucide-react";
import type { CommercialFilterUrlState } from "../utils/filterUrl";
import { formatCommercialBranchPrintLabel } from "../utils/commercialClientFilters";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DASHBOARD_SI_DEPARTMENT_ID } from "../constants/siDepartmentId";
import { DepartmentIddBadge } from "./DepartmentIddBadge";
import { HelpTooltip } from "./HelpTooltip";
import { PrintReportSummary } from "./PrintReportSummary";

type CommercialPageHeaderProps = {
  filterState: CommercialFilterUrlState;
  exportActions?: ReactNode;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function CommercialPageHeader({
  filterState,
  exportActions,
  onRefresh,
  refreshing = false,
}: CommercialPageHeaderProps) {
  return (
    <>
      <PrintReportSummary
        title="Dashboard Comercial"
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
              <h1>Dashboard Comercial</h1>
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
              ROL, taxa de conversão e clientes novos (TOTVS)
              <HelpTooltip
                content={COMMERCIAL_HELP_TOOLTIPS.actions.pageSubtitle}
                ariaLabel="Ajuda: escopo do dashboard"
                className="dc-page-subtitle__help"
              />
            </span>
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
