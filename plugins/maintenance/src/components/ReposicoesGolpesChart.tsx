import { useMemo } from "react";
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

import { ChartSection } from "./data";
import type { ReposicaoItem } from "../data/api/maintenanceApi";
import { formatCodigoDescricao } from "../utils/pecaOptions";

type ReposicoesGolpesChartProps = {
  reposicoes: ReposicaoItem[];
  pecaLabels?: Record<string, string>;
  loading?: boolean;
};

const PECA_LINE_COLORS = [
  "#089bdb",
  "#22c55e",
  "#f59e0b",
  "#a855f7",
  "#ef4444",
  "#06b6d4",
  "#eab308",
  "#ec4899",
];

function formatEventLabel(value: string): string {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ReposicoesGolpesChart({
  reposicoes,
  pecaLabels = {},
  loading = false,
}: ReposicoesGolpesChartProps) {
  const { chartData, pecaSeries } = useMemo(() => {
    const sorted = [...reposicoes].sort(
      (first, second) =>
        new Date(first.data_reposicao).getTime() - new Date(second.data_reposicao).getTime(),
    );
    const pecas = [...new Set(sorted.map((item) => item.codigo_peca))].sort((first, second) =>
      first.localeCompare(second, "pt-BR"),
    );

    const chartData = sorted.map((item) => {
      const row: Record<string, string | number | null> = {
        label: formatEventLabel(item.data_reposicao),
        eventId: item.reposicao_id,
      };
      for (const peca of pecas) {
        row[peca] = item.codigo_peca === peca ? item.golpes : null;
      }
      return row;
    });

    const pecaSeries = pecas.map((codigo, index) => ({
      codigo,
      name: codigo,
      color: PECA_LINE_COLORS[index % PECA_LINE_COLORS.length],
    }));

    return { chartData, pecaSeries };
  }, [reposicoes]);

  if (loading) {
    return (
      <ChartSection title="Golpes por reposição">
        <p className="dm-chart-empty">Carregando histórico…</p>
      </ChartSection>
    );
  }

  if (chartData.length === 0 || pecaSeries.length === 0) {
    return null;
  }

  return (
    <ChartSection title="Golpes por reposição">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 12, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--dm-card-border, #334155)" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) => {
              const codigo = String(name);
              const descricao = pecaLabels[codigo];
              return [
                Number(value ?? 0).toLocaleString("pt-BR"),
                descricao ? formatCodigoDescricao(codigo, descricao) : codigo,
              ];
            }}
            labelFormatter={(label) => label}
          />
          <Legend />
          {pecaSeries.map((series) => (
            <Line
              key={series.codigo}
              type="monotone"
              dataKey={series.codigo}
              name={series.name}
              stroke={series.color}
              strokeWidth={2}
              dot={{ r: 3, strokeWidth: 2 }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartSection>
  );
}
