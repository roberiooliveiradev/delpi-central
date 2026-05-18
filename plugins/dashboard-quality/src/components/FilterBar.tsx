import { QualityFilters } from "./QualityFilters";
import { QualityPageHeader } from "./QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";
import type { QualityFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  filterState: QualityFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branch: string;
  printDisabled?: boolean;
  branches?: string[];
  branchesLoading?: boolean;
  currentPath?: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  filterState,
  dateStart,
  dateEnd,
  branch,
  branches,
  branchesLoading,
  currentPath,
  printDisabled = false,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onRefresh,
  refreshing = false,
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
      />
      <QualityFilters
        className="dq-no-print"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
      />
    </>
  );
}
