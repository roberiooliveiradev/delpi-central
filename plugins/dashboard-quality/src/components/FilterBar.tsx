import { QualityFilters } from "./QualityFilters";
import { QualityPageHeader } from "./QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";
import type { QualityFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  filterState: QualityFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  printDisabled?: boolean;
  branchOptions?: string[];
  branchesLoading?: boolean;
  currentPath?: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  filterState,
  dateStart,
  dateEnd,
  branches,
  branchOptions,
  branchesLoading,
  currentPath,
  printDisabled = false,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
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
        branches={branches}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
      />
    </>
  );
}
