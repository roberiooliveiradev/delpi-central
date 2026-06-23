import type { ReactNode } from "react";
import { CommercialFilters } from "./CommercialFilters";
import { CommercialPageHeader } from "./CommercialPageHeader";
import type { CommercialFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  filterState: CommercialFilterUrlState;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  customerSegment: CommercialFilterUrlState["customerSegment"];
  exportActions?: ReactNode;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
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
  branches,
  customerSegment,
  exportActions,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onCustomerSegmentChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <CommercialPageHeader
        filterState={filterState}
        exportActions={exportActions}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />
      <CommercialFilters
        className="dc-no-print"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        customerSegment={customerSegment}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
        onCustomerSegmentChange={onCustomerSegmentChange}
      />
    </>
  );
}
