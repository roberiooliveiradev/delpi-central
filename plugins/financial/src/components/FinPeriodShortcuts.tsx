import { copy } from "../content/copy";
import {
  DELINQUENCY_PERIOD_PRESET_IDS,
  detectDelinquencyPeriodPreset,
  resolveDelinquencyPeriodPreset,
  type DelinquencyPeriodPreset,
} from "../utils/delinquencyPeriodPresets";

type FinPeriodShortcutsProps = {
  startDate: string | null;
  endDate: string | null;
  disabled?: boolean;
  onApply: (range: { startDate: string; endDate: string }) => void;
};

const PRESET_LABELS: Record<DelinquencyPeriodPreset, string> = {
  this_month: copy.period.presets.thisMonth,
  this_semester: copy.period.presets.thisSemester,
  this_year: copy.period.presets.thisYear,
};

export function FinPeriodShortcuts({
  startDate,
  endDate,
  disabled = false,
  onApply,
}: FinPeriodShortcutsProps) {
  const activePreset = detectDelinquencyPeriodPreset(startDate, endDate);

  return (
    <div className="fin-period-shortcuts" role="group" aria-label={copy.period.shortcutsAria}>
      {DELINQUENCY_PERIOD_PRESET_IDS.map((preset) => {
        const isActive = activePreset === preset;
        return (
          <button
            key={preset}
            type="button"
            className={`fin-period-shortcuts__btn${isActive ? " fin-period-shortcuts__btn--active" : ""}`}
            disabled={disabled}
            aria-pressed={isActive}
            onClick={() => onApply(resolveDelinquencyPeriodPreset(preset))}
          >
            {PRESET_LABELS[preset]}
          </button>
        );
      })}
    </div>
  );
}
