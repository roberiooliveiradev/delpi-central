import { FINANCIAL_ROUTES } from "../constants/routes";
import type { FinancialFilterUrlState } from "../utils/filterUrl";
import { FinancialFilters } from "./FinancialFilters";
import { FinancialPageHeader } from "./FinancialPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: FinancialFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branch: string;
  showPeriodFilters?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title = "Dashboard Financeiro",
  subtitle = "ROL, EBITDA, custos fixos e prazo médio de recebimento",
  currentPath,
  filterState,
  dateStart,
  dateEnd,
  branch,
  showPeriodFilters = true,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onRefresh,
  refreshing = false,
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
      />
      <FinancialFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        showPeriodFilters={showPeriodFilters}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
      />
    </>
  );
}
