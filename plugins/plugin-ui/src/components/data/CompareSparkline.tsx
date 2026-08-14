import { delpiUiClass } from "../../utils/delpiUiClass";

export type CompareSparklineTone = "up" | "down" | "flat";

export type CompareSparklineClassNames = {
  root: string;
  chart: string;
};

export type CompareSparklineProps = {
  classNames: CompareSparklineClassNames;
  /** Valor do período anterior. */
  prior: number;
  /** Valor do período atual. */
  current: number;
  /** Tom forçado; default derivado de prior×current. */
  tone?: CompareSparklineTone;
  className?: string;
  "aria-label"?: string;
};

const VB_W = 64;
const VB_H = 32;
const PAD_Y = 3;
const BAR_W = 10;
const BAR_GAP = 18;
const BAR_X0 = 14;
const BAR_X1 = BAR_X0 + BAR_W + BAR_GAP;
const BASE_Y = VB_H - 2;

export function compareSparklineBemClasses(prefix: string): CompareSparklineClassNames {
  const p = prefix.trim() || "delpi-ui";
  return {
    root: delpiUiClass(`${p}-compare-sparkline`, "delpi-ui-compare-sparkline"),
    chart: delpiUiClass(`${p}-compare-sparkline__chart`, "delpi-ui-compare-sparkline__chart"),
  };
}

export function resolveCompareSparklineTone(
  prior: number,
  current: number,
): CompareSparklineTone {
  if (!Number.isFinite(prior) || !Number.isFinite(current)) return "flat";
  if (current > prior) return "up";
  if (current < prior) return "down";
  return "flat";
}

function safeAbs(n: number): number {
  return Number.isFinite(n) ? Math.abs(n) : 0;
}

/** Altura da barra em coordenadas SVG (do baseline para cima). */
export function compareBarHeight(value: number, max: number): number {
  const usable = VB_H - PAD_Y * 2 - 2;
  if (!Number.isFinite(value) || value <= 0 || max <= 0) return Math.max(3, usable * 0.08);
  return Math.max(3, (value / max) * usable);
}

/**
 * Minigráfico prior × atual unificado (barras + linha + área) para células de tabela.
 */
export function CompareSparkline({
  classNames,
  prior,
  current,
  tone: toneProp,
  className,
  "aria-label": ariaLabel,
}: CompareSparklineProps) {
  const tone = toneProp ?? resolveCompareSparklineTone(prior, current);
  const priorAbs = safeAbs(prior);
  const currentAbs = safeAbs(current);
  const max = Math.max(priorAbs, currentAbs, 1);
  const h0 = compareBarHeight(priorAbs, max);
  const h1 = compareBarHeight(currentAbs, max);
  const y0 = BASE_Y - h0;
  const y1 = BASE_Y - h1;
  const cx0 = BAR_X0 + BAR_W / 2;
  const cx1 = BAR_X1 + BAR_W / 2;
  const areaPath = [
    `M${cx0},${BASE_Y}`,
    `L${cx0},${y0.toFixed(2)}`,
    `L${cx1},${y1.toFixed(2)}`,
    `L${cx1},${BASE_Y}`,
    "Z",
  ].join(" ");
  const linePath = `M${cx0},${y0.toFixed(2)} L${cx1},${y1.toFixed(2)}`;

  const rootClass = [
    classNames.root,
    `delpi-ui-compare-sparkline--${tone}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role="img"
      aria-label={
        ariaLabel ??
        `Comparação período anterior ${prior} e atual ${current}`
      }
    >
      <svg
        className={classNames.chart}
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      >
        <line
          className="delpi-ui-compare-sparkline__baseline"
          x1={6}
          y1={BASE_Y}
          x2={VB_W - 6}
          y2={BASE_Y}
        />
        <path className="delpi-ui-compare-sparkline__area" d={areaPath} />
        <rect
          className="delpi-ui-compare-sparkline__bar delpi-ui-compare-sparkline__bar--prior"
          x={BAR_X0}
          y={y0}
          width={BAR_W}
          height={h0}
          rx={2}
        />
        <rect
          className="delpi-ui-compare-sparkline__bar delpi-ui-compare-sparkline__bar--current"
          x={BAR_X1}
          y={y1}
          width={BAR_W}
          height={h1}
          rx={2}
        />
        <path className="delpi-ui-compare-sparkline__line" d={linePath} />
        <circle
          className="delpi-ui-compare-sparkline__dot delpi-ui-compare-sparkline__dot--prior"
          cx={cx0}
          cy={y0}
          r={2.25}
        />
        <circle
          className="delpi-ui-compare-sparkline__dot delpi-ui-compare-sparkline__dot--current"
          cx={cx1}
          cy={y1}
          r={2.5}
        />
      </svg>
    </div>
  );
}

export type DashboardCompareSparklineProps = Omit<CompareSparklineProps, "classNames">;

export function createDashboardCompareSparkline(config: { prefix: string }) {
  const classNames = compareSparklineBemClasses(config.prefix);
  return function DashboardCompareSparkline(props: DashboardCompareSparklineProps) {
    return <CompareSparkline classNames={classNames} {...props} />;
  };
}
