import { useId, useMemo, useState } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type SpeedometerGaugeTone = "neutral" | "success" | "warning" | "danger";

export type SpeedometerGaugeClassNames = {
  root: string;
  svg: string;
  track: string;
  zone: string;
  fill: string;
  needle: string;
  hub: string;
  goalMarker: string;
  goalTick: string;
  value: string;
  label: string;
  unit: string;
  goal: string;
  tooltip: string;
  legend: string;
  legendItem: string;
};

export type SpeedometerGaugeProps = {
  /** Valor atual (ex.: 98.8). */
  value: number | null | undefined;
  /** Meta (ex.: 95). Desenha indicador no arco e caption. */
  goal?: number | null | undefined;
  /** Rótulo da meta. Default «Meta». */
  goalLabel?: string;
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
   * Com `goal`, compara o valor à meta (higher-is-better).
   */
  autoTone?: boolean;
  /** Limites relativos (0–1) das faixas de alerta. */
  warningBelow?: number;
  dangerBelow?: number;
  size?: number;
  /** Texto do tooltip interativo (hover/foco). */
  tip?: string;
  /** Exibe legenda das faixas. Default true. */
  showZonesLegend?: boolean;
  className?: string;
  classNames?: Partial<SpeedometerGaugeClassNames>;
  /** Prefixo BEM dual-class. Default `ds`. */
  prefix?: string;
  "aria-label"?: string;
};

const VIEW = 140;
const CX = 70;
const CY = 82;
const R = 56;
const START_ANGLE = Math.PI;
const END_ANGLE = 0;
const SWEEP = START_ANGLE - END_ANGLE;

/** Cores sólidas de alerta (não dependem de var() em &lt;stop&gt; SVG). */
export const SPEEDOMETER_TONE_COLORS: Record<SpeedometerGaugeTone, string> = {
  success: "#16a34a",
  warning: "#d97706",
  danger: "#dc2626",
  neutral: "#089bdb",
};

