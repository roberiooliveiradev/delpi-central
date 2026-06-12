import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartSection } from "./data";
import type { ReposicaoItem } from "../data/api/maintenanceApi";

type ReposicoesGolpesChartProps = {
  reposicoes: ReposicaoItem[];
  loading?: boolean;
};

export function ReposicoesGolpesChart({ reposicoes, loading = false }: ReposicoesGolpesChartProps) {
  const chartData = useMemo(() => {
    return [...reposicoes]
      .sort(
        (first, second) =>
          new Date(first.data_reposicao).getTime() - new Date(second.data_reposicao).getTime(),
      )
      .map((item) => ({
        id: item.reposicao_id,
        label: new Date(item.data_reposicao).toLocaleDateString("pt-BR"),
        golpes: item.golpes,
        peca: item.codigo_peca,
      }));
  }, [reposicoes]);

  if (loading) {
    return (
      <ChartSection title="Golpes por reposição">
        <p className="dm-chart-empty">Carregando histórico…</p>
      </ChartSection>
    );
  }

  if (chartData.length === 0) {
    return null;
  }

  return (
    <ChartSection title="Golpes por reposição">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--dm-card-border, #334155)" />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value) => [
              Number(value ?? 0).toLocaleString("pt-BR"),
              "Golpes",
            ]}
            labelFormatter={(label, payload) => {
              const peca = payload?.[0]?.payload?.peca;
              return peca ? `${label} — ${peca}` : label;
            }}
          />
          <Line
            type="monotone"
            dataKey="golpes"
            stroke="var(--dm-accent, #089bdb)"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartSection>
  );
}
