import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

type PresentationDepartmentSparklinePoint = {
  period?: string;
  label?: string;
  value: number;
};

type PresentationDepartmentSparklineProps = {
  points: PresentationDepartmentSparklinePoint[];
  direction?: "up" | "down" | "stable";
  height?: number;
  compact?: boolean;
  showGrid?: boolean;
};

type TooltipValue = number | string | null | undefined;

function resolveSparklineColor(direction?: "up" | "down" | "stable") {
  if (direction === "up") return "#22c55e";
  if (direction === "down") return "#ef4444";
  return "#3b82f6";
}

function formatValue(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function normalizeTooltipValue(value: TooltipValue): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function resolvePointLabel(point: PresentationDepartmentSparklinePoint) {
  return point.period ?? point.label ?? "";
}

export function PresentationDepartmentSparkline({
  points,
  direction = "stable",
  height = 72,
  compact = false,
  showGrid = false,
}: PresentationDepartmentSparklineProps) {
  const color = resolveSparklineColor(direction);

  if (!points.length) {
    return (
      <div
        className="si-presentation-sparkline si-presentation-sparkline--empty"
        style={{ height }}
      />
    );
  }

  const chartData = points.map((point, index) => ({
    ...point,
    chartLabel: resolvePointLabel(point) || `P${index + 1}`,
  }));

  const gradientId = `sparkline-gradient-${direction}-${chartData.length}-${height}`;
  const strokeWidth = compact ? 2.5 : 3;
  const dotRadius = compact ? 2 : 2.8;

  return (
    <div className="si-presentation-sparkline" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{
            top: compact ? 4 : 6,
            right: compact ? 4 : 8,
            left: compact ? 0 : 4,
            bottom: compact ? 0 : 4,
          }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.34} />
              <stop offset="100%" stopColor={color} stopOpacity={0.03} />
            </linearGradient>
          </defs>

          {showGrid ? (
            <CartesianGrid
              vertical={false}
              stroke="rgba(0,0,0,0.08)"
              strokeDasharray="4 4"
            />
          ) : null}

          <XAxis dataKey="chartLabel" hide />

          <Tooltip
            cursor={false}
            labelFormatter={(label) => String(label ?? "")}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;

              const numericValue = normalizeTooltipValue(
                payload[0]?.value as TooltipValue,
              );

              if (numericValue === null) return null;

              return (
                <div
                  style={{
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.12)",
                    background: "rgba(15, 23, 42, 0.96)",
                    color: "#ffffff",
                    padding: "8px 10px",
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  <div style={{ marginBottom: 4 }}>{String(label ?? "")}</div>
                  <div>Score: {formatValue(numericValue)}</div>
                </div>
              );
            }}
          />

          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={strokeWidth}
            fill={`url(#${gradientId})`}
            dot={
              chartData.length <= 8
                ? { r: dotRadius, strokeWidth: 0, fill: color }
                : false
            }
            activeDot={{ r: compact ? 3 : 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}