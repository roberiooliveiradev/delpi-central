import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "@delpi/plugin-ui";
import { MultiSelectField } from "./MultiSelectField";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type ProductionFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  className?: string;
};

export function ProductionFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  className = "",
}: ProductionFiltersProps) {
  return (
    <section className={`dp-filters-row ${className}`.trim()} aria-label="Filtros do dashboard">
      <label className="dp-filter-box dp-field" htmlFor="dp-competence">
        <FieldLabel label="Competência" hint={DP_HELP_TOOLTIPS.filters.competence} className="dp-field__label" />
        <input
          id="dp-competence"
          type="month"
          value={competence}
          onChange={(e) => onCompetenceChange(e.target.value)}
        />
      </label>
      <label className="dp-filter-box dp-field" htmlFor="dp-date-start">
        <FieldLabel label="Data inicial" hint={DP_HELP_TOOLTIPS.filters.dateStart} className="dp-field__label" />
        <input
          id="dp-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>
      <label className="dp-filter-box dp-field" htmlFor="dp-date-end">
        <FieldLabel label="Data final" hint={DP_HELP_TOOLTIPS.filters.dateEnd} className="dp-field__label" />
        <input
          id="dp-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </label>
      <MultiSelectField
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={DP_HELP_TOOLTIPS.filters.branch}
        options={BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Consolidado (média)"
        searchable
      />
    </section>
  );
}
