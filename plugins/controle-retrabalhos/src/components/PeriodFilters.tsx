import type { FilterFormState } from "../types/retrabalho";
import { type QuickRangePreset, validatePeriodRange } from "../utils/dateRange";
import { FilterBarShell, FilterInputField } from "./filtersUi";

export type { QuickRangePreset };

type PeriodFiltersProps = {
  filters: FilterFormState;
  validationError: string | null;
  loading?: boolean;
  onChange: (patch: Partial<FilterFormState>) => void;
  onQuickRange: (preset: QuickRangePreset) => void;
};

const QUICK_RANGE_OPTIONS: Array<{ preset: QuickRangePreset; label: string }> = [
  { preset: "today", label: "Hoje" },
  { preset: "thisWeek", label: "Esta semana" },
  { preset: "thisMonth", label: "Este mês" },
  { preset: "30d", label: "30 dias" },
  { preset: "6m", label: "6 meses" },
  { preset: "12m", label: "Últimos 12 meses" },
];

export function PeriodFilters({
  filters,
  validationError,
  loading = false,
  onChange,
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
        {QUICK_RANGE_OPTIONS.map(({ preset, label }) => (
          <button
            key={preset}
            type="button"
            className="cr-btn cr-btn--secondary"
            onClick={() => onQuickRange(preset)}
            disabled={loading}
          >
            {label}
          </button>
        ))}
      </div>
    </FilterBarShell>
  );
}
