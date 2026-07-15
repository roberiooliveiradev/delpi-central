import type { FilterFormState } from "../types/scrap";
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
    <section className="sm-filter-bar sm-card">
      <div className="sm-filter-bar__grid">
        <label className="sm-field" htmlFor="sm-filter-start">
          <span className="sm-field__label">Data inicial</span>
          <input
            id="sm-filter-start"
            className="sm-field__input"
            type="date"
            value={filters.dataInicio}
            onChange={(event) => onChange({ dataInicio: event.target.value })}
          />
        </label>
        <label className="sm-field" htmlFor="sm-filter-end">
          <span className="sm-field__label">Data final</span>
          <input
            id="sm-filter-end"
            className="sm-field__input"
            type="date"
            value={filters.dataFim}
            onChange={(event) => onChange({ dataFim: event.target.value })}
          />
        </label>
      </div>
      {validationError || localError ? (
        <p className="sm-filters__error" role="alert">
          {validationError ?? localError}
        </p>
      ) : null}
      <div className="sm-filter-bar__actions">
        <button
          type="button"
          className="sm-btn sm-btn--primary"
          onClick={onApply}
          disabled={loading || Boolean(localError)}
        >
          Aplicar período
        </button>
        <button
          type="button"
          className="sm-btn sm-btn--secondary"
          onClick={() => onQuickRange("thisMonth")}
          disabled={loading}
        >
          Este mês
        </button>
        <button
          type="button"
          className="sm-btn sm-btn--secondary"
          onClick={() => onQuickRange("6m")}
          disabled={loading}
        >
          Últimos 6 meses
        </button>
        <button
          type="button"
          className="sm-btn sm-btn--secondary"
          onClick={() => onQuickRange("12m")}
          disabled={loading}
        >
          Últimos 12 meses
        </button>
      </div>
    </section>
  );
}
