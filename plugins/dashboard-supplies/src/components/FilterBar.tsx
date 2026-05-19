import { SUPPLIES_ROUTES } from "../constants/routes";
import type { SuppliesFilterUrlState } from "../utils/filterUrl";
import { SuppliesFilters } from "./SuppliesFilters";
import { SuppliesPageHeader } from "./SuppliesPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: SuppliesFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branch: string;
  location: string;
  showPeriodFilters?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title = "Dashboard Suprimentos",
  subtitle = "CPV, OTD de compras, estoque e giro (IDD)",
  currentPath,
  filterState,
  dateStart,
  dateEnd,
  branch,
  location,
  showPeriodFilters = true,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onLocationChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <SuppliesPageHeader
        title={title}
        subtitle={subtitle}
        currentPath={currentPath ?? SUPPLIES_ROUTES.home}
        filterState={filterState}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <SuppliesFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        location={location}
        showPeriodFilters={showPeriodFilters}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
        onLocationChange={onLocationChange}
      />
    </>
  );
}
