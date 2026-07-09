import type { ReactNode } from "react";
import { QualityFilters } from "./QualityFilters";
import { QualityPageHeader } from "./QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";
import type { QualityFilterUrlState } from "../utils/filterUrl";
import type { PpmProductScope } from "../utils/ppmProductScope";

type FilterBarProps = {
  filterState: QualityFilterUrlState;
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  ppmProductScope?: PpmProductScope;
  showPpmProductScope?: boolean;
  printDisabled?: boolean;
  branchOptions?: string[];
  branchesLoading?: boolean;
  currentPath?: string;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onPpmProductScopeChange?: (value: PpmProductScope) => void;
  onRefresh: () => void;
  refreshing?: boolean;
  exportActions?: ReactNode;
};

export function FilterBar({
  filterState,
  competence,
  dateStart,
  dateEnd,
  branches,
  ppmProductScope = "all",
  showPpmProductScope = false,
  branchOptions,
  branchesLoading,
  currentPath,
  printDisabled = false,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onPpmProductScopeChange,
  onRefresh,
  refreshing = false,
  exportActions,
}: FilterBarProps) {
  return (
    <>
      <QualityPageHeader
        title="Dashboard Qualidade"
        subtitle="PPM, kaizens, auditorias 5S e NC (TOTVS)"
        currentPath={currentPath ?? QUALITY_ROUTES.home}
        filterState={filterState}
        printDisabled={printDisabled}
        onRefresh={onRefresh}
        refreshing={refreshing}
        actions={
          exportActions ? (
            <div className="dq-header-action dq-no-print">{exportActions}</div>
          ) : undefined
        }
      />
      <QualityFilters
        className="dq-no-print"
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        ppmProductScope={ppmProductScope}
        showPpmProductScope={showPpmProductScope}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        onCompetenceChange={onCompetenceChange}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
        onPpmProductScopeChange={onPpmProductScopeChange}
      />
    </>
  );
}
