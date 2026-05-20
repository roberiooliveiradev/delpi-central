import { ENGINEERING_ROUTES } from "../constants/routes";
import type { EngineeringFilterUrlState } from "../utils/filterUrl";
import { EngineeringFilters } from "./EngineeringFilters";
import { EngineeringPageHeader } from "./EngineeringPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: EngineeringFilterUrlState;
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
  title = "Dashboard Engenharia",
  subtitle = "TRANSFORMA+ DELPI — ganhos e processos de melhoria",
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
      <EngineeringPageHeader
        title={title}
        subtitle={subtitle}
        currentPath={currentPath ?? ENGINEERING_ROUTES.home}
        filterState={filterState}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <EngineeringFilters
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
