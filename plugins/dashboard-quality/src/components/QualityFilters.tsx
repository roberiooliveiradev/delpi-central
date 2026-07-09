import { useMemo } from "react";

import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FilterSelectField, FiltersRow } from "./dashboardFiltersUi";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";
import {
  PPM_PRODUCT_SCOPE_OPTIONS,
  type PpmProductScope,
} from "../utils/ppmProductScope";

type QualityFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  ppmProductScope?: PpmProductScope;
  showPpmProductScope?: boolean;
  branchOptions?: string[];
  branchesLoading?: boolean;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onPpmProductScopeChange?: (value: PpmProductScope) => void;
  idPrefix?: string;
  className?: string;
};

export function QualityFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  ppmProductScope = "all",
  showPpmProductScope = false,
  branchOptions = [],
  branchesLoading = false,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onPpmProductScopeChange,
  idPrefix = "dq",
  className,
}: QualityFiltersProps) {
  const options = useMemo(
    () => buildBranchOptions(branchOptions),
    [branchOptions]
  );

  const selectedValues = useMemo(
    () => sanitizeBranches(branches, branchOptions),
    [branchOptions, branches]
  );

  return (
    <FiltersRow className={className}>
      <FilterInputField
        id={`${idPrefix}-competence`}
        label="Competência"
        hint={QUALITY_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id={`${idPrefix}-date-start`}
        label="Data inicial"
        hint={QUALITY_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id={`${idPrefix}-date-end`}
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
      {showPpmProductScope ? (
        <FilterSelectField
          id={`${idPrefix}-ppm-product`}
          label="Produto (PPM)"
          hint={QUALITY_HELP_TOOLTIPS.filters.ppmProductScope}
          value={ppmProductScope}
          onChange={(value) => onPpmProductScopeChange?.(value as PpmProductScope)}
          options={PPM_PRODUCT_SCOPE_OPTIONS.map((option) => ({
            value: option.value,
            label: option.label,
          }))}
        />
      ) : null}
    </FiltersRow>
  );
}
