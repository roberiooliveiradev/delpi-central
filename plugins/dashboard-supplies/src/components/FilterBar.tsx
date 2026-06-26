import type { ReactNode } from "react";
import { SUPPLIES_ROUTES } from "../constants/routes";
import type { SuppliesFilterUrlState } from "../utils/filterUrl";
import { SuppliesFilters } from "./SuppliesFilters";
import { SuppliesPageHeader } from "./SuppliesPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: SuppliesFilterUrlState;
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  location: string;
  showPeriodFilters?: boolean;
  showLocationFilter?: boolean;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onLocationChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
  exportActions?: ReactNode;
};

export function FilterBar({
  title = "Dashboard Suprimentos",
  subtitle = "CPV, OTD de compras, estoque e giro de estoque",
  currentPath,
  filterState,
  competence,
  dateStart,
  dateEnd,
  branches,
  location,
  showPeriodFilters = true,
  showLocationFilter = true,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onLocationChange,
  onRefresh,
  refreshing = false,
  exportActions,
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
        actions={
          exportActions ? (
            <div className="ds-header-action ds-no-print">{exportActions}</div>
          ) : undefined
        }
      />
      <SuppliesFilters
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        location={location}
        showPeriodFilters={showPeriodFilters}
        showLocationFilter={showLocationFilter}
        onCompetenceChange={onCompetenceChange}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
        onLocationChange={onLocationChange}
      />
    </>
  );
}
