import {
  Area,
  AreaChart,
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
}: PresentationDepartmentSparklineProps) {
  const color = resolveSparklineColor(direction);

  if (!points.length) {
    return (
      <div className="si-presentation-sparkline si-presentation-sparkline--empty" />
    );
  }

  const chartData = points.map((point, index) => ({
    ...point,
    chartLabel: resolvePointLabel(point) || `P${index + 1}`,
  }));

  const gradientId = `sparkline-gradient-${direction}-${chartData.length}`;

  return (
    <div className="si-presentation-sparkline">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 4, right: 4, left: 4, bottom: 2 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.42} />
              <stop offset="100%" stopColor={color} stopOpacity={0.04} />
            </linearGradient>
          </defs>

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
            strokeWidth={3}
            fill={`url(#${gradientId})`}
            dot={chartData.length <= 8 ? { r: 2.5, strokeWidth: 0, fill: color } : false}
            activeDot={{ r: 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}