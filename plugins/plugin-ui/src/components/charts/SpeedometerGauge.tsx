import { useId, useMemo, useState, type CSSProperties } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import {
  bindChartPartPointer,
  chartPartTypographyStyle,
  getChartPartState,
  type ChartPartRef,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "./seriesChartParts";

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
  /**
   * Texto do tooltip interativo (hover/foco).
   * Só exibe card flutuante quando esta prop é uma string não vazia.
   */
  tip?: string;
  /** Exibe legenda das faixas. Default true. */
  showZonesLegend?: boolean;
  className?: string;
  classNames?: Partial<SpeedometerGaugeClassNames>;
  /** Prefixo BEM dual-class. Default `ds`. */
  prefix?: string;
  /**
   * Cor de destaque (agulha / preenchimento / hub). Quando definida, sobrescreve
   * a cor do tom automático nesses elementos; as faixas R/O/G permanecem semânticas.
   */
  accentColor?: string;
  /** Hit-test / seleção no editor TV (opcional). */
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
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

function resolveGaugePartBind(
  ref: ChartPartRef,
  interaction?: SeriesChartInteraction | null,
  chartParts?: ChartPartsMap | null,
) {
  const state = getChartPartState(chartParts, ref);
  const pointer = bindChartPartPointer(ref, interaction);
  const { selected, editing: _editing, onPointerDown, onDoubleClick, ...dom } = pointer;
  return {
    visible: state?.visible !== false,
    style: state?.style,
    content: state?.content,
    selected,
    onPointerDown,
    onDoubleClick,
    dom,
  };
}

/**
 * Velocímetro semicircular (0–max) para KPIs percentuais — SVG puro, faixas de alerta.
 * Tooltip só com `tip` explícito (sem auto-card no hover).
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
  accentColor,
  interaction,
  chartParts,
  "aria-label": ariaLabel,
}: SpeedometerGaugeProps) {
  const uid = useId();
  const [active, setActive] = useState(false);
  const base = useMemo(() => speedometerGaugeBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };
  const explicitTip = typeof tip === "string" && tip.trim() ? tip.trim() : null;

  const trackPart = resolveGaugePartBind({ kind: "gaugeTrack" }, interaction, chartParts);
  const fillPart = resolveGaugePartBind({ kind: "gaugeFill" }, interaction, chartParts);
  const needlePart = resolveGaugePartBind({ kind: "gaugeNeedle" }, interaction, chartParts);
  const valuePart = resolveGaugePartBind({ kind: "gaugeValue" }, interaction, chartParts);
  const labelPart = resolveGaugePartBind({ kind: "gaugeLabel" }, interaction, chartParts);
  const goalPart = resolveGaugePartBind({ kind: "gaugeGoalMarker" }, interaction, chartParts);
  const legendPart = resolveGaugePartBind({ kind: "legend" }, interaction, chartParts);
  const zone0 = resolveGaugePartBind({ kind: "gaugeZone", zoneIndex: 0 }, interaction, chartParts);
  const zone1 = resolveGaugePartBind({ kind: "gaugeZone", zoneIndex: 1 }, interaction, chartParts);
  const zone2 = resolveGaugePartBind({ kind: "gaugeZone", zoneIndex: 2 }, interaction, chartParts);
  const zoneParts = [zone0, zone1, zone2];

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
  const accent = accentColor?.trim() || toneColor;
  const fillStroke = fillPart.style?.stroke?.trim() || accent;
  const needleStroke = needlePart.style?.stroke?.trim() || accent;
  const needleFill = needlePart.style?.fill?.trim() || accent;
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

  const dangerEnd = START_ANGLE - zonesResolved.dangerBelow * SWEEP;
  const warningEnd = START_ANGLE - zonesResolved.warningBelow * SWEEP;
  const zones = [
    { tone: "danger" as const, from: START_ANGLE, to: dangerEnd, part: zone0 },
    { tone: "warning" as const, from: dangerEnd, to: warningEnd, part: zone1 },
    { tone: "success" as const, from: warningEnd, to: END_ANGLE, part: zone2 },
  ];

  const goalAngle = goalRatio == null ? null : START_ANGLE - goalRatio * SWEEP;
  const goalOuter = goalAngle == null ? null : polar(CX, CY, R + 8, goalAngle);
  const goalInner = goalAngle == null ? null : polar(CX, CY, R - 14, goalAngle);

  const valueTypography = chartPartTypographyStyle(chartParts, { kind: "gaugeValue" });
  const labelTypography = chartPartTypographyStyle(chartParts, { kind: "gaugeLabel" });
  const valueTextStyle: CSSProperties = {
    ...valueTypography,
    ...(valuePart.style?.color ? { fill: valuePart.style.color } : {}),
  };
  const labelTextStyle: CSSProperties = {
    ...labelTypography,
    ...(labelPart.style?.color ? { color: labelPart.style.color } : {}),
  };

  const tipHandlers = explicitTip
    ? {
        onMouseEnter: () => setActive(true),
        onMouseLeave: () => setActive(false),
        onFocus: () => setActive(true),
        onBlur: () => setActive(false),
      }
    : {};

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
      {...tipHandlers}
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
            <stop offset="0%" stopColor={fillStroke} stopOpacity={0.35} />
            <stop offset="100%" stopColor={fillStroke} stopOpacity={0.75} />
          </linearGradient>
        </defs>
        {zones.map((zone, zoneIndex) => {
          const part = zoneParts[zoneIndex];
          if (!part.visible || zone.from - zone.to <= 0.001) return null;
          const stroke = part.style?.stroke?.trim() || SPEEDOMETER_TONE_COLORS[zone.tone];
          return (
            <path
              key={zone.tone}
              className={withBemModifier(classNames.zone, zone.tone)}
              d={describeArc(CX, CY, R, zone.from, zone.to)}
              fill="none"
              stroke={stroke}
              strokeWidth={part.style?.strokeWidth ?? 14}
              strokeLinecap="butt"
              opacity={part.style?.opacity ?? 0.88}
              {...part.dom}
              onPointerDown={part.onPointerDown}
              onDoubleClick={part.onDoubleClick}
              style={part.selected ? { outline: "1px solid currentColor" } : undefined}
            />
          );
        })}
        {trackPart.visible ? (
          <path
            className={classNames.track}
            d={describeArc(CX, CY, R, START_ANGLE, END_ANGLE)}
            fill="none"
            stroke={trackPart.style?.stroke?.trim() || undefined}
            strokeWidth={trackPart.style?.strokeWidth ?? 2}
            strokeLinecap="round"
            opacity={trackPart.style?.opacity ?? 0.35}
            {...trackPart.dom}
            onPointerDown={trackPart.onPointerDown}
            onDoubleClick={trackPart.onDoubleClick}
          />
        ) : null}
        {fillPart.visible && fillPath ? (
          <path
            className={classNames.fill}
            d={fillPath}
            fill="none"
            stroke={fillPart.style?.stroke ? fillStroke : `url(#${uid}-fill)`}
            strokeWidth={fillPart.style?.strokeWidth ?? 6}
            strokeLinecap="round"
            opacity={fillPart.style?.opacity ?? 0.9}
            {...fillPart.dom}
            onPointerDown={fillPart.onPointerDown}
            onDoubleClick={fillPart.onDoubleClick}
          />
        ) : null}
        {goalPart.visible && goalOuter && goalInner ? (
          <g
            className={classNames.goalMarker}
            {...goalPart.dom}
            onPointerDown={goalPart.onPointerDown}
            onDoubleClick={goalPart.onDoubleClick}
          >
            <line
              className={classNames.goalTick}
              x1={goalInner.x}
              y1={goalInner.y}
              x2={goalOuter.x}
              y2={goalOuter.y}
              stroke={goalPart.style?.stroke?.trim() || undefined}
              strokeWidth={goalPart.style?.strokeWidth ?? 2.5}
              strokeLinecap="round"
            />
            <circle
              className={classNames.goalTick}
              cx={goalOuter.x}
              cy={goalOuter.y}
              r={3}
              fill={goalPart.style?.fill?.trim() || undefined}
            />
          </g>
        ) : null}
        {needlePart.visible && numeric != null ? (
          <g
            {...needlePart.dom}
            onPointerDown={needlePart.onPointerDown}
            onDoubleClick={needlePart.onDoubleClick}
          >
            <line
              className={classNames.needle}
              x1={CX}
              y1={CY}
              x2={tipPoint.x}
              y2={tipPoint.y}
              stroke={needleStroke}
              strokeWidth={needlePart.style?.strokeWidth ?? 3}
              strokeLinecap="round"
            />
            <circle className={classNames.hub} cx={CX} cy={CY} r={5.5} fill={needleFill} />
          </g>
        ) : null}
        {valuePart.visible ? (
          <text
            className={classNames.value}
            x={CX}
            y={CY - 10}
            textAnchor="middle"
            style={valueTextStyle}
            {...valuePart.dom}
            onPointerDown={valuePart.onPointerDown}
            onDoubleClick={valuePart.onDoubleClick}
          >
            {display}
            {numeric != null && unit ? (
              <tspan className={classNames.unit} dx={3}>
                {unit}
              </tspan>
            ) : null}
          </text>
        ) : null}
      </svg>
      {labelPart.visible && label ? (
        <p
          className={classNames.label}
          style={labelTextStyle}
          {...labelPart.dom}
          onPointerDown={labelPart.onPointerDown}
          onDoubleClick={labelPart.onDoubleClick}
        >
          {labelPart.content?.trim() || label}
        </p>
      ) : null}
      {goalPart.visible && goalCaption ? <p className={classNames.goal}>{goalCaption}</p> : null}
      {legendPart.visible && showZonesLegend ? (
        <ul
          className={classNames.legend}
          aria-hidden="true"
          {...legendPart.dom}
          onPointerDown={legendPart.onPointerDown}
          onDoubleClick={legendPart.onDoubleClick}
        >
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
      {explicitTip && active ? (
        <div className={classNames.tooltip} role="tooltip">
          {explicitTip}
        </div>
      ) : null}
    </div>
  );
}
