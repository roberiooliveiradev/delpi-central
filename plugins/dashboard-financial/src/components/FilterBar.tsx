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
  branches: string[];
  showPeriodFilters?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
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
  branches,
  showPeriodFilters = true,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
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
        branches={branches}
        showPeriodFilters={showPeriodFilters}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
      />
    </>
  );
}
