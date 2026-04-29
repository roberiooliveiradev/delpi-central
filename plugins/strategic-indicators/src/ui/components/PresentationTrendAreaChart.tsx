import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./PresentationTrendAreaChart.css";

type PresentationTrendAreaChartPoint = {
  period: string;
  value: number;
};

type PresentationTrendAreaChartProps = {
  points: PresentationTrendAreaChartPoint[];
};

type TooltipValue =
  | number
  | string
  | readonly (string | number)[]
  | undefined;

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

function formatScore(value: TooltipValue) {
  return toNumber(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function PresentationTrendAreaChart({
  points,
}: PresentationTrendAreaChartProps) {
  return (
    <section className="si-presentation-trend-chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={points}
          margin={{ top: 12, right: 16, left: -8, bottom: 0 }}
        >
          <defs>
            <linearGradient
              id="si-presentation-trend-area"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop offset="0%" stopColor="#089bdb" stopOpacity={0.42} />
              <stop offset="100%" stopColor="#089bdb" stopOpacity={0.04} />
            </linearGradient>
          </defs>

          <CartesianGrid
            vertical={false}
            stroke="color-mix(in srgb, var(--si-card-border) 76%, transparent)"
            strokeDasharray="4 4"
          />
          <XAxis
            dataKey="period"
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--si-text-muted)", fontSize: 12 }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--si-text-muted)", fontSize: 12 }}
            domain={["dataMin - 0.5", "dataMax + 0.5"]}
            tickFormatter={(value) => formatScore(value)}
          />

          <Tooltip
            formatter={(value) => [formatScore(value), "IGD"]}
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
            stroke="#089bdb"
            strokeWidth={4}
            fill="url(#si-presentation-trend-area)"
            dot={{
              r: 5,
              fill: "#089bdb",
              stroke: "#ffffff",
              strokeWidth: 2,
            }}
            activeDot={{
              r: 6,
              fill: "#089bdb",
              stroke: "#ffffff",
              strokeWidth: 2,
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </section>
  );
}