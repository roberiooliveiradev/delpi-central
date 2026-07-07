import { useMemo } from "react";

import { HR_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { FieldLabel } from "@delpi/plugin-ui";
import { MultiSelectField } from "./MultiSelectField";
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
    <section className="dh-filters-row" aria-label="Filtros do dashboard de RH">
      <label className="dh-filter-box dh-field">
        <FieldLabel
          label="Competência"
          hint={HR_HELP_TOOLTIPS.filters.competence} className="dh-field__label"    />
        <input
          id="hr-filter-competence"
          type="month"
          value={competence}
          onChange={(event) => onCompetenceChange(event.target.value)}
        />
      </label>
      <label className="dh-filter-box dh-field">
        <FieldLabel label="Início" hint={HR_HELP_TOOLTIPS.filters.dateStart} className="dh-field__label" />
        <input
          id="hr-filter-start"
          type="date"
          value={dateStart}
          onChange={(event) => onDateStartChange(event.target.value)}
        />
      </label>
      <label className="dh-filter-box dh-field">
        <FieldLabel label="Fim" hint={HR_HELP_TOOLTIPS.filters.dateEnd} className="dh-field__label" />
        <input
          id="hr-filter-end"
          type="date"
          value={dateEnd}
          onChange={(event) => onDateEndChange(event.target.value)}
        />
      </label>
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
    </section>
  );
}
