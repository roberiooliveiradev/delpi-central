import { useMemo } from "react";

import { HR_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type HrFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
};

export function HrFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  branchOptions,
  branchesLoading = false,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
}: HrFiltersProps) {
  const options = useMemo(
    () => buildBranchOptions(branchOptions),
    [branchOptions]
  );

  const selectedValues = useMemo(
    () => sanitizeBranches(branches, branchOptions),
    [branchOptions, branches]
  );

  return (
    <FiltersRow>
      <FilterInputField
        id="hr-filter-competence"
        label="Competência"
        hint={HR_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id="hr-filter-start"
        label="Início"
        hint={HR_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="hr-filter-end"
        label="Fim"
        hint={HR_HELP_TOOLTIPS.filters.dateEnd}
        type="date"
        value={dateEnd}
        onChange={onDateEndChange}
      />
      <MultiSelectField
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={HR_HELP_TOOLTIPS.filters.branch}
        options={options}
        selectedValues={selectedValues}
        onChange={onBranchesChange}
        emptyLabel="Todas"
        searchable
        disabled={branchesLoading}
      />
    </FiltersRow>
  );
}
