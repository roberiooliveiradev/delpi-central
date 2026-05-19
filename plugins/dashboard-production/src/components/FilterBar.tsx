import { ProductionFilters } from "./ProductionFilters";
import { ProductionPageHeader } from "./ProductionPageHeader";

type FilterBarProps = {
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
      <ProductionPageHeader onRefresh={onRefresh} refreshing={refreshing} />
      <ProductionFilters
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
