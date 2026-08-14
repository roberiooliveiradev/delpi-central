import type { PersistedChartType } from "../../hooks/usePersistedChartPreferences";
import { SegmentToggle } from "../forms/SegmentToggle";
import {
  CHART_TYPE_LABELS_PT,
  chartTypesForFamily,
  type ChartDataFamily,
} from "./chartDataFamilies";

export type ChartTypeSegmentToggleProps = {
  family: ChartDataFamily;
  value: PersistedChartType;
  onChange: (value: PersistedChartType) => void;
  idPrefix?: string;
  prefix?: string;
  disabled?: boolean;
  categoryCount?: number;
  ariaLabel?: string;
  className?: string;
};

/**
 * Compact chart-type switcher filtered by data family.
 */
export function ChartTypeSegmentToggle({
  family,
  value,
  onChange,
  idPrefix = "chart-type",
  prefix = "ds",
  disabled = false,
  categoryCount,
  ariaLabel = "Tipo de gráfico",
  className,
}: ChartTypeSegmentToggleProps) {
  const types = chartTypesForFamily(family, { categoryCount });
  if (types.length <= 1) return null;

  return (
    <SegmentToggle
      ariaLabel={ariaLabel}
      idPrefix={idPrefix}
      prefix={prefix}
      size="sm"
      disabled={disabled}
      className={className}
      value={value}
      onChange={onChange}
      options={types.map((type) => ({
        value: type,
        label: CHART_TYPE_LABELS_PT[type],
      }))}
    />
  );
}
