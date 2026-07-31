import {
  ActionButton,
  SegmentToggle,
} from "@delpi/plugin-ui/index";

import type { PeriodFormState, PeriodPreset } from "../../types/inadimplencia";
import { resolvePeriodPreset, validatePeriodRange } from "../../utils/period";
import { FilterBarShell, FiTextField } from "../../components/fiFormFields";

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
    <>
      <FilterBarShell
        leading={
          <SegmentToggle
            prefix="fi"
            idPrefix="fi-period"
            ariaLabel="Períodos rápidos"
            options={PRESETS}
            value={value.preset}
            onChange={handlePreset}
            disabled={disabled}
          />
        }
      >
        {value.preset === "custom" ? (
          <>
            <FiTextField
              id="fi-period-start"
              label="Data inicial"
              type="date"
              value={value.startDate}
              disabled={disabled}
              onChange={(startDate) =>
                onChange({ ...value, startDate, preset: "custom" })
              }
            />
            <FiTextField
              id="fi-period-end"
              label="Data final (exclusiva)"
              type="date"
              value={value.endDate}
              disabled={disabled}
              onChange={(endDate) =>
                onChange({ ...value, endDate, preset: "custom" })
              }
            />
            <ActionButton
              variant="primary"
              disabled={
                disabled || Boolean(validatePeriodRange(value.startDate, value.endDate))
              }
              onClick={onApplyCustom}
            >
              Aplicar período
            </ActionButton>
          </>
        ) : null}
      </FilterBarShell>

      {validationError ? (
        <p className="fi-filters__error" role="alert">
          {validationError}
        </p>
      ) : null}
    </>
  );
}
