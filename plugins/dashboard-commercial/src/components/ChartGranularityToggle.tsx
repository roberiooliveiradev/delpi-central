import type { ChartGranularity } from "../types/chart";
import { CHART_GRANULARITY_OPTIONS } from "../types/chart";

type ChartGranularityToggleProps = {
  value: ChartGranularity;
  onChange: (value: ChartGranularity) => void;
  idPrefix?: string;
};

export function ChartGranularityToggle({
  value,
  onChange,
  idPrefix = "chart",
}: ChartGranularityToggleProps) {
  return (
    <div className="dc-segment-toggle" role="group" aria-label="Agrupamento do gráfico">
      {CHART_GRANULARITY_OPTIONS.map((option) => (
        <button
          key={option.value}
          id={`${idPrefix}-granularity-${option.value}`}
          type="button"
          className={`dc-segment-toggle__btn${
            value === option.value ? " dc-segment-toggle__btn--active" : ""
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
