import { HrFilters } from "./HrFilters";
import { HrPageHeader } from "./HrPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title = "Dashboard RH",
  subtitle = "Indicadores consolidados do Portal RH",
  dateStart,
  dateEnd,
  branches,
  branchOptions,
  branchesLoading = false,
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
