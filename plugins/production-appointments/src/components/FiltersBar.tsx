import type { FilterFormState, WorkCenterItem } from "../types/appointments";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import { validatePeriodRange } from "../utils/dateRange";
import { FilterBarShell, FilterInputField, FilterSelectField } from "./filtersUi";

export type QuickRangePreset = "30d" | "6m" | "thisMonth";

type FiltersBarProps = {
  filters: FilterFormState;
  workCenters: WorkCenterItem[];
  validationError: string | null;
  loading?: boolean;
  onChange: (patch: Partial<FilterFormState>) => void;
  onQuickRange: (preset: QuickRangePreset) => void;
};

function isInspection(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

export function FiltersBar({
  filters,
  workCenters,
  validationError,
  loading = false,
  onChange,
  onQuickRange,
}: FiltersBarProps) {
  const localError = validatePeriodRange(filters.dateStart, filters.dateEnd);

  const workCenterOptions = workCenters.map((ct) => ({
    value: ct.work_center,
    label: `${ct.work_center} — ${ct.name}${
      isInspection(ct.is_final_inspection) ? " (inspeção final)" : ""
    }`,
  }));

  return (
    <FilterBarShell>
      <div className="pa-filter-bar__grid pa-filters__grid">
        <FilterInputField
          id="pa-filter-start"
          label="Data inicial"
          hint={PA_HELP_TOOLTIPS.filters.dateStart}
          type="date"
          value={filters.dateStart}
          onChange={(value) => onChange({ dateStart: value })}
        />
        <FilterInputField
          id="pa-filter-end"
          label="Data final"
          hint={PA_HELP_TOOLTIPS.filters.dateEnd}
          type="date"
          value={filters.dateEnd}
          onChange={(value) => onChange({ dateEnd: value })}
        />
        <FilterSelectField
          id="pa-filter-ct"
          label="Centro de trabalho"
          hint={PA_HELP_TOOLTIPS.filters.workCenter}
          value={filters.workCenter}
          onChange={(value) => onChange({ workCenter: value })}
          options={workCenterOptions}
          placeholderOption="Todos"
          searchable
        />
        <FilterInputField
          id="pa-filter-op"
          label="OP"
          hint={PA_HELP_TOOLTIPS.filters.op}
          type="text"
          value={filters.op}
          onChange={(value) => onChange({ op: value })}
          placeholder="Opcional"
        />
        <FilterInputField
          id="pa-filter-product"
          label="Produto"
          hint={PA_HELP_TOOLTIPS.filters.product}
          type="text"
          value={filters.product}
          onChange={(value) => onChange({ product: value })}
          placeholder="Opcional"
        />
      </div>
      {validationError || localError ? (
        <p className="pa-filters__error" role="alert">
          {validationError ?? localError}
        </p>
      ) : null}
      <div className="pa-filter-bar__actions pa-filters__actions">
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
    </FilterBarShell>
  );
}
