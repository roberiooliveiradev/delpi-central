import { IP_HELP } from "../content/helpTooltips";
import {
  resolveQuickRangePreset,
  validatePeriodRange,
  type QuickRangePreset,
} from "../utils/dateRange";
import type { DashboardPeriod } from "../utils/periodQuery";
import { FilterBarShell, FilterInputField, FiltersRow } from "./filtersUi";

type PeriodFiltersProps = {
  period: DashboardPeriod;
  loading?: boolean;
  onChange: (period: DashboardPeriod) => void;
};

const QUICK_RANGE_OPTIONS: Array<{ preset: QuickRangePreset; label: string }> = [
  { preset: "thisMonth", label: "Este mês" },
  { preset: "30d", label: "30 dias" },
  { preset: "6m", label: "6 meses" },
  { preset: "12m", label: "12 meses" },
  { preset: "all", label: "Todo o histórico" },
];

function isPresetActive(period: DashboardPeriod, preset: QuickRangePreset): boolean {
  const resolved = resolveQuickRangePreset(preset);
  if (preset === "all") {
    return period.mode === "all";
  }
  return (
    period.mode === "range" &&
    resolved !== null &&
    period.startDate === resolved.startDate &&
    period.endDate === resolved.endDate
  );
}

export function PeriodFilters({ period, loading = false, onChange }: PeriodFiltersProps) {
  const startDate = period.mode === "range" ? period.startDate : "";
  const endDate = period.mode === "range" ? period.endDate : "";
  const localError =
    period.mode === "range" ? validatePeriodRange(period.startDate, period.endDate) : null;

  return (
    <FilterBarShell ariaLabel="Filtro de período das inspeções">
      <FiltersRow as="div" ariaLabel="Datas do período">
        <FilterInputField
          id="ip-filter-start"
          label="Data inicial"
          hint={IP_HELP.period.startDate}
          type="date"
          value={startDate}
          onChange={(value) =>
            onChange({
              mode: "range",
              startDate: value,
              endDate: endDate || value,
            })
          }
        />
        <FilterInputField
          id="ip-filter-end"
          label="Data final"
          hint={IP_HELP.period.endDate}
          type="date"
          value={endDate}
          onChange={(value) =>
            onChange({
              mode: "range",
              startDate: startDate || value,
              endDate: value,
            })
          }
        />
      </FiltersRow>
      {localError ? (
        <p className="ip-period-error" role="alert">
          {localError}
        </p>
      ) : (
        <p className="ip-auditoria-hint">
          Filtra as medições pela data do ensaio. Atalhos limitam a janela aos últimos 12 meses;
          «Todo o histórico» usa o consolidado da filial.
        </p>
      )}
      <div className="ip-period-presets">
        {QUICK_RANGE_OPTIONS.map(({ preset, label }) => {
          const active = isPresetActive(period, preset);
          return (
            <button
              key={preset}
              type="button"
              className={active ? "ip-button ip-button--primary" : "ip-button"}
              onClick={() => {
                const resolved = resolveQuickRangePreset(preset);
                if (resolved === null) {
                  onChange({ mode: "all" });
                  return;
                }
                onChange({ mode: "range", ...resolved });
              }}
              disabled={loading}
              aria-pressed={active}
            >
              {label}
            </button>
          );
        })}
      </div>
    </FilterBarShell>
  );
}
