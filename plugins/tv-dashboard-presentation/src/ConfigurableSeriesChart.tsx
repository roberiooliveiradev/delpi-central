import {
  formatSeriesChartValue,
  mergeComunicadoChartOptions,
  resolveSeriesChartTicks,
  usableSeriesChartPoints,
  type ComunicadoChartOptions,
  type SeriesChartKind,
  type SeriesChartPoint,
} from "./comunicadoChartOptions";

export type ConfigurableSeriesChartProps = {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  options?: ComunicadoChartOptions | null;
  emptyMessage?: string;
  className?: string;
};

const VIEW_W = 400;
const VIEW_H = 220;
const MARGIN = { top: 12, right: 12, bottom: 36, left: 52 };

function xLabelStep(count: number): number {
  if (count <= 8) return 1;
  if (count <= 16) return 2;
  return Math.ceil(count / 8);
}

function ChartDataTable({
  points,
  seriesName,
  valueFormat,
}: {
  points: SeriesChartPoint[];
  seriesName: string;
  valueFormat: ComunicadoChartOptions["valueFormat"];
}) {
  return (
    <table className="tdp-series-chart__data-table">
      <thead>
        <tr>
          <th>Período</th>
          <th>{seriesName}</th>
        </tr>
      </thead>
      <tbody>
        {points.map((point, index) => (
          <tr key={`dt-${index}`}>
            <td>{String(point.label ?? index + 1)}</td>
            <td>{formatSeriesChartValue(Number(point.value), valueFormat ?? "auto")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ConfigurableSeriesChart({
  chartType,
  points,
  options,
  emptyMessage = "Sem série",
  className,
}: ConfigurableSeriesChartProps) {
  const config = mergeComunicadoChartOptions(options);
  const usable = usableSeriesChartPoints(points);
  if (usable.length === 0) {
    return (
      <div className={["tdp-series-chart tdp-series-chart--empty", className].filter(Boolean).join(" ")}>
        {emptyMessage}
      </div>
    );
  }

  const values = usable.map((point) => Number(point.value));
  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  const ticks = resolveSeriesChartTicks(dataMin, dataMax);
  const axisMin = ticks[0] ?? dataMin;
  const axisMax = ticks[ticks.length - 1] ?? dataMax;
  const axisRange = Math.max(axisMax - axisMin, 1e-6);

  const plotW = VIEW_W - MARGIN.left - MARGIN.right;
  const plotH = VIEW_H - MARGIN.top - MARGIN.bottom;
  const labelStep = xLabelStep(usable.length);
  const seriesColor = config.seriesColor || "#0d7a8c";
  const title = config.title?.trim();
  const seriesName = config.seriesName?.trim() || title || "Série";
  const showLegend = config.showLegend && config.legendPosition !== "hidden";
  const showAxes = config.showAxes !== false;
  const valueFormat = config.valueFormat ?? "auto";

  const legend = showLegend ? (
    <ul
      className={[
        "tdp-series-chart__legend",
        `tdp-series-chart__legend--${config.legendPosition}`,
      ].join(" ")}
      aria-label="Legenda"
    >
      <li className="tdp-series-chart__legend-item">
        <span className="tdp-series-chart__legend-swatch" style={{ background: seriesColor }} aria-hidden />
        <span>{seriesName}</span>
      </li>
    </ul>
  ) : null;

  const toX = (index: number) =>
    MARGIN.left + (usable.length > 1 ? (index / (usable.length - 1)) * plotW : plotW / 2);
  const toY = (value: number) => MARGIN.top + plotH - ((value - axisMin) / axisRange) * plotH;

  return (
    <div className={["tdp-series-chart", className].filter(Boolean).join(" ")}>
      {config.showTitle && title ? <div className="tdp-series-chart__title">{title}</div> : null}
      {config.legendPosition === "top" ? legend : null}
      <div className="tdp-series-chart__body">
        <svg
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          className="tdp-series-chart__svg"
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={title || seriesName}
        >
          {config.showYAxisTitle && config.yAxisTitle ? (
            <text
              x={10}
              y={MARGIN.top + plotH / 2}
              className="tdp-series-chart__axis-title tdp-series-chart__axis-title--y"
              transform={`rotate(-90 10 ${MARGIN.top + plotH / 2})`}
            >
              {config.yAxisTitle}
            </text>
          ) : null}

          {config.showGrid
            ? ticks.map((tick) => {
                const y = toY(tick);
                return (
                  <line
                    key={`grid-h-${tick}`}
                    x1={MARGIN.left}
                    y1={y}
                    x2={MARGIN.left + plotW}
                    y2={y}
                    className="tdp-series-chart__grid-line"
                  />
                );
              })
            : null}

          {config.showVerticalGrid
            ? usable.map((_, index) => {
                const x = toX(index);
                return (
                  <line
                    key={`grid-v-${index}`}
                    x1={x}
                    y1={MARGIN.top}
                    x2={x}
                    y2={MARGIN.top + plotH}
                    className="tdp-series-chart__grid-line tdp-series-chart__grid-line--vertical"
                  />
                );
              })
            : null}

          <rect
            x={MARGIN.left}
            y={MARGIN.top}
            width={plotW}
            height={plotH}
            className={[
              "tdp-series-chart__plot-area",
              showAxes ? "tdp-series-chart__plot-area--axes" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          />

          {showAxes ? (
            <>
              <line
                x1={MARGIN.left}
                y1={MARGIN.top + plotH}
                x2={MARGIN.left + plotW}
                y2={MARGIN.top + plotH}
                className="tdp-series-chart__axis-line"
              />
              <line
                x1={MARGIN.left}
                y1={MARGIN.top}
                x2={MARGIN.left}
                y2={MARGIN.top + plotH}
                className="tdp-series-chart__axis-line"
              />
            </>
          ) : null}

          {config.showYAxisLabels
            ? ticks.map((tick) => {
                const y = toY(tick);
                return (
                  <text
                    key={`y-${tick}`}
                    x={MARGIN.left - 6}
                    y={y}
                    className="tdp-series-chart__tick tdp-series-chart__tick--y"
                    textAnchor="end"
                    dominantBaseline="middle"
                  >
                    {formatSeriesChartValue(tick, valueFormat)}
                  </text>
                );
              })
            : null}

          {chartType === "bar"
            ? usable.map((point, index) => {
                const value = Number(point.value);
                const barW = plotW / Math.max(usable.length, 1);
                const gap = Math.min(barW * 0.2, 8);
                const width = Math.max(barW - gap, 2);
                const x = MARGIN.left + index * barW + gap / 2;
                const y = toY(value);
                const height = MARGIN.top + plotH - y;
                return (
                  <g key={`bar-${index}`}>
                    <rect x={x} y={y} width={width} height={height} fill={seriesColor} rx={1} />
                    {config.showDataLabels ? (
                      <text
                        x={x + width / 2}
                        y={y - 4}
                        className="tdp-series-chart__data-label"
                        textAnchor="middle"
                      >
                        {formatSeriesChartValue(value, valueFormat)}
                      </text>
                    ) : null}
                  </g>
                );
              })
            : null}

          {chartType === "line" ? (
            <>
              <polyline
                points={usable.map((point, index) => `${toX(index)},${toY(Number(point.value))}`).join(" ")}
                fill="none"
                stroke={seriesColor}
                strokeWidth={2}
                vectorEffect="non-scaling-stroke"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              {config.showMarkers !== false
                ? usable.map((point, index) => (
                    <circle
                      key={`dot-${index}`}
                      cx={toX(index)}
                      cy={toY(Number(point.value))}
                      r={2.5}
                      fill={seriesColor}
                    />
                  ))
                : null}
              {config.showDataLabels
                ? usable.map((point, index) => (
                    <text
                      key={`label-${index}`}
                      x={toX(index)}
                      y={toY(Number(point.value)) - 6}
                      className="tdp-series-chart__data-label"
                      textAnchor="middle"
                    >
                      {formatSeriesChartValue(Number(point.value), valueFormat)}
                    </text>
                  ))
                : null}
            </>
          ) : null}

          {config.showXAxisLabels
            ? usable.map((point, index) =>
                index % labelStep === 0 || index === usable.length - 1 ? (
                  <text
                    key={`x-${index}`}
                    x={toX(index)}
                    y={MARGIN.top + plotH + 14}
                    className="tdp-series-chart__tick tdp-series-chart__tick--x"
                    textAnchor="middle"
                  >
                    {String(point.label ?? index + 1)}
                  </text>
                ) : null,
              )
            : null}

          {config.showXAxisTitle && config.xAxisTitle ? (
            <text
              x={MARGIN.left + plotW / 2}
              y={VIEW_H - 4}
              className="tdp-series-chart__axis-title tdp-series-chart__axis-title--x"
              textAnchor="middle"
            >
              {config.xAxisTitle}
            </text>
          ) : null}
        </svg>
        {config.legendPosition === "right" ? legend : null}
      </div>
      {config.legendPosition === "bottom" ? legend : null}
      {config.showDataTable ? (
        <ChartDataTable points={usable} seriesName={seriesName} valueFormat={valueFormat} />
      ) : null}
    </div>
  );
}
