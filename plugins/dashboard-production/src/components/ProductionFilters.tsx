import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type ProductionFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  className?: string;
};

export function ProductionFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  className = "",
}: ProductionFiltersProps) {
  return (
    <FiltersRow className={className}>
      <FilterInputField
        id="dp-competence"
        label="Competência"
        hint={DP_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id="dp-date-start"
        label="Data inicial"
        hint={DP_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="dp-date-end"
        label="Data final"
        hint={DP_HELP_TOOLTIPS.filters.dateEnd}
        type="date"
        value={dateEnd}
        onChange={onDateEndChange}
      />
      <MultiSelectField
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={DP_HELP_TOOLTIPS.filters.branch}
        options={BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Consolidado (média)"
        searchable
      />
    </FiltersRow>
  );
}
