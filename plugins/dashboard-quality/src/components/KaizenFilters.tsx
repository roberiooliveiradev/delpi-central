import { useMemo } from "react";

import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type KaizenFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  selectedBranches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  title: string;
  status: string;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onTitleChange: (value: string) => void;
  onStatusChange: (value: string) => void;
};

export function KaizenFilters({
  competence,
  dateStart,
  dateEnd,
  selectedBranches,
  branchOptions,
  branchesLoading = false,
  title,
  status,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onTitleChange,
  onStatusChange,
}: KaizenFiltersProps) {
  const options = useMemo(
    () => buildBranchOptions(branchOptions),
    [branchOptions]
  );

  const selectedValues = useMemo(
    () => sanitizeBranches(selectedBranches, branchOptions),
    [branchOptions, selectedBranches]
  );

  return (
    <FiltersRow
      className="dq-filters-row--extended"
      ariaLabel="Filtros de kaizen"
      variant="extended"
    >
      <FilterInputField
        id="kz-competence"
        label="Competência"
        hint={QUALITY_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id="kz-date-start"
        label="Data inicial"
        hint={QUALITY_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="kz-date-end"
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
      <FilterInputField
        id="kz-title"
        label="Título"
        type="text"
        value={title}
        placeholder="Buscar por título"
        onChange={onTitleChange}
      />
      <FilterInputField
        id="kz-status"
        label="Status"
        type="text"
        value={status}
        placeholder="Filtro de status"
        onChange={onStatusChange}
      />
    </FiltersRow>
  );
}
