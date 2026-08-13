import { useId, useMemo } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type SpeedometerGaugeTone = "neutral" | "success" | "warning" | "danger";

export type SpeedometerGaugeClassNames = {
  root: string;
  svg: string;
  track: string;
  fill: string;
  needle: string;
  hub: string;
  value: string;
  label: string;
  unit: string;
};

export type SpeedometerGaugeProps = {
  /** Valor atual (ex.: 98.8). */
  value: number | null | undefined;
  /** Máximo da escala. Default 100. */
  max?: number;
  /** Mínimo da escala. Default 0. */
  min?: number;
  label?: string;
  /** Sufixo exibido junto ao valor (ex.: "%"). Default "%". */
  unit?: string;
  /** Formata o número central. */
  formatValue?: (value: number) => string;
  tone?: SpeedometerGaugeTone;
  /**
   * Se omitido, deriva tom por faixas de % do máximo:
   * &lt; 90 danger · &lt; 95 warning · demais success.
   */
  autoTone?: boolean;
  size?: number;
  className?: string;
  classNames?: Partial<SpeedometerGaugeClassNames>;
  /** Prefixo BEM dual-class. Default `ds`. */
  prefix?: string;
  "aria-label"?: string;
};

const VIEW = 120;
const CX = 60;
const CY = 70;
const R = 48;
const START_ANGLE = Math.PI; // 180°
const END_ANGLE = 0; // 0°
const SWEEP = START_ANGLE - END_ANGLE;

export function speedometerGaugeBemClasses(prefix: string): SpeedometerGaugeClassNames {
  const ui = "delpi-ui-speedometer-gauge";
  return {
    root: delpiUiClass(`${prefix}-speedometer-gauge`, ui),
    svg: delpiUiClass(`${prefix}-speedometer-gauge__svg`, `${ui}__svg`),
    track: delpiUiClass(`${prefix}-speedometer-gauge__track`, `${ui}__track`),
    fill: delpiUiClass(`${prefix}-speedometer-gauge__fill`, `${ui}__fill`),
    needle: delpiUiClass(`${prefix}-speedometer-gauge__needle`, `${ui}__needle`),
    hub: delpiUiClass(`${prefix}-speedometer-gauge__hub`, `${ui}__hub`),
    value: delpiUiClass(`${prefix}-speedometer-gauge__value`, `${ui}__value`),
    label: delpiUiClass(`${prefix}-speedometer-gauge__label`, `${ui}__label`),
    unit: delpiUiClass(`${prefix}-speedometer-gauge__unit`, `${ui}__unit`),
  };
}

function polar(cx: number, cy: number, r: number, angle: number): { x: number; y: number } {
  return { x: cx + r * Math.cos(angle), y: cy - r * Math.sin(angle) };
}

function describeArc(
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number,
): string {
  const start = polar(cx, cy, r, startAngle);
  const end = polar(cx, cy, r, endAngle);
  const largeArc = startAngle - endAngle > Math.PI ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function resolveTone(
  ratio: number,
  tone: SpeedometerGaugeTone | undefined,
  autoTone: boolean,
): SpeedometerGaugeTone {
  if (tone) return tone;
  if (!autoTone) return "neutral";
  if (ratio < 0.9) return "danger";
  if (ratio < 0.95) return "warning";
  return "success";
}

function defaultFormat(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

/**
 * Velocímetro semicircular (0–max) para KPIs percentuais — SVG puro, tokens do kit.
 */
export function SpeedometerGauge({
  value,
  max = 100,
  min = 0,
  label,
  unit = "%",
  formatValue = defaultFormat,
  tone,
  autoTone = true,
  size = 168,
  className,
  classNames: classNamesOverride,
  prefix = "ds",
  "aria-label": ariaLabel,
}: SpeedometerGaugeProps) {
  const uid = useId();
  const base = useMemo(() => speedometerGaugeBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };

  const numeric = value == null || Number.isNaN(Number(value)) ? null : Number(value);
  const span = max - min || 1;
  const ratio = numeric == null ? 0 : clamp((numeric - min) / span, 0, 1);
  const needleAngle = START_ANGLE - ratio * SWEEP;
  const tip = polar(CX, CY, R - 6, needleAngle);
  const resolvedTone = resolveTone(ratio, tone, autoTone);
  const fillPath =
    ratio <= 0
      ? ""
      : describeArc(CX, CY, R, START_ANGLE, START_ANGLE - ratio * SWEEP);
  const trackPath = describeArc(CX, CY, R, START_ANGLE, END_ANGLE);
  const display = numeric == null ? "—" : formatValue(numeric);
  const accessible =
    ariaLabel ||
    [label, numeric == null ? undefined : `${display}${unit}`].filter(Boolean).join(": ");

  return (
    <div
      className={[withBemModifier(classNames.root, resolvedTone), className]
        .filter(Boolean)
        .join(" ")}
      role="img"
      aria-label={accessible || "Velocímetro"}
      data-tone={resolvedTone}
    >
      <svg
        className={classNames.svg}
        viewBox={`0 0 ${VIEW} ${VIEW * 0.78}`}
        width={size}
        height={size * 0.78}
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={`${uid}-fill`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--delpi-ui-speedometer-start, var(--delpi-ui-accent, #089bdb))" />
            <stop offset="100%" stopColor="var(--delpi-ui-speedometer-end, var(--delpi-ui-accent, #089bdb))" />
          </linearGradient>
        </defs>
        <path className={classNames.track} d={trackPath} fill="none" strokeWidth={10} strokeLinecap="round" />
        {fillPath ? (
          <path
            className={classNames.fill}
            d={fillPath}
            fill="none"
            stroke={`url(#${uid}-fill)`}
            strokeWidth={10}
            strokeLinecap="round"
          />
        ) : null}
        {numeric != null ? (
          <>
            <line
              className={classNames.needle}
              x1={CX}
              y1={CY}
              x2={tip.x}
              y2={tip.y}
              strokeWidth={2.5}
              strokeLinecap="round"
            />
            <circle className={classNames.hub} cx={CX} cy={CY} r={4.5} />
          </>
        ) : null}
        <text className={classNames.value} x={CX} y={CY - 8} textAnchor="middle">
          {display}
          {numeric != null && unit ? (
            <tspan className={classNames.unit} dx={2}>
              {unit}
            </tspan>
          ) : null}
        </text>
      </svg>
      {label ? <p className={classNames.label}>{label}</p> : null}
    </div>
  );
}
