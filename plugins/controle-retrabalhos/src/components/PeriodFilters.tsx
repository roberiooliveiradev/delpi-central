import type { FilterFormState } from "../types/retrabalho";
import { validatePeriodRange } from "../utils/dateRange";
import { FilterBarShell, FilterInputField } from "./filtersUi";

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
  const localError = validatePeriodRange(filters.start_date, filters.end_date);

  return (
    <FilterBarShell>
      <div className="cr-filter-bar__grid cr-filters__grid">
        <FilterInputField
          id="cr-filter-start"
          label="Data inicial"
          type="date"
          value={filters.start_date}
          onChange={(value) => onChange({ start_date: value })}
        />
        <FilterInputField
          id="cr-filter-end"
          label="Data final"
          type="date"
          value={filters.end_date}
          onChange={(value) => onChange({ end_date: value })}
        />
      </div>
      {validationError || localError ? (
        <p className="cr-filters__error" role="alert">
          {validationError ?? localError}
        </p>
      ) : null}
      <div className="cr-filter-bar__actions cr-filters__actions">
        <button
          type="button"
          className="cr-btn cr-btn--primary"
          onClick={onApply}
          disabled={loading || Boolean(localError)}
        >
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
    </FilterBarShell>
  );
}
