import type { ReactNode } from "react";
import { ENGINEERING_ROUTES } from "../constants/routes";
import type { EngineeringFilterUrlState } from "../utils/filterUrl";
import { EngineeringFilters } from "./EngineeringFilters";
import { EngineeringPageHeader } from "./EngineeringPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  filterState: EngineeringFilterUrlState;
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
  exportActions?: ReactNode;
};

export function FilterBar({
  title = "Dashboard Engenharia",
  subtitle = "LMPs no prazo e TRANSFORMA+ DELPI — indicadores estratégicos",
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
  exportActions,
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
        actions={
          exportActions ? (
            <div className="ds-header-action ds-no-print">{exportActions}</div>
          ) : undefined
        }
      />
      <EngineeringFilters
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
