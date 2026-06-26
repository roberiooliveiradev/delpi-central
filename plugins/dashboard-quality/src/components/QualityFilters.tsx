import { useMemo } from "react";

import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";

type QualityFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branches: string[];
  branchOptions?: string[];
  branchesLoading?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  idPrefix?: string;
  className?: string;
};

export function QualityFilters({
  dateStart,
  dateEnd,
  branches,
  branchOptions = [],
  branchesLoading = false,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
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
    <section
      className={["dq-filters-row", className].filter(Boolean).join(" ")}
      aria-label="Filtros do dashboard"
    >
      <label className="dq-filter-box dq-field">
        <FieldLabel
          label="Data inicial"
          hint={QUALITY_HELP_TOOLTIPS.filters.dateStart}
        />
        <input
          id={`${idPrefix}-date-start`}
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel
          label="Data final"
          hint={QUALITY_HELP_TOOLTIPS.filters.dateEnd}
        />
        <input
          id={`${idPrefix}-date-end`}
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </label>

      <MultiSelectField
        label="Filial"
        labelHint={QUALITY_HELP_TOOLTIPS.filters.branch}
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
