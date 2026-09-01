import type { ChartPoint } from "../../utils/detailDisplay";

type SimpleLineChartProps = {
  points: ChartPoint[];
  height?: number;
  emptyMessage?: string;
};

export function SimpleLineChart({
  points,
  height = 220,
  emptyMessage = "Sem leituras no período.",
}: SimpleLineChartProps) {
  if (points.length === 0) {
    return <p className="pp-chart-empty">{emptyMessage}</p>;
  }

  const width = 640;
  const padding = { top: 16, right: 16, bottom: 28, left: 48 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const ys = points.map((point) => point.y);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanY = maxY - minY || 1;

  const coords = points.map((point, index) => {
    const x =
      padding.left +
      (points.length === 1 ? innerWidth / 2 : (index / (points.length - 1)) * innerWidth);
    const y = padding.top + innerHeight - ((point.y - minY) / spanY) * innerHeight;
    return { x, y };
  });

  const polyline = coords.map((coord) => `${coord.x},${coord.y}`).join(" ");

  return (
    <div className="pp-line-chart" style={{ height }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Gráfico de evolução temporal"
        preserveAspectRatio="none"
        className="pp-line-chart__svg"
      >
        <line
          x1={padding.left}
          y1={padding.top + innerHeight}
          x2={width - padding.right}
          y2={padding.top + innerHeight}
          className="pp-line-chart__axis"
        />
        <text x={padding.left} y={height - 6} className="pp-line-chart__label">
          {points[0]?.label}
        </text>
        <text x={width - padding.right} y={height - 6} textAnchor="end" className="pp-line-chart__label">
          {points[points.length - 1]?.label}
        </text>
        <text x={8} y={padding.top + 4} className="pp-line-chart__label">
          {maxY.toLocaleString("pt-BR")}
        </text>
        <text x={8} y={padding.top + innerHeight} className="pp-line-chart__label">
          {minY.toLocaleString("pt-BR")}
        </text>
        <polyline points={polyline} className="pp-line-chart__line" fill="none" />
        {coords.map((coord, index) => (
          <circle
            key={`${coord.x}-${index}`}
            cx={coord.x}
            cy={coord.y}
            r={3}
            className="pp-line-chart__dot"
          />
        ))}
      </svg>
    </div>
  );
}
