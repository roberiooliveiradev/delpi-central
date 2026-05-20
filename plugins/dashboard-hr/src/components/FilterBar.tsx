import { HrFilters } from "./HrFilters";
import { HrPageHeader } from "./HrPageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  dateStart: string;
  dateEnd: string;
  branch: string;
  branchOptions: string[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  title = "Dashboard RH",
  subtitle = "Indicadores consolidados do Portal RH",
  dateStart,
  dateEnd,
  branch,
  branchOptions,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
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
        branch={branch}
        branchOptions={branchOptions}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
      />
    </>
  );
}
