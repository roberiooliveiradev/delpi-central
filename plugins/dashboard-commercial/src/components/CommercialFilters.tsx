import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";
import type { CommercialFilterUrlState } from "../utils/filterUrl";

type CommercialFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  customerSegment: CommercialFilterUrlState["customerSegment"];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onCustomerSegmentChange: (
    value: CommercialFilterUrlState["customerSegment"]
  ) => void;
  className?: string;
};

export function CommercialFilters({
  dateStart,
  dateEnd,
  branch,
  customerSegment,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
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
      <label className="dc-filter-box dc-field">
        <FieldLabel
          label="Filial (indicadores)"
          hint={COMMERCIAL_HELP_TOOLTIPS.filters.branch}
        />
        <select
          id="dc-branch"
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Todas</option>
          <option value="01">01 — Filial 01</option>
          <option value="02">02 — Filial 02</option>
        </select>
      </label>
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