export function speedometerGaugeBemClasses(prefix: string): SpeedometerGaugeClassNames {
  const ui = "delpi-ui-speedometer-gauge";
  return {
    root: delpiUiClass(`${prefix}-speedometer-gauge`, ui),
    svg: delpiUiClass(`${prefix}-speedometer-gauge__svg`, `${ui}__svg`),
    track: delpiUiClass(`${prefix}-speedometer-gauge__track`, `${ui}__track`),
    zone: delpiUiClass(`${prefix}-speedometer-gauge__zone`, `${ui}__zone`),
    fill: delpiUiClass(`${prefix}-speedometer-gauge__fill`, `${ui}__fill`),
    needle: delpiUiClass(`${prefix}-speedometer-gauge__needle`, `${ui}__needle`),
    hub: delpiUiClass(`${prefix}-speedometer-gauge__hub`, `${ui}__hub`),
    goalMarker: delpiUiClass(`${prefix}-speedometer-gauge__goal-marker`, `${ui}__goal-marker`),
    goalTick: delpiUiClass(`${prefix}-speedometer-gauge__goal-tick`, `${ui}__goal-tick`),
    value: delpiUiClass(`${prefix}-speedometer-gauge__value`, `${ui}__value`),
    label: delpiUiClass(`${prefix}-speedometer-gauge__label`, `${ui}__label`),
    unit: delpiUiClass(`${prefix}-speedometer-gauge__unit`, `${ui}__unit`),
    goal: delpiUiClass(`${prefix}-speedometer-gauge__goal`, `${ui}__goal`),
    tooltip: delpiUiClass(`${prefix}-speedometer-gauge__tooltip`, `${ui}__tooltip`),
    legend: delpiUiClass(`${prefix}-speedometer-gauge__legend`, `${ui}__legend`),
    legendItem: delpiUiClass(`${prefix}-speedometer-gauge__legend-item`, `${ui}__legend-item`),
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
  dangerBelow: number,
  warningBelow: number,
): SpeedometerGaugeTone {
  if (tone) return tone;
  if (!autoTone) return "neutral";
  if (ratio < dangerBelow) return "danger";
  if (ratio < warningBelow) return "warning";
  return "success";
}

/**
 * Faixas do arco (0–1). Com meta, o verde começa na meta e o vermelho fica ~10% abaixo.
 */
export function resolveSpeedometerZoneThresholds(args: {
  goalRatio: number | null;
  dangerBelow: number;
  warningBelow: number;
}): { dangerBelow: number; warningBelow: number } {
  const { goalRatio, dangerBelow, warningBelow } = args;
  if (goalRatio == null || !Number.isFinite(goalRatio) || goalRatio <= 0) {
    return { dangerBelow, warningBelow };
  }
  const warning = clamp(goalRatio, 0.05, 1);
  const danger = clamp(Math.min(warning * 0.9, warning - 0.05), 0.02, Math.max(0.03, warning - 0.01));
  return { dangerBelow: danger, warningBelow: warning };
}

function defaultFormat(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function formatLegendPct(ratio: number): string {
  return `${Math.round(ratio * 100)}`;
}

function toneLabel(tone: SpeedometerGaugeTone): string {
  switch (tone) {
    case "success":
      return "Dentro da meta";
    case "warning":
      return "Atenção";
    case "danger":
      return "Crítico";
    default:
      return "Neutro";
  }
}

/**
 * Velocímetro semicircular (0–max) para KPIs percentuais — SVG puro, faixas de alerta e tooltip.
 */
export function SpeedometerGauge({
  value,
  goal,
  goalLabel = "Meta",
  max = 100,
  min = 0,
  label,
  unit = "%",
  formatValue = defaultFormat,
  tone,
  autoTone = true,
  warningBelow = 0.95,
  dangerBelow = 0.9,
  size = 260,
  tip,
  showZonesLegend = true,
  className,
  classNames: classNamesOverride,
  prefix = "ds",
  "aria-label": ariaLabel,
}: SpeedometerGaugeProps) {
  const uid = useId();
  const [active, setActive] = useState(false);
  const base = useMemo(() => speedometerGaugeBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };

  const numeric = value == null || Number.isNaN(Number(value)) ? null : Number(value);
  const goalNumeric = goal == null || Number.isNaN(Number(goal)) ? null : Number(goal);
  const span = max - min || 1;
  const ratio = numeric == null ? 0 : clamp((numeric - min) / span, 0, 1);
  const goalRatio =
    goalNumeric == null ? null : clamp((goalNumeric - min) / span, 0, 1);
  const zonesResolved = resolveSpeedometerZoneThresholds({
    goalRatio,
    dangerBelow,
    warningBelow,
  });
  const needleAngle = START_ANGLE - ratio * SWEEP;
  const tipPoint = polar(CX, CY, R - 8, needleAngle);
  const resolvedTone = resolveTone(
    ratio,
    tone,
    autoTone,
    zonesResolved.dangerBelow,
    zonesResolved.warningBelow,
  );
  const toneColor = SPEEDOMETER_TONE_COLORS[resolvedTone];
  const fillPath =
    ratio <= 0 ? "" : describeArc(CX, CY, R, START_ANGLE, START_ANGLE - ratio * SWEEP);
  const display = numeric == null ? "—" : formatValue(numeric);
  const goalDisplay = goalNumeric == null ? null : formatValue(goalNumeric);
  const goalCaption =
    goalDisplay == null ? null : `${goalLabel}: ${goalDisplay}${unit ? ` ${unit}` : ""}`;
  const accessible =
    ariaLabel ||
    [
      label,
      numeric == null ? undefined : `${display}${unit}`,
      goalCaption ?? undefined,
      toneLabel(resolvedTone),
    ]
      .filter(Boolean)
      .join(": ");
  const tooltipText =
    tip ||
    (numeric == null
      ? "Sem dado no período."
      : [
          label ? `${label}: ${display}${unit}` : `${display}${unit}`,
          goalCaption,
          toneLabel(resolvedTone),
        ]
          .filter(Boolean)
          .join(" · "));

  const dangerEnd = START_ANGLE - zonesResolved.dangerBelow * SWEEP;
  const warningEnd = START_ANGLE - zonesResolved.warningBelow * SWEEP;
  const zones = [
    { tone: "danger" as const, from: START_ANGLE, to: dangerEnd },
    { tone: "warning" as const, from: dangerEnd, to: warningEnd },
    { tone: "success" as const, from: warningEnd, to: END_ANGLE },
  ];

  const goalAngle = goalRatio == null ? null : START_ANGLE - goalRatio * SWEEP;
  const goalOuter = goalAngle == null ? null : polar(CX, CY, R + 8, goalAngle);
  const goalInner = goalAngle == null ? null : polar(CX, CY, R - 14, goalAngle);

  return (
    <div
      className={[withBemModifier(classNames.root, resolvedTone), className]
        .filter(Boolean)
        .join(" ")}
      role="img"
      aria-label={accessible || "Velocímetro"}
      data-tone={resolvedTone}
      data-goal={goalNumeric == null ? undefined : String(goalNumeric)}
      data-zone-warning={String(zonesResolved.warningBelow)}
      data-zone-danger={String(zonesResolved.dangerBelow)}
      tabIndex={0}
      onMouseEnter={() => setActive(true)}
      onMouseLeave={() => setActive(false)}
      onFocus={() => setActive(true)}
      onBlur={() => setActive(false)}
    >
      <svg
        className={classNames.svg}
        viewBox={`0 0 ${VIEW} ${VIEW * 0.72}`}
        width={size}
        height={size * 0.72}
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={`${uid}-fill`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={toneColor} stopOpacity={0.35} />
            <stop offset="100%" stopColor={toneColor} stopOpacity={0.75} />
          </linearGradient>
        </defs>
        {zones.map((zone) =>
          zone.from - zone.to > 0.001 ? (
            <path
              key={zone.tone}
              className={withBemModifier(classNames.zone, zone.tone)}
              d={describeArc(CX, CY, R, zone.from, zone.to)}
              fill="none"
              stroke={SPEEDOMETER_TONE_COLORS[zone.tone]}
              strokeWidth={14}
              strokeLinecap="butt"
              opacity={0.88}
            />
          ) : null,
        )}
        <path
          className={classNames.track}
          d={describeArc(CX, CY, R, START_ANGLE, END_ANGLE)}
          fill="none"
          strokeWidth={2}
          strokeLinecap="round"
          opacity={0.35}
        />
        {fillPath ? (
          <path
            className={classNames.fill}
            d={fillPath}
            fill="none"
            stroke={`url(#${uid}-fill)`}
            strokeWidth={6}
            strokeLinecap="round"
            opacity={0.9}
          />
        ) : null}
        {goalOuter && goalInner ? (
          <g className={classNames.goalMarker}>
            <line
              className={classNames.goalTick}
              x1={goalInner.x}
              y1={goalInner.y}
              x2={goalOuter.x}
              y2={goalOuter.y}
              strokeWidth={2.5}
              strokeLinecap="round"
            />
            <circle className={classNames.goalTick} cx={goalOuter.x} cy={goalOuter.y} r={3} />
          </g>
        ) : null}
        {numeric != null ? (
          <>
            <line
              className={classNames.needle}
              x1={CX}
              y1={CY}
              x2={tipPoint.x}
              y2={tipPoint.y}
              stroke={toneColor}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <circle className={classNames.hub} cx={CX} cy={CY} r={5.5} fill={toneColor} />
          </>
        ) : null}
        <text className={classNames.value} x={CX} y={CY - 10} textAnchor="middle">
          {display}
          {numeric != null && unit ? (
            <tspan className={classNames.unit} dx={3}>
              {unit}
            </tspan>
          ) : null}
        </text>
      </svg>
      {label ? <p className={classNames.label}>{label}</p> : null}
      {goalCaption ? <p className={classNames.goal}>{goalCaption}</p> : null}
      {showZonesLegend ? (
        <ul className={classNames.legend} aria-hidden="true">
          <li className={classNames.legendItem} data-tone="danger">
            &lt; {formatLegendPct(zonesResolved.dangerBelow)}
            {unit}
          </li>
          <li className={classNames.legendItem} data-tone="warning">
            {formatLegendPct(zonesResolved.dangerBelow)}
            {unit}–{formatLegendPct(zonesResolved.warningBelow)}
            {unit}
          </li>
          <li className={classNames.legendItem} data-tone="success">
            ≥ {formatLegendPct(zonesResolved.warningBelow)}
            {unit}
          </li>
        </ul>
      ) : null}
      {active ? (
        <div className={classNames.tooltip} role="tooltip">
          {tooltipText}
        </div>
      ) : null}
    </div>
  );
}
