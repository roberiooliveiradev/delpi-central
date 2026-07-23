import { useMemo } from "react";

import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type Audit5sFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  selectedBranches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
};

export function Audit5sFilters({
  competence,
  dateStart,
  dateEnd,
  selectedBranches,
  branchOptions,
  branchesLoading = false,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
}: Audit5sFiltersProps) {
  const options = useMemo(
    () => buildBranchOptions(branchOptions),
    [branchOptions]
  );

  const selectedValues = useMemo(
    () => sanitizeBranches(selectedBranches, branchOptions),
    [branchOptions, selectedBranches]
  );

  return (
    <FiltersRow ariaLabel="Filtros de auditoria 5S">
      <FilterInputField
        id="a5s-competence"
        label="Competência"
        hint={QUALITY_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id="a5s-date-start"
        label="Data inicial"
        hint={QUALITY_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="a5s-date-end"
        label="Data final"
        hint={QUALITY_HELP_TOOLTIPS.filters.dateEnd}
        type="date"
        value={dateEnd}
        onChange={onDateEndChange}
      />
      <MultiSelectField
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={QUALITY_HELP_TOOLTIPS.filters.branch}
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
