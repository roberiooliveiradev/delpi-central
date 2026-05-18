import { ListFilter, TrendingUp } from "lucide-react";
import type { CommercialFilterUrlState } from "../utils/filterUrl";
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
            <span className="dc-page-subtitle">
              ROL, taxa de conversão e clientes novos (TOTVS)
            </span>
          </div>
        </div>

        <div className="dc-header-actions">
          <PrintReportButton disabled={printDisabled} />
          <button
            className="dc-primary-btn dc-no-print"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </header>
    </>
  );
}
