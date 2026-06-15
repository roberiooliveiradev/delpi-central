import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";

type ProductionFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  className?: string;
};

export function ProductionFilters({
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  className = "",
}: ProductionFiltersProps) {
  return (
    <section className={`dp-filters-row ${className}`.trim()}>
      <label className="dp-filter-box" htmlFor="dp-date-start">
        <FieldLabel label="Data inicial" hint={DP_HELP_TOOLTIPS.filters.dateStart} />
        <input
          id="dp-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </label>
      <label className="dp-filter-box" htmlFor="dp-date-end">
        <FieldLabel label="Data final" hint={DP_HELP_TOOLTIPS.filters.dateEnd} />
        <input
          id="dp-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </label>
      <label className="dp-filter-box" htmlFor="dp-branch">
        <FieldLabel label="Filial" hint={DP_HELP_TOOLTIPS.filters.branch} />
        <select
          id="dp-branch"
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Consolidado (média)</option>
          <option value="01">01 — Matriz</option>
          <option value="02">02 — Filial</option>
        </select>
      </label>
    </section>
  );
}
