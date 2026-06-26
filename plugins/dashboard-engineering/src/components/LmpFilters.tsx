import {
  LMP_LISTING_TYPE_OPTIONS,
  LMP_STATUS_OPTIONS,
} from "../constants/lmpFilterOptions";
import { ENGINEERING_HELP_TOOLTIPS } from "../content/helpTooltips";
import { MultiSelectField } from "./MultiSelectField";

type LmpFiltersProps = {
  listingTypes: string[];
  statuses: string[];
  onListingTypesChange: (values: string[]) => void;
  onStatusesChange: (values: string[]) => void;
};

export function LmpFilters({
  listingTypes,
  statuses,
  onListingTypesChange,
  onStatusesChange,
}: LmpFiltersProps) {
  return (
    <section
      className="ds-filters-row ds-filters-row--extended"
      aria-label="Filtros de LMP"
    >
      <MultiSelectField
        label="Tipo"
        labelHint={ENGINEERING_HELP_TOOLTIPS.filters.listingType}
        options={LMP_LISTING_TYPE_OPTIONS}
        selectedValues={listingTypes}
        onChange={onListingTypesChange}
        emptyLabel="Todos"
        searchable
      />
      <MultiSelectField
        label="Status"
        labelHint={ENGINEERING_HELP_TOOLTIPS.filters.status}
        options={LMP_STATUS_OPTIONS}
        selectedValues={statuses}
        onChange={onStatusesChange}
        emptyLabel="Todos"
        searchable
      />
    </section>
  );
}
