import type { ReactNode } from "react";
import { CommercialFilters } from "./CommercialFilters";
import { CommercialPageHeader } from "./CommercialPageHeader";
import type { CommercialFilterUrlState } from "../utils/filterUrl";

type FilterBarProps = {
  filterState: CommercialFilterUrlState;
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  customerSegment: CommercialFilterUrlState["customerSegment"];
  exportActions?: ReactNode;
  onCompetenceChange: (value: string) => void;
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
  competence,
  dateStart,
  dateEnd,
  branches,
  customerSegment,
  exportActions,
  onCompetenceChange,
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
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        customerSegment={customerSegment}
        onCompetenceChange={onCompetenceChange}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchesChange={onBranchesChange}
        onCustomerSegmentChange={onCustomerSegmentChange}
      />
    </>
  );
}
