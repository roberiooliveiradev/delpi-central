import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const MIN_LABEL_WIDTH = 200;
const MAX_LABEL_WIDTH = 320;
const CHAR_WIDTH_PX = 7.2;
const RANKING_ROW_HEIGHT = 34;

type RankingBarChartProps = {
  data: { name: string; value: number }[];
  colors: string[];
  height?: number;
  formatValue: (value: number) => string;
};

function labelWidthForNames(names: string[]): number {
  const longest = names.reduce((max, name) => Math.max(max, name.length), 0);
  const estimated = Math.ceil(longest * CHAR_WIDTH_PX) + 16;
  return Math.min(MAX_LABEL_WIDTH, Math.max(MIN_LABEL_WIDTH, estimated));
}

export function RankingBarChart({
  data,
  colors,
  height,
  formatValue,
}: RankingBarChartProps) {
  const labelWidth = labelWidthForNames(data.map((row) => row.name));
  const chartHeight = height ?? Math.max(300, data.length * RANKING_ROW_HEIGHT + 48);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ left: 4, right: 12, top: 8, bottom: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
        <XAxis type="number" tickFormatter={(v) => formatValue(Number(v))} />
        <YAxis
          type="category"
          dataKey="name"
          width={labelWidth}
          interval={0}
          tick={{ fontSize: 13, fill: "var(--ds-text)" }}
        />
        <Tooltip formatter={(v) => formatValue(Number(v))} />
        <Bar dataKey="value" radius={[0, 8, 8, 0]} maxBarSize={32}>
          {data.map((_, index) => (
            <Cell key={index} fill={colors[index % colors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
