import { HrFilters } from "./HrFilters";
import { HrPageHeader } from "./HrPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title = "Dashboard RH",
  subtitle = "Indicadores consolidados do Portal RH",
  competence,
  dateStart,
  dateEnd,
  branches,
  branchOptions,
  branchesLoading = false,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <HrPageHeader
        title={title}
        subtitle={subtitle}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <HrFilters
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        onCompetenceChange={onCompetenceChange}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
      />
    </>
  );
}
