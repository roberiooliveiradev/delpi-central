import { BRANCH_OPTIONS } from "../constants/filterOptions";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "@delpi/plugin-ui";
import { MultiSelectField } from "./MultiSelectField";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type SuppliesFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  location: string;
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onLocationChange: (value: string) => void;
  showPeriodFilters?: boolean;
  showLocationFilter?: boolean;
  className?: string;
};

export function SuppliesFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  location,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onLocationChange,
  showPeriodFilters = true,
  showLocationFilter = true,
  className = "",
}: SuppliesFiltersProps) {
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
              hint={SUPPLIES_HELP_TOOLTIPS.filters.competence} className="ds-field__label"      />
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
              hint={SUPPLIES_HELP_TOOLTIPS.filters.dateStart} className="ds-field__label"      />
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
              hint={SUPPLIES_HELP_TOOLTIPS.filters.dateEnd} className="ds-field__label"      />
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
        label={OPERATIONAL_UNIT_FIELD_LABEL}
        labelHint={SUPPLIES_HELP_TOOLTIPS.filters.branch}
        options={BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Consolidado"
        searchable
      />
      {showLocationFilter ? (
        <label className="ds-filter-box ds-field">
          <FieldLabel
            label="Localização (estoque)"
            hint={SUPPLIES_HELP_TOOLTIPS.filters.location} className="ds-field__label"     />
          <input
            id="ds-location"
            type="text"
            value={location}
            placeholder="Todas"
            onChange={(e) => onLocationChange(e.target.value)}
          />
        </label>
      ) : null}
    </section>
  );
}
