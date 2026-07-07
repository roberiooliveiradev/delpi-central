import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { ENGINEERING_HELP_TOOLTIPS } from "../content/helpTooltips";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type EngineeringFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  showPeriodFilters?: boolean;
  className?: string;
};

export function EngineeringFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  showPeriodFilters = true,
  className = "",
}: EngineeringFiltersProps) {
  return (
    <FiltersRow className={className}>
      {showPeriodFilters ? (
        <>
          <FilterInputField
            id="ds-competence"
            label="Competência"
            hint={ENGINEERING_HELP_TOOLTIPS.filters.competence}
            type="month"
            value={competence}
            onChange={onCompetenceChange}
          />
          <FilterInputField
            id="ds-date-start"
            label="Data inicial"
            hint={ENGINEERING_HELP_TOOLTIPS.filters.dateStart}
            type="date"
            value={dateStart}
            onChange={onDateStartChange}
          />
          <FilterInputField
            id="ds-date-end"
            label="Data final"
            hint={ENGINEERING_HELP_TOOLTIPS.filters.dateEnd}
            type="date"
            value={dateEnd}
            onChange={onDateEndChange}
          />
        </>
      ) : null}
      <MultiSelectField
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={ENGINEERING_HELP_TOOLTIPS.filters.branch}
        options={BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Consolidado"
        searchable
      />
    </FiltersRow>
  );
}
