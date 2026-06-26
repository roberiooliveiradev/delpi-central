import { useMemo } from "react";

import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";

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
    <section className="dq-filters-row dq-filters-row--extended" aria-label="Filtros de kaizen">
      <label className="dq-filter-box dq-field">
        <FieldLabel label="Competência" hint={QUALITY_HELP_TOOLTIPS.filters.competence} />
        <input
          id="kz-competence"
          type="month"
          value={competence}
          onChange={(e) => onCompetenceChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Data inicial" hint={QUALITY_HELP_TOOLTIPS.filters.dateStart} />
        <input
          id="kz-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Data final" hint={QUALITY_HELP_TOOLTIPS.filters.dateEnd} />
        <input
          id="kz-date-end"
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

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Título" />
        <input
          id="kz-title"
          type="text"
          value={title}
          placeholder="Buscar por título"
          onChange={(e) => onTitleChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Status" />
        <input
          id="kz-status"
          type="text"
          value={status}
          placeholder="Filtro de status"
          onChange={(e) => onStatusChange(e.target.value)}
        />
      </label>
    </section>
  );
}
