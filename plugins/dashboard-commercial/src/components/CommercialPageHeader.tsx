import { ListFilter, TrendingUp } from "lucide-react";
import type { CommercialFilterUrlState } from "../utils/filterUrl";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { HelpTooltip } from "./HelpTooltip";
import { PrintReportButton } from "./PrintReportButton";
import { PrintReportSummary } from "./PrintReportSummary";

type CommercialPageHeaderProps = {
  filterState: CommercialFilterUrlState;
  printDisabled?: boolean;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function CommercialPageHeader({
  filterState,
  printDisabled = false,
  onRefresh,
  refreshing = false,
}: CommercialPageHeaderProps) {
  return (
    <>
      <PrintReportSummary
        title="Dashboard Comercial"
        dateStart={filterState.dateStart}
        dateEnd={filterState.dateEnd}
        branch={filterState.branch}
      />

      <header className="dc-page-header dc-screen-only">
        <div className="dc-page-header__brand">
          <div className="dc-header__icon" aria-hidden="true">
            <TrendingUp size={28} strokeWidth={1.75} />
          </div>
          <div>
            <p className="dc-eyebrow">DELPI • Comercial</p>
            <h1>Dashboard Comercial</h1>
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
          <div className="dc-header-action">
            <PrintReportButton disabled={printDisabled} />
            <HelpTooltip
              content={COMMERCIAL_HELP_TOOLTIPS.actions.print}
              ariaLabel="Ajuda: imprimir relatório"
              className="dc-header-action__help"
            />
          </div>
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
