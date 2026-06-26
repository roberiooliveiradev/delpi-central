import type { ReactNode } from "react";
import { FINANCIAL_ROUTES } from "../constants/routes";
import type { FinancialFilterUrlState } from "../utils/filterUrl";
import { FinancialFilters } from "./FinancialFilters";
import { FinancialPageHeader } from "./FinancialPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: FinancialFilterUrlState;
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  showPeriodFilters?: boolean;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onRefresh: () => void;
  refreshing?: boolean;
  exportActions?: ReactNode;
};

export function FilterBar({
  title = "Dashboard Financeiro",
  subtitle = "ROL, EBITDA, custos fixos e prazo médio de recebimento",
  currentPath,
  filterState,
  competence,
  dateStart,
  dateEnd,
  branches,
  showPeriodFilters = true,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onRefresh,
  refreshing = false,
  exportActions,
}: FilterBarProps) {
  return (
    <>
      <FinancialPageHeader
        title={title}
        subtitle={subtitle}
        currentPath={currentPath ?? FINANCIAL_ROUTES.home}
        filterState={filterState}
        onRefresh={onRefresh}
        refreshing={refreshing}
        actions={
          exportActions ? (
            <div className="ds-header-action ds-no-print">{exportActions}</div>
          ) : undefined
        }
      />
      <FinancialFilters
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        showPeriodFilters={showPeriodFilters}
        onCompetenceChange={onCompetenceChange}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
      />
    </>
  );
}
