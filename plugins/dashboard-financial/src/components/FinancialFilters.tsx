import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { FINANCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";

type FinancialFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  showPeriodFilters?: boolean;
  className?: string;
};

export function FinancialFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  showPeriodFilters = true,
  className = "",
}: FinancialFiltersProps) {
  return (
    <section
      className={`ds-filters-row ${className}`.trim()}
      aria-label="Filtros do dashboard"
    >
      {showPeriodFilters ? (
        <>
          <label className="ds-filter-box ds-field">
            <FieldLabel
              label="Competência"
              hint={FINANCIAL_HELP_TOOLTIPS.filters.competence}
            />
            <input
              id="ds-competence"
              type="month"
              value={competence}
              onChange={(e) => onCompetenceChange(e.target.value)}
            />
          </label>
          <label className="ds-filter-box ds-field">
            <FieldLabel
              label="Data inicial"
              hint={FINANCIAL_HELP_TOOLTIPS.filters.dateStart}
            />
            <input
              id="ds-date-start"
              type="date"
              value={dateStart}
              onChange={(e) => onDateStartChange(e.target.value)}
            />
          </label>
          <label className="ds-filter-box ds-field">
            <FieldLabel
              label="Data final"
              hint={FINANCIAL_HELP_TOOLTIPS.filters.dateEnd}
            />
            <input
              id="ds-date-end"
              type="date"
              value={dateEnd}
              onChange={(e) => onDateEndChange(e.target.value)}
            />
          </label>
        </>
      ) : null}
      <MultiSelectField
        label="Filial"
        labelHint={FINANCIAL_HELP_TOOLTIPS.filters.branch}
        options={BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Consolidado"
        searchable
      />
    </section>
  );
}
