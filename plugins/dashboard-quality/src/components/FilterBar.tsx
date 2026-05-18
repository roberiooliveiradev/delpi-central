import { QualityFilters } from "./QualityFilters";
import { QualityPageHeader } from "./QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
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
  dateStart,
  dateEnd,
  branch,
  branches,
  branchesLoading,
  currentPath,
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
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <QualityFilters
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
