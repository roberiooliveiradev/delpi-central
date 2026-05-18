import {
  Line,
  LineChart,
  ResponsiveContainer,
  YAxis,
} from "recharts";

import { CHART_COLORS } from "../constants/chartColors";

type PpmSparklineProps = {
  data: { periodo: string; ppm: number }[];
  color?: string;
  loading?: boolean;
};

export function PpmSparkline({
  data,
  color = CHART_COLORS[0],
  loading = false,
}: PpmSparklineProps) {
  if (loading) {
    return <div className="dq-sparkline dq-sparkline--loading" aria-hidden="true" />;
  }

  if (data.length === 0) {
    return (
      <div className="dq-sparkline dq-sparkline--empty" aria-hidden="true">
        Sem histórico no período
      </div>
    );
  }

  return (
    <div className="dq-sparkline" aria-hidden="true">
      <ResponsiveContainer width="100%" height={56}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
          <YAxis domain={["auto", "auto"]} hide />
          <Line
            type="monotone"
            dataKey="ppm"
            stroke={color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
