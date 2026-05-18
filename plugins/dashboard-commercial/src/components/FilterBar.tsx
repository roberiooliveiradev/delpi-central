import { CommercialFilters } from "./CommercialFilters";
import { CommercialPageHeader } from "./CommercialPageHeader";
import type { CommercialFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  filterState: CommercialFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branch: string;
  printDisabled?: boolean;
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
  printDisabled = false,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <CommercialPageHeader
        filterState={filterState}
        printDisabled={printDisabled}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <CommercialFilters
        className="dc-no-print"
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
