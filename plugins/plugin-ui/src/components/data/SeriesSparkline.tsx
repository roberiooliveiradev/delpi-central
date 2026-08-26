import { delpiUiClass } from "../../utils/delpiUiClass";

export type SeriesSparklineTone = "default" | "success" | "warning" | "danger";

export type SeriesSparklineClassNames = {
  root: string;
  chart: string;
};

export type SeriesSparklineProps = {
  classNames: SeriesSparklineClassNames;
  points: number[];
  tone?: SeriesSparklineTone;
  className?: string;
  "aria-label"?: string;
};

const VIEWBOX_WIDTH = 100;
const VIEWBOX_HEIGHT = 36;

export function seriesSparklineBemClasses(prefix: string): SeriesSparklineClassNames {
  const p = prefix.trim() || "delpi-ui";
  return {
    root: delpiUiClass(`${p}-series-sparkline`, "delpi-ui-series-sparkline"),
    chart: delpiUiClass(`${p}-series-sparkline__chart`, "delpi-ui-series-sparkline__chart"),
  };
}

function buildSeriesPath(points: number[]): string | null {
  if (points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const h = VIEWBOX_HEIGHT;

  return points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * VIEWBOX_WIDTH;
      const y = h - ((point - min) / span) * (h - 4) - 2;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function SeriesSparkline({
  classNames,
  points,
  tone = "default",
  className,
  "aria-label": ariaLabel,
}: SeriesSparklineProps) {
  const path = buildSeriesPath(points);
  if (!path) return null;

  const rootClass = [
    classNames.root,
    tone !== "default" ? `delpi-ui-series-sparkline--${tone}` : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role="img"
      aria-label={ariaLabel ?? `Série com ${points.length} pontos`}
    >
      <svg
        className={classNames.chart}
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d={path}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

export type DashboardSeriesSparklineProps = Omit<SeriesSparklineProps, "classNames">;

export function createDashboardSeriesSparkline(config: { prefix: string }) {
  const classNames = seriesSparklineBemClasses(config.prefix);
  return function DashboardSeriesSparkline(props: DashboardSeriesSparklineProps) {
    return <SeriesSparkline classNames={classNames} {...props} />;
  };
}
