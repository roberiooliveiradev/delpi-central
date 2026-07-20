import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const CHART_HEIGHT = 320;

const SERIES_COLORS = [
  "var(--ess-accent)",
  "var(--ess-chart-secondary, #0f766e)",
  "var(--ess-chart-tertiary, #b45309)",
];

export type EssModernMultiLineSeries = {
  key: string;
  label: string;
  color?: string;
};

export type EssModernMultiLinePoint = {
  label: string;
  [seriesKey: string]: string | number | null;
};

type EssModernMultiLineChartProps = {
  points: EssModernMultiLinePoint[];
  series: EssModernMultiLineSeries[];
  formatValue: (value: number) => string;
  emptyMessage?: string;
  className?: string;
};

export function toggleHiddenSeriesKey(
  hiddenKeys: ReadonlySet<string>,
  key: string,
): Set<string> {
  const next = new Set(hiddenKeys);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  return next;
}

export function EssModernMultiLineChart({
  points,
  series,
  formatValue,
  emptyMessage = "Sem pontos para o gráfico.",
  className,
}: EssModernMultiLineChartProps) {
  const seriesKeySignature = useMemo(
    () => series.map((item) => item.key).join("|"),
    [series],
  );
  const [hiddenKeys, setHiddenKeys] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    setHiddenKeys(new Set());
  }, [seriesKeySignature]);

  const hasSeriesData = series.some((item) =>
    points.some((point) => {
      const value = point[item.key];
      return typeof value === "number" && Number.isFinite(value);
    }),
  );

  if (points.length === 0 || series.length === 0 || !hasSeriesData) {
    return <p className="ess-detail__empty">{emptyMessage}</p>;
  }

  const rootClassName = ["ess-modern-line-chart", className].filter(Boolean).join(" ");

  return (
    <div className={rootClassName}>
      <p className="ess-modern-line-chart__hint">
        Clique em um ano na legenda para ocultar ou exibir a linha.
      </p>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <LineChart
          data={points}
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
            interval={0}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--ess-text-muted)" }}
            tickFormatter={(value: number) => formatValue(value)}
            axisLine={false}
            tickLine={false}
            width={76}
          />
          <Tooltip
            formatter={(value, name) => {
              if (value == null || value === "") return ["—", String(name)];
              const numeric = typeof value === "number" ? value : Number(value);
              return [
                Number.isFinite(numeric) ? formatValue(numeric) : "—",
                String(name),
              ];
            }}
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
            wrapperStyle={{
              color: "var(--ess-text)",
              fontSize: 12,
              cursor: "pointer",
            }}
            onClick={(entry) => {
              const key = String(entry.dataKey ?? "");
              if (!key) return;
              setHiddenKeys((current) => toggleHiddenSeriesKey(current, key));
            }}
            formatter={(value, entry) => {
              const key = String(entry.dataKey ?? "");
              const inactive = hiddenKeys.has(key);
              return (
                <span
                  className={
                    inactive
                      ? "ess-modern-line-chart__legend-item ess-modern-line-chart__legend-item--hidden"
                      : "ess-modern-line-chart__legend-item"
                  }
                >
                  {value}
                </span>
              );
            }}
          />
          {series.map((item, index) => {
            const stroke = item.color ?? SERIES_COLORS[index % SERIES_COLORS.length];
            const hidden = hiddenKeys.has(item.key);
            return (
              <Line
                key={item.key}
                type="monotone"
                dataKey={item.key}
                name={item.label}
                stroke={stroke}
                strokeWidth={index === series.length - 1 ? 3 : 2}
                hide={hidden}
                connectNulls={false}
                dot={{
                  r: 3,
                  fill: "var(--ess-surface)",
                  stroke,
                  strokeWidth: 2,
                }}
                activeDot={{
                  r: 5,
                  fill: stroke,
                  stroke: "var(--ess-surface)",
                  strokeWidth: 2,
                }}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
