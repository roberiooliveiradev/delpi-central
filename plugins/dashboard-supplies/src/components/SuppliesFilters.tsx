import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type SuppliesFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  location: string;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onLocationChange: (value: string) => void;
  showPeriodFilters?: boolean;
  showLocationFilter?: boolean;
  className?: string;
};

export function SuppliesFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  location,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onLocationChange,
  showPeriodFilters = true,
  showLocationFilter = true,
  className = "",
}: SuppliesFiltersProps) {
  return (
    <FiltersRow className={className}>
      {showPeriodFilters ? (
        <>
          <FilterInputField
            id="ds-competence"
            label="Competência"
            hint={SUPPLIES_HELP_TOOLTIPS.filters.competence}
            type="month"
            value={competence}
            onChange={onCompetenceChange}
          />
          <FilterInputField
            id="ds-date-start"
            label="Data inicial"
            hint={SUPPLIES_HELP_TOOLTIPS.filters.dateStart}
            type="date"
            value={dateStart}
            onChange={onDateStartChange}
          />
          <FilterInputField
            id="ds-date-end"
            label="Data final"
            hint={SUPPLIES_HELP_TOOLTIPS.filters.dateEnd}
            type="date"
            value={dateEnd}
            onChange={onDateEndChange}
          />
        </>
      ) : null}
      <MultiSelectField
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={SUPPLIES_HELP_TOOLTIPS.filters.branch}
        options={BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Consolidado"
        searchable
      />
      {showLocationFilter ? (
        <FilterInputField
          id="ds-location"
          label="Localização (estoque)"
          hint={SUPPLIES_HELP_TOOLTIPS.filters.location}
          type="text"
          value={location}
          placeholder="Todas"
          onChange={onLocationChange}
        />
      ) : null}
    </FiltersRow>
  );
}
