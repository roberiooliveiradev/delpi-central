import type { ReactNode } from "react";
import { CommercialFilters } from "./CommercialFilters";
import { CommercialPageHeader } from "./CommercialPageHeader";
import type { CommercialFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  filterState: CommercialFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branch: string;
  customerSegment: CommercialFilterUrlState["customerSegment"];
  printDisabled?: boolean;
  exportActions?: ReactNode;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onCustomerSegmentChange: (
    value: CommercialFilterUrlState["customerSegment"]
  ) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  filterState,
  dateStart,
  dateEnd,
  branch,
  customerSegment,
  printDisabled = false,
  exportActions,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onCustomerSegmentChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <CommercialPageHeader
        filterState={filterState}
        printDisabled={printDisabled}
        exportActions={exportActions}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <CommercialFilters
        className="dc-no-print"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        customerSegment={customerSegment}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
        onCustomerSegmentChange={onCustomerSegmentChange}
      />
    </>
  );
}
