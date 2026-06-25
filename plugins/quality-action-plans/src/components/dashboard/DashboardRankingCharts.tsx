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
import type { DashboardRankings } from "../../types/actionPlan";
import { buildRankingChartData } from "../../utils/chartData";
import { ChartCard } from "../ui/ChartCard";

type Props = {
  rankings?: DashboardRankings | null;
};

type ChartPoint = {
  name: string;
  fullName?: string;
  value: number;
  openPlans?: number;
  fill: string;
};

function RankingBarChart({ data }: { data: ChartPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--pac-card-border)" />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" width={132} tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(value, _name, item) => {
            const point = item?.payload as ChartPoint | undefined;
            const open = point?.openPlans ?? 0;
            const total = Number(value ?? 0);
            return [`${total} planos (${open} abertos)`, point?.fullName ?? "Total"];
          }}
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

export function DashboardRankingCharts({ rankings }: Props) {
  if (!rankings) {
    return null;
  }

  const windowMonths = rankings.window_months;
  const customerData = buildRankingChartData(rankings.by_customer);
  const productData = buildRankingChartData(rankings.by_product);
  const ownerData = buildRankingChartData(rankings.by_owner);

  return (
    <div className="pac-charts-grid pac-charts-grid--rankings">
      <ChartCard title="Top clientes (NC)" hint={`Mais planos nos últimos ${windowMonths} meses.`}>
        {customerData.length ? (
          <RankingBarChart data={customerData} />
        ) : (
          <EmptyChart message="Sem planos com cliente no período." />
        )}
      </ChartCard>

      <ChartCard title="Top produtos (NC)" hint={`Produtos com mais ocorrências (${windowMonths} meses).`}>
        {productData.length ? (
          <RankingBarChart data={productData} />
        ) : (
          <EmptyChart message="Sem planos com produto no período." />
        )}
      </ChartCard>

      <ChartCard
        title="Top responsáveis"
        hint={`Donos de plano com maior volume (${windowMonths} meses).`}
      >
        {ownerData.length ? (
          <RankingBarChart data={ownerData} />
        ) : (
          <EmptyChart message="Sem responsáveis atribuídos no período." />
        )}
      </ChartCard>
    </div>
  );
}
