import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ClosingRateData } from "../../../types/analytics";

type AnalyticsFunnelChartProps = {
  closingRate: ClosingRateData | null;
};

export function AnalyticsFunnelChart({ closingRate }: AnalyticsFunnelChartProps) {
  if (!closingRate) {
    return <p className="cm-muted">Sem dados de conversão no período.</p>;
  }

  const data = [
    { stage: "Propostas", value: closingRate.qtd_proposals ?? 0 },
    { stage: "Ganhas", value: closingRate.qtd_won ?? 0 },
  ];

  return (
    <div className="cm-chart-wrap" style={{ width: "100%", height: 240 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 16, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" allowDecimals={false} />
          <YAxis type="category" dataKey="stage" width={90} />
          <Tooltip />
          <Bar dataKey="value" name="Quantidade" fill="var(--chart-1, #089bdb)" radius={4} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
