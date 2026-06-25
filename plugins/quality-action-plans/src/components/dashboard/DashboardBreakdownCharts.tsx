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

import { CHART_HEIGHT } from "../../constants/chartColors";
import type { DashboardBreakdowns } from "../../types/actionPlan";
import {
  buildActionTypeBreakdownData,
  buildBreakdownChartData,
} from "../../utils/chartData";
import { ChartCard } from "../ui/ChartCard";

type Props = {
  breakdowns?: DashboardBreakdowns | null;
};

type ChartPoint = {
  name: string;
  fullName?: string;
  value: number;
  fill: string;
};

function BreakdownBarChart({ data }: { data: ChartPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--pac-card-border)" />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" width={132} tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(value, _name, item) => [
            value ?? 0,
            (item?.payload as ChartPoint | undefined)?.fullName ?? "Quantidade",
          ]}
          contentStyle={{
            borderRadius: 12,
            border: "1px solid var(--pac-card-border)",
            background: "var(--pac-card-bg)",
          }}
        />
        <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function EmptyChart({ message }: { message: string }) {
  return <div className="pac-state-box">{message}</div>;
}

export function DashboardBreakdownCharts({ breakdowns }: Props) {
  if (!breakdowns) {
    return null;
  }

  const windowMonths = breakdowns.window_months;
  const rootCauseData = buildBreakdownChartData(breakdowns.by_root_cause);
  const failureModeData = buildBreakdownChartData(breakdowns.by_failure_mode);
  const actionTypeData = buildActionTypeBreakdownData(breakdowns.by_action_type);

  return (
    <div className="pac-charts-grid pac-charts-grid--breakdowns">
      <ChartCard
        title="Por causa raiz"
        hint={`Top categorias nos últimos ${windowMonths} meses.`}
      >
        {rootCauseData.length ? (
          <BreakdownBarChart data={rootCauseData} />
        ) : (
          <EmptyChart message="Sem causas raiz registradas no período." />
        )}
      </ChartCard>

      <ChartCard
        title="Por modo de falha"
        hint={`Recorrência de modos de falha (${windowMonths} meses).`}
      >
        {failureModeData.length ? (
          <BreakdownBarChart data={failureModeData} />
        ) : (
          <EmptyChart message="Sem modos de falha no período." />
        )}
      </ChartCard>

      <ChartCard
        title="Por tipo de ação"
        hint={`Distribuição de ações criadas (${windowMonths} meses).`}
      >
        {actionTypeData.length ? (
          <BreakdownBarChart data={actionTypeData} />
        ) : (
          <EmptyChart message="Sem ações registradas no período." />
        )}
      </ChartCard>
    </div>
  );
}
