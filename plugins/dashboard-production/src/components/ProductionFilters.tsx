import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";

type ProductionFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branches: string[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  className?: string;
};

export function ProductionFilters({
  dateStart,
  dateEnd,
  branches,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  className = "",
}: ProductionFiltersProps) {
  return (
    <section className={`dp-filters-row ${className}`.trim()} aria-label="Filtros do dashboard">
      <label className="dp-filter-box dp-field" htmlFor="dp-date-start">
        <FieldLabel label="Data inicial" hint={DP_HELP_TOOLTIPS.filters.dateStart} />
        <input
          id="dp-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>
      <label className="dp-filter-box dp-field" htmlFor="dp-date-end">
        <FieldLabel label="Data final" hint={DP_HELP_TOOLTIPS.filters.dateEnd} />
        <input
          id="dp-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </label>
      <MultiSelectField
        label="Filial"
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
