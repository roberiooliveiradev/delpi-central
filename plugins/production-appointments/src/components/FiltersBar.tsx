import type { FilterFormState, WorkCenterItem } from "../types/appointments";
import { validatePeriodRange } from "../utils/dateRange";

export type QuickRangePreset = "30d" | "6m" | "thisMonth";

type FiltersBarProps = {
  filters: FilterFormState;
  workCenters: WorkCenterItem[];
  validationError: string | null;
  loading?: boolean;
  onChange: (patch: Partial<FilterFormState>) => void;
  onApply: () => void;
  onQuickRange: (preset: QuickRangePreset) => void;
};

export function FiltersBar({
  filters,
  workCenters,
  validationError,
  loading = false,
  onChange,
  onApply,
  onQuickRange,
}: FiltersBarProps) {
  const localError = validatePeriodRange(filters.dateStart, filters.dateEnd);

  return (
    <section className="pa-filter-bar pa-card">
      <div className="pa-filter-bar__grid">
        <label className="pa-field" htmlFor="pa-filter-start">
          <span className="pa-field__label">Data inicial</span>
          <input
            id="pa-filter-start"
            className="pa-field__input"
            type="date"
            value={filters.dateStart}
            onChange={(event) => onChange({ dateStart: event.target.value })}
          />
        </label>
        <label className="pa-field" htmlFor="pa-filter-end">
          <span className="pa-field__label">Data final</span>
          <input
            id="pa-filter-end"
            className="pa-field__input"
            type="date"
            value={filters.dateEnd}
            onChange={(event) => onChange({ dateEnd: event.target.value })}
          />
        </label>
        <label className="pa-field" htmlFor="pa-filter-ct">
          <span className="pa-field__label">Centro de trabalho</span>
          <select
            id="pa-filter-ct"
            className="pa-field__input"
            value={filters.workCenter}
            onChange={(event) => onChange({ workCenter: event.target.value })}
          >
            <option value="">Todos</option>
            {workCenters.map((ct) => (
              <option key={ct.work_center} value={ct.work_center}>
                {ct.work_center} — {ct.name}
                {ct.is_final_inspection === 1 || ct.is_final_inspection === true
                  ? " (inspeção final)"
                  : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="pa-field" htmlFor="pa-filter-op">
          <span className="pa-field__label">OP</span>
          <input
            id="pa-filter-op"
            className="pa-field__input"
            value={filters.op}
            onChange={(event) => onChange({ op: event.target.value })}
            placeholder="Opcional"
          />
        </label>
        <label className="pa-field" htmlFor="pa-filter-product">
          <span className="pa-field__label">Produto</span>
          <input
            id="pa-filter-product"
            className="pa-field__input"
            value={filters.product}
            onChange={(event) => onChange({ product: event.target.value })}
            placeholder="Opcional"
          />
        </label>
      </div>
      {validationError || localError ? (
        <p className="pa-filters__error" role="alert">
          {validationError ?? localError}
        </p>
      ) : null}
      <div className="pa-filter-bar__actions">
        <button
          type="button"
          className="pa-btn pa-btn--primary"
          onClick={onApply}
          disabled={loading || Boolean(localError)}
        >
          Aplicar
        </button>
        <button
          type="button"
          className="pa-btn pa-btn--secondary"
          onClick={() => onQuickRange("thisMonth")}
          disabled={loading}
        >
          Este mês
        </button>
        <button
          type="button"
          className="pa-btn pa-btn--secondary"
          onClick={() => onQuickRange("30d")}
          disabled={loading}
        >
          30 dias
        </button>
        <button
          type="button"
          className="pa-btn pa-btn--secondary"
          onClick={() => onQuickRange("6m")}
          disabled={loading}
        >
          6 meses
        </button>
      </div>
    </section>
  );
}
