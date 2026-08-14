import { delpiUiClass } from "../../utils/delpiUiClass";

export type CompareSparklineTone = "up" | "down" | "flat";

export type CompareSparklineClassNames = {
  root: string;
  bars: string;
  bar: string;
  spark: string;
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

export function compareSparklineBemClasses(prefix: string): CompareSparklineClassNames {
  const p = prefix.trim() || "delpi-ui";
  return {
    root: delpiUiClass(`${p}-compare-sparkline`, "delpi-ui-compare-sparkline"),
    bars: delpiUiClass(`${p}-compare-sparkline__bars`, "delpi-ui-compare-sparkline__bars"),
    bar: delpiUiClass(`${p}-compare-sparkline__bar`, "delpi-ui-compare-sparkline__bar"),
    spark: delpiUiClass(`${p}-compare-sparkline__spark`, "delpi-ui-compare-sparkline__spark"),
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

function barHeightPct(value: number, max: number): number {
  if (!Number.isFinite(value) || value <= 0 || max <= 0) return 8;
  return Math.max(8, Math.min(100, (value / max) * 100));
}

function sparkPath(prior: number, current: number): string {
  const w = 48;
  const h = 20;
  const min = Math.min(prior, current);
  const max = Math.max(prior, current);
  const span = max - min || 1;
  const y0 = h - ((prior - min) / span) * (h - 4) - 2;
  const y1 = h - ((current - min) / span) * (h - 4) - 2;
  return `M2,${y0.toFixed(2)} L${(w - 2).toFixed(2)},${y1.toFixed(2)}`;
}

/**
 * Minigráfico prior × atual (duas barras + sparkline de 2 pontos) para células de tabela.
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
  const max = Math.max(
    Number.isFinite(prior) ? Math.abs(prior) : 0,
    Number.isFinite(current) ? Math.abs(current) : 0,
    1,
  );
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
      <div className={classNames.bars} aria-hidden="true">
        <span
          className={[classNames.bar, "delpi-ui-compare-sparkline__bar--prior"].join(" ")}
          style={{ height: `${barHeightPct(Math.abs(prior), max)}%` }}
        />
        <span
          className={[classNames.bar, "delpi-ui-compare-sparkline__bar--current"].join(" ")}
          style={{ height: `${barHeightPct(Math.abs(current), max)}%` }}
        />
      </div>
      <svg
        className={classNames.spark}
        viewBox="0 0 48 20"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d={sparkPath(prior, current)}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
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
