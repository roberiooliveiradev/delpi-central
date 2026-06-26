import { COMMERCIAL_BRANCH_OPTIONS } from "../constants/filterOptions";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";
import type { CommercialFilterUrlState } from "../utils/filterUrl";

type CommercialFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  customerSegment: CommercialFilterUrlState["customerSegment"];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onCustomerSegmentChange: (
    value: CommercialFilterUrlState["customerSegment"]
  ) => void;
  className?: string;
};

export function CommercialFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  customerSegment,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onCustomerSegmentChange,
  className = "",
}: CommercialFiltersProps) {
  return (
    <section
      className={`dc-filters-row ${className}`.trim()}
      aria-label="Filtros do dashboard"
    >
      <label className="dc-filter-box dc-field">
        <FieldLabel
          label="Competência"
          hint={COMMERCIAL_HELP_TOOLTIPS.filters.competence}
        />
        <input
          id="dc-competence"
          type="month"
          value={competence}
          onChange={(e) => onCompetenceChange(e.target.value)}
        />
      </label>
      <label className="dc-filter-box dc-field">
        <FieldLabel
          label="Data inicial"
          hint={COMMERCIAL_HELP_TOOLTIPS.filters.dateStart}
        />
        <input
          id="dc-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>
      <label className="dc-filter-box dc-field">
        <FieldLabel
          label="Data final"
          hint={COMMERCIAL_HELP_TOOLTIPS.filters.dateEnd}
        />
        <input
          id="dc-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </label>
      <MultiSelectField
        label="Filial (indicadores)"
        labelHint={COMMERCIAL_HELP_TOOLTIPS.filters.branch}
        options={COMMERCIAL_BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Todas"
        searchable
      />
      <label className="dc-filter-box dc-field">
        <FieldLabel
          label="Clientes"
          hint={COMMERCIAL_HELP_TOOLTIPS.filters.customerSegment}
        />
        <select
          id="dc-customer-segment"
          value={customerSegment}
          onChange={(e) =>
            onCustomerSegmentChange(
              e.target.value as CommercialFilterUrlState["customerSegment"]
            )
          }
        >
          <option value="">Todos</option>
          <option value="weg">WEG</option>
          <option value="new_business">Novos negócios</option>
        </select>
      </label>
    </section>
  );
}
