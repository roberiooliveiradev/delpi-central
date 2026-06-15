import { ProductionFilters } from "./ProductionFilters";
import { ProductionPageHeader } from "./ProductionPageHeader";
import { PRODUCTION_ROUTES } from "../constants/routes";
import type { ProductionFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState?: ProductionFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title,
  subtitle,
  currentPath,
  filterState,
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <ProductionPageHeader
        title={title}
        subtitle={subtitle}
        currentPath={currentPath ?? PRODUCTION_ROUTES.home}
        filterState={filterState}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <ProductionFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
      />
    </>
  );
}
