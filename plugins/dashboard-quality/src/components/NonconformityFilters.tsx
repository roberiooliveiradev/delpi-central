import { useMemo } from "react";

import type { NonconformityType } from "../types/nonconformity";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildBranchOptions,
  sanitizeBranches,
} from "../utils/branchClientFilters";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";
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
    <section className="dq-filters-row dq-filters-row--extended" aria-label="Filtros de NC">
      <label className="dq-filter-box dq-field">
        <FieldLabel label="Competência" hint={QUALITY_HELP_TOOLTIPS.filters.competence} />
        <input
          id="nc-competence"
          type="month"
          value={competence}
          onChange={(e) => onCompetenceChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Data inicial" hint={QUALITY_HELP_TOOLTIPS.filters.dateStart} />
        <input
          id="nc-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Data final" hint={QUALITY_HELP_TOOLTIPS.filters.dateEnd} />
        <input
          id="nc-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </label>

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

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Tipo" />
        <select
          id="nc-type"
          value={type}
          onChange={(e) => onTypeChange(e.target.value as NonconformityType)}
        >
          <option value="internal">Interna</option>
          <option value="external">Externa</option>
        </select>
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Status" />
        <input
          id="nc-status"
          type="text"
          value={status}
          placeholder="Status"
          onChange={(e) => onStatusChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field">
        <FieldLabel label="Item" />
        <input
          id="nc-item"
          type="text"
          value={itemCode}
          placeholder="Código do item"
          onChange={(e) => onItemCodeChange(e.target.value)}
        />
      </label>

      <label className="dq-filter-box dq-field dq-filter-box--wide">
        <FieldLabel label="Descrição" />
        <input
          id="nc-description"
          type="text"
          value={description}
          placeholder="Buscar na descrição"
          onChange={(e) => onDescriptionChange(e.target.value)}
        />
      </label>
    </section>
  );
}
