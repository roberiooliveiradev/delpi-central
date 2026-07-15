import { segmentToggleBemClasses } from "@delpi/plugin-ui/index";

import type { ChartGranularity } from "../types/chart";
import { CHART_GRANULARITY_OPTIONS } from "../types/chart";

type ChartGranularityToggleProps = {
  value: ChartGranularity;
  onChange: (value: ChartGranularity) => void;
  idPrefix?: string;
};

const SEGMENT = segmentToggleBemClasses("ds");

export function ChartGranularityToggle({
  value,
  onChange,
  idPrefix = "tm-savings",
}: ChartGranularityToggleProps) {
  return (
    <div className={SEGMENT.root} role="group" aria-label="Agrupamento do gráfico">
      {CHART_GRANULARITY_OPTIONS.map((option) => (
        <button
          key={option.value}
          id={`${idPrefix}-granularity-${option.value}`}
          type="button"
          className={value === option.value ? SEGMENT.buttonActive : SEGMENT.button}
          onClick={() => onChange(option.value)}
          aria-pressed={value === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
