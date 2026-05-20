import type { ChartGranularity } from "../types/chart";
import { CHART_GRANULARITY_OPTIONS } from "../types/chart";

type ChartGranularityToggleProps = {
  value: ChartGranularity;
  onChange: (value: ChartGranularity) => void;
  idPrefix?: string;
  modes?: ChartGranularity[];
};

export function ChartGranularityToggle({
  value,
  onChange,
  idPrefix = "chart",
  modes,
}: ChartGranularityToggleProps) {
  const options = modes
    ? CHART_GRANULARITY_OPTIONS.filter((option) => modes.includes(option.value))
    : CHART_GRANULARITY_OPTIONS;

  return (
    <div className="lmps-segment-toggle" role="group" aria-label="Agrupamento do gráfico">
      {options.map((option) => (
        <button
          key={option.value}
          id={`${idPrefix}-granularity-${option.value}`}
          type="button"
          className={`lmps-segment-toggle__btn${
            value === option.value ? " lmps-segment-toggle__btn--active" : ""
          }`}
          onClick={() => onChange(option.value)}
          aria-pressed={value === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
