import {
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const CHART_HEIGHT = 320;

export type EssModernLineChartPoint = {
  label: string;
  value: number;
};

type EssModernLineChartProps = {
  points: EssModernLineChartPoint[];
  seriesLabel: string;
  formatValue: (value: number) => string;
  averageValue?: number | null;
  averageLabel?: string;
  emptyMessage?: string;
  className?: string;
};

type ChartPoint = {
  label: string;
  value: number;
  average: number | null;
};

export function EssModernLineChart({
  points,
  seriesLabel,
  formatValue,
  averageValue,
  averageLabel = "Média do período",
  emptyMessage = "Sem pontos para o gráfico.",
  className,
}: EssModernLineChartProps) {
  const normalizedAverage =
    typeof averageValue === "number" && Number.isFinite(averageValue)
      ? averageValue
      : null;
  const data: ChartPoint[] = points.map((point) => ({
    ...point,
    average: normalizedAverage,
  }));

  if (data.length === 0) {
    return <p className="ess-detail__empty">{emptyMessage}</p>;
  }

  const rootClassName = ["ess-modern-line-chart", className].filter(Boolean).join(" ");
  const renderPointLabel = (value: unknown): string => {
    const numeric = typeof value === "number" ? value : Number(value);
    return Number.isFinite(numeric) ? formatValue(numeric) : "";
  };

  return (
    <div className={rootClassName}>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <LineChart
          data={data}
          margin={{ top: 28, right: 28, bottom: 8, left: 8 }}
          accessibilityLayer
        >
          <CartesianGrid
            stroke="var(--ess-border)"
            strokeDasharray="3 3"
            vertical={false}
          />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "var(--ess-text-muted)" }}
            axisLine={{ stroke: "var(--ess-border)" }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--ess-text-muted)" }}
            tickFormatter={(value: number) => formatValue(value)}
            axisLine={false}
            tickLine={false}
            width={76}
          />
          <Tooltip
            formatter={(value, name) => [
              formatValue(typeof value === "number" ? value : Number(value)),
              String(name),
            ]}
            contentStyle={{
              background: "var(--ess-surface)",
              border: "1px solid var(--ess-border)",
              borderRadius: 12,
              color: "var(--ess-text)",
            }}
            labelStyle={{ color: "var(--ess-title)", fontWeight: 700 }}
          />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ color: "var(--ess-text)", fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="value"
            name={seriesLabel}
            stroke="var(--ess-accent)"
            strokeWidth={3}
            dot={{
              r: 4,
              fill: "var(--ess-surface)",
              stroke: "var(--ess-accent)",
              strokeWidth: 2,
            }}
            activeDot={{
              r: 6,
              fill: "var(--ess-accent)",
              stroke: "var(--ess-surface)",
              strokeWidth: 2,
            }}
          >
            <LabelList
              dataKey="value"
              position="top"
              formatter={renderPointLabel}
              fill="var(--ess-text)"
              fontSize={11}
              fontWeight={600}
            />
          </Line>
          {normalizedAverage !== null ? (
            <Line
              type="monotone"
              dataKey="average"
              name={averageLabel}
              stroke="var(--ess-text-muted)"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
              activeDot={false}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
