import type { FilterFormState } from "../types/retrabalho";
import { validatePeriodRange } from "../utils/dateRange";

export type QuickRangePreset = "12m" | "6m" | "thisMonth";

type PeriodFiltersProps = {
  filters: FilterFormState;
  validationError: string | null;
  loading?: boolean;
  onChange: (patch: Partial<FilterFormState>) => void;
  onApply: () => void;
  onQuickRange: (preset: QuickRangePreset) => void;
};

export function PeriodFilters({
  filters,
  validationError,
  loading = false,
  onChange,
  onApply,
  onQuickRange,
}: PeriodFiltersProps) {
  const localError = validatePeriodRange(filters.dataInicio, filters.dataFim);

  return (
    <section className="cr-card cr-filters">
      <div className="cr-filters__grid">
        <label className="cr-field">
          <span>Data inicial</span>
          <input
            type="date"
            value={filters.dataInicio}
            onChange={(event) => onChange({ dataInicio: event.target.value })}
          />
        </label>
        <label className="cr-field">
          <span>Data final</span>
          <input
            type="date"
            value={filters.dataFim}
            onChange={(event) => onChange({ dataFim: event.target.value })}
          />
        </label>
      </div>
      {validationError || localError ? (
        <p className="cr-filters__error" role="alert">{validationError ?? localError}</p>
      ) : null}
      <div className="cr-filters__actions">
        <button type="button" className="cr-btn cr-btn--primary" onClick={onApply} disabled={loading || Boolean(localError)}>
          Aplicar período
        </button>
        <button
          type="button"
          className="cr-btn cr-btn--secondary"
          onClick={() => onQuickRange("12m")}
          disabled={loading}
        >
          Últimos 12 meses
        </button>
        <button
          type="button"
          className="cr-btn cr-btn--secondary"
          onClick={() => onQuickRange("6m")}
          disabled={loading}
        >
          Últimos 6 meses
        </button>
        <button
          type="button"
          className="cr-btn cr-btn--secondary"
          onClick={() => onQuickRange("thisMonth")}
          disabled={loading}
        >
          Este mês
        </button>
      </div>
    </section>
  );
}
