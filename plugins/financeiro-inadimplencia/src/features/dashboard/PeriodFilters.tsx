import type { PeriodFormState, PeriodPreset } from "../../types/inadimplencia";
import { resolvePeriodPreset, validatePeriodRange } from "../../utils/period";

type PeriodFiltersProps = {
  value: PeriodFormState;
  disabled?: boolean;
  validationError?: string | null;
  onChange: (next: PeriodFormState) => void;
  onApplyCustom: () => void;
};

const PRESETS: Array<{ value: PeriodPreset; label: string }> = [
  { value: "last_6_months", label: "Últimos 6 meses" },
  { value: "last_12_months", label: "Últimos 12 meses" },
  { value: "current_year", label: "Ano atual" },
  { value: "previous_year", label: "Ano anterior" },
  { value: "custom", label: "Personalizado" },
];

export function PeriodFilters({
  value,
  disabled = false,
  validationError = null,
  onChange,
  onApplyCustom,
}: PeriodFiltersProps) {
  const handlePreset = (preset: PeriodPreset) => {
    if (preset === "custom") {
      onChange({ ...value, preset: "custom" });
      return;
    }
    const range = resolvePeriodPreset(preset);
    onChange({
      preset,
      startDate: range.startDate,
      endDate: range.endDate,
    });
  };

  return (
    <section className="fi-filters" aria-label="Filtros de período">
      <div className="fi-filters__presets" role="group" aria-label="Períodos rápidos">
        {PRESETS.map((preset) => (
          <button
            key={preset.value}
            type="button"
            className={`fi-chip${value.preset === preset.value ? " fi-chip--active" : ""}`}
            onClick={() => handlePreset(preset.value)}
            disabled={disabled}
            aria-pressed={value.preset === preset.value}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {value.preset === "custom" ? (
        <div className="fi-filters__custom">
          <label className="fi-field">
            <span>Data inicial</span>
            <input
              type="date"
              value={value.startDate}
              disabled={disabled}
              onChange={(event) =>
                onChange({ ...value, startDate: event.target.value, preset: "custom" })
              }
            />
          </label>
          <label className="fi-field">
            <span>Data final (exclusiva)</span>
            <input
              type="date"
              value={value.endDate}
              disabled={disabled}
              onChange={(event) =>
                onChange({ ...value, endDate: event.target.value, preset: "custom" })
              }
            />
          </label>
          <button
            type="button"
            className="fi-btn fi-btn--primary"
            disabled={disabled || Boolean(validatePeriodRange(value.startDate, value.endDate))}
            onClick={onApplyCustom}
          >
            Aplicar período
          </button>
        </div>
      ) : null}

      {validationError ? (
        <p className="fi-filters__error" role="alert">
          {validationError}
        </p>
      ) : (
        <p className="fi-filters__hint">
          Períodos padrão incluem o mês corrente (ainda incompleto). O limite final
          é exclusivo.
        </p>
      )}
    </section>
  );
}
