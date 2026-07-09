import { useMemo } from "react";

import type { NonconformityType } from "../types/nonconformity";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FilterSelectField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type NonconformityFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  selectedBranches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  type: NonconformityType;
  status: string;
  itemCode: string;
  description: string;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onTypeChange: (value: NonconformityType) => void;
  onStatusChange: (value: string) => void;
  onItemCodeChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
};

const TYPE_OPTIONS = [
  { value: "internal", label: "Interna" },
  { value: "external", label: "Externa" },
] as const;

export function NonconformityFilters({
  competence,
  dateStart,
  dateEnd,
  selectedBranches,
  branchOptions,
  branchesLoading = false,
  type,
  status,
  itemCode,
  description,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onTypeChange,
  onStatusChange,
  onItemCodeChange,
  onDescriptionChange,
}: NonconformityFiltersProps) {
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
      ariaLabel="Filtros de NC"
      variant="extended"
    >
      <FilterInputField
        id="nc-competence"
        label="Competência"
        hint={QUALITY_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id="nc-date-start"
        label="Data inicial"
        hint={QUALITY_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="nc-date-end"
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
      <FilterSelectField
        id="nc-type"
        label="Tipo"
        hint={QUALITY_HELP_TOOLTIPS.filters.nonconformityType}
        value={type}
        onChange={(value) => onTypeChange(value as NonconformityType)}
        options={TYPE_OPTIONS}
      />
      <FilterInputField
        id="nc-status"
        label="Status"
        hint={QUALITY_HELP_TOOLTIPS.filters.nonconformityStatus}
        type="text"
        value={status}
        placeholder="Status"
        onChange={onStatusChange}
      />
      <FilterInputField
        id="nc-item"
        label="Item"
        hint={QUALITY_HELP_TOOLTIPS.filters.nonconformityItem}
        type="text"
        value={itemCode}
        placeholder="Código do item"
        onChange={onItemCodeChange}
      />
      <FilterInputField
        id="nc-description"
        label="Descrição"
        hint={QUALITY_HELP_TOOLTIPS.filters.nonconformityDescription}
        type="text"
        value={description}
        placeholder="Buscar na descrição"
        onChange={onDescriptionChange}
      />
    </FiltersRow>
  );
}
