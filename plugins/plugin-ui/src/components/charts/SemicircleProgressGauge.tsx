import { useMemo, type CSSProperties } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type SemicircleProgressGaugeTone =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

export type SemicircleProgressGaugeLegendItem = {
  id: string;
  label: string;
  count: number;
  tone?: SemicircleProgressGaugeTone;
};

export type SemicircleProgressGaugeClassNames = {
  root: string;
  chart: string;
  svg: string;
  track: string;
  fill: string;
  center: string;
  value: string;
  centerLabel: string;
  legend: string;
  legendItem: string;
  legendDot: string;
  legendCount: string;
};

export type SemicircleProgressGaugeProps = {
  /** Current value (for example 100). Clamped to [min, max]. */
  value: number | null | undefined;
  max?: number;
  min?: number;
  /** Suffix next to the center value. Default "%". */
  unit?: string;
  formatValue?: (value: number) => string;
  /** Text under the center value. */
  centerLabel?: string;
  legend?: SemicircleProgressGaugeLegendItem[];
  tone?: SemicircleProgressGaugeTone;
  size?: number;
  className?: string;
  classNames?: Partial<SemicircleProgressGaugeClassNames>;
  /** BEM dual-class prefix. Default `ds`. */
  prefix?: string;
  "aria-label"?: string;
};

export const SEMICIRCLE_GAUGE_TONE_COLORS: Record<SemicircleProgressGaugeTone, string> = {
  success: "#16a34a",
  warning: "#d97706",
  danger: "#dc2626",
  info: "#089bdb",
  neutral: "#64748b",
};

const VIEW_W = 200;
const VIEW_H = 124;
const CX = 100;
const CY = 106;
const R = 80;

export function semicircleProgressGaugeBemClasses(
  prefix: string,
): SemicircleProgressGaugeClassNames {
  const ui = "delpi-ui-semicircle-gauge";
  const base = `${prefix}-semicircle-gauge`;
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    chart: pair(`${base}__chart`, `${ui}__chart`),
    svg: pair(`${base}__svg`, `${ui}__svg`),
    track: pair(`${base}__track`, `${ui}__track`),
    fill: pair(`${base}__fill`, `${ui}__fill`),
    center: pair(`${base}__center`, `${ui}__center`),
    value: pair(`${base}__value`, `${ui}__value`),
    centerLabel: pair(`${base}__center-label`, `${ui}__center-label`),
    legend: pair(`${base}__legend`, `${ui}__legend`),
    legendItem: pair(`${base}__legend-item`, `${ui}__legend-item`),
    legendDot: pair(`${base}__legend-dot`, `${ui}__legend-dot`),
    legendCount: pair(`${base}__legend-count`, `${ui}__legend-count`),
  };
}

function polar(angle: number): { x: number; y: number } {
  return { x: CX + R * Math.cos(angle), y: CY - R * Math.sin(angle) };
}

function describeArc(startAngle: number, endAngle: number): string {
  const start = polar(startAngle);
  const end = polar(endAngle);
  const largeArc = startAngle - endAngle > Math.PI ? 1 : 0;
  return `M ${start.x} ${start.y} A ${R} ${R} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function defaultFormat(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

/**
 * Semicircular donut progress (SVG) with a center value and an optional
 * count legend. The kit owns only presentation: the consumer computes the
 * value and the legend from its own data.
 */
export function SemicircleProgressGauge({
  value,
  max = 100,
  min = 0,
  unit = "%",
  formatValue = defaultFormat,
  centerLabel,
  legend,
  tone = "success",
  size = 220,
  className,
  classNames: classNamesOverride,
  prefix = "ds",
  "aria-label": ariaLabel,
}: SemicircleProgressGaugeProps) {
  const base = useMemo(() => semicircleProgressGaugeBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };
  const numeric = value == null || Number.isNaN(Number(value)) ? null : Number(value);
  const span = max - min || 1;
  const ratio = numeric == null ? 0 : clamp((numeric - min) / span, 0, 1);
  const display = numeric == null ? "—" : formatValue(numeric);
  const fillPath = ratio <= 0 ? "" : describeArc(Math.PI, Math.PI - ratio * Math.PI);
  const accessible =
    ariaLabel ??
    [
      centerLabel,
      numeric == null ? undefined : `${display}${unit}`,
      ...(legend ?? []).map((item) => `${item.label}: ${item.count}`),
    ]
      .filter(Boolean)
      .join(" · ");

  return (
    <div
      className={[withBemModifier(classNames.root, tone), className].filter(Boolean).join(" ")}
      role="img"
      aria-label={accessible || "Progresso"}
      data-tone={tone}
      data-ratio={ratio.toFixed(4)}
    >
      <div className={classNames.chart} style={{ width: size, maxWidth: "100%" }}>
        <svg
          className={classNames.svg}
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          width="100%"
          aria-hidden="true"
        >
          <path
            className={classNames.track}
            d={describeArc(Math.PI, 0)}
            fill="none"
            strokeWidth={20}
            strokeLinecap="round"
          />
          {fillPath ? (
            <path
              className={classNames.fill}
              d={fillPath}
              fill="none"
              stroke={SEMICIRCLE_GAUGE_TONE_COLORS[tone]}
              strokeWidth={20}
              strokeLinecap="round"
            />
          ) : null}
        </svg>
        <div className={classNames.center}>
          <strong className={classNames.value}>
            {display}
            {numeric != null && unit ? <span>{unit}</span> : null}
          </strong>
          {centerLabel ? <span className={classNames.centerLabel}>{centerLabel}</span> : null}
        </div>
      </div>
      {legend?.length ? (
        <ul className={classNames.legend}>
          {legend.map((item) => {
            const itemTone = item.tone ?? "neutral";
            const dotStyle: CSSProperties = {
              background: SEMICIRCLE_GAUGE_TONE_COLORS[itemTone],
            };
            return (
              <li key={item.id} className={classNames.legendItem} data-tone={itemTone}>
                <span className={classNames.legendDot} style={dotStyle} aria-hidden="true" />
                <span className={classNames.legendCount}>{item.count}</span>
                <span>{item.label}</span>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

export function createSemicircleProgressGauge(config: { prefix: string }) {
  return function DashboardSemicircleProgressGauge(
    props: Omit<SemicircleProgressGaugeProps, "prefix">,
  ) {
    return <SemicircleProgressGauge prefix={config.prefix} {...props} />;
  };
}
