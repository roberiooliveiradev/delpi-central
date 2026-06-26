import { useMemo } from "react";

import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";

type Audit5sFiltersProps = {
  dateStart: string;
  dateEnd: string;
  selectedBranches: string[];
  branchOptions: string[];
  branchesLoading?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
};

export function Audit5sFilters({
  dateStart,
  dateEnd,
  selectedBranches,
  branchOptions,
  branchesLoading = false,
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
    <section className="dq-filters-row" aria-label="Filtros de auditoria 5S">
      <label className="dq-filter-box dq-field">
        <FieldLabel label="Data inicial" hint={QUALITY_HELP_TOOLTIPS.filters.dateStart} />
        <input
          id="a5s-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Data final" hint={QUALITY_HELP_TOOLTIPS.filters.dateEnd} />
        <input
          id="a5s-date-end"
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
