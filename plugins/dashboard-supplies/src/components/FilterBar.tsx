import { SuppliesFilters } from "./SuppliesFilters";
import { SuppliesPageHeader } from "./SuppliesPageHeader";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  location: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar(props: FilterBarProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    location,
    onDateStartChange,
    onDateEndChange,
    onBranchChange,
    onLocationChange,
    onRefresh,
    refreshing = false,
  } = props;

  return (
    <>
      <SuppliesPageHeader onRefresh={onRefresh} refreshing={refreshing} />
      <SuppliesFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        location={location}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onBranchChange={onBranchChange}
        onLocationChange={onLocationChange}
      />
    </>
  );
}
