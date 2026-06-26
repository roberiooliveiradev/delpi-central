import { ProductionFilters } from "./ProductionFilters";
import { ProductionPageHeader } from "./ProductionPageHeader";
import { PRODUCTION_ROUTES } from "../constants/routes";
import type { ProductionFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState?: ProductionFilterUrlState;
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title,
  subtitle,
  currentPath,
  filterState,
  competence,
  dateStart,
  dateEnd,
  branches,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
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
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        onCompetenceChange={onCompetenceChange}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
      />
    </>
  );
}
