import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

type PresentationDepartmentSparklinePoint = {
  label: string;
  value: number;
};

type PresentationDepartmentSparklineProps = {
  points: PresentationDepartmentSparklinePoint[];
  direction?: "up" | "down" | "stable";
};

type TooltipValue =
  | number
  | string
  | readonly (string | number)[]
  | undefined;

function resolveSparklineColor(direction?: "up" | "down" | "stable") {
  if (direction === "up") return "#22c55e";
  if (direction === "down") return "#ef4444";
  return "#3b82f6";
}

function toNumber(value: TooltipValue): number {
  if (typeof value === "number") return value;

  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      if (typeof item === "number" && Number.isFinite(item)) {
        return item;
      }

      if (typeof item === "string") {
        const parsed = Number(item);
        if (Number.isFinite(parsed)) {
          return parsed;
        }
      }
    }
  }

  return 0;
}

function formatValue(value: TooltipValue) {
  return toNumber(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
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

  return (
    <div className="si-presentation-sparkline">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={points}
          margin={{ top: 4, right: 4, left: 4, bottom: 2 }}
        >
          <defs>
            <linearGradient
              id={`sparkline-gradient-${color}`}
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop offset="0%" stopColor={color} stopOpacity={0.42} />
              <stop offset="100%" stopColor={color} stopOpacity={0.04} />
            </linearGradient>
          </defs>

          <XAxis dataKey="label" hide />
          <Tooltip
            cursor={false}
            formatter={(value) => [formatValue(value), "Score"]}
            labelFormatter={() => ""}
            contentStyle={{
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(15, 23, 42, 0.96)",
              color: "#ffffff",
            }}
          />

          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={3}
            fill={`url(#sparkline-gradient-${color})`}
            dot={{ r: 2.5, strokeWidth: 0, fill: color }}
            activeDot={{ r: 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}