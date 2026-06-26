import type { ReactNode } from "react";
import { Award, ListFilter } from "lucide-react";
import type { QualityFilterUrlState } from "../utils/filterUrl";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import { PrintReportButton } from "./PrintReportButton";
import { PrintReportSummary } from "./PrintReportSummary";
import { QualityNav } from "./QualityNav";

type QualityPageHeaderProps = {
  title: string;
  subtitle: string;
  currentPath?: string;
  filterState?: QualityFilterUrlState;
  printFilters?: Pick<QualityFilterUrlState, "dateStart" | "dateEnd" | "branches">;
  showPrint?: boolean;
  printDisabled?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
};

export function QualityPageHeader({
  title,
  subtitle,
  currentPath,
  filterState,
  printFilters,
  showPrint = true,
  printDisabled = false,
  onRefresh,
  refreshing = false,
  actions,
}: QualityPageHeaderProps) {
  const summaryFilters = printFilters ?? filterState;

  return (
    <>
      {summaryFilters ? (
        <PrintReportSummary
          title={title}
          dateStart={summaryFilters.dateStart}
          dateEnd={summaryFilters.dateEnd}
          branch={formatBranchFilterLabel(summaryFilters.branches)}
        />
      ) : null}

      <header className="dq-page-header dq-screen-only">
        <div className="dq-page-header__brand">
          <div className="dq-header__icon" aria-hidden="true">
            <Award size={28} strokeWidth={1.75} />
          </div>
          <div>
            <p className="dq-eyebrow">DELPI • Qualidade</p>
            <h1>{title}</h1>
            <span className="dq-page-subtitle">{subtitle}</span>
            <QualityNav currentPath={currentPath} filterState={filterState} />
          </div>
        </div>

        <div className="dq-header-actions">
          {showPrint ? <PrintReportButton disabled={printDisabled} /> : null}
          {actions}
          {onRefresh ? (
            <button
              className="dq-primary-btn dq-no-print"
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
    </>
  );
}
