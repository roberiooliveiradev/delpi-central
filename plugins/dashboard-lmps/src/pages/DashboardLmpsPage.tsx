import { useMemo, useState } from "react";
import { BarChart3, CircleGauge, Clock3 } from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  Legend
} from "recharts";

import { KpiCard } from "../components/KpiCard";
import { ChartCard } from "../components/ChartCard";
import { FilterBar } from "../components/FilterBar";
import { CHART_COLORS } from "../constants/chartColors";
import { useLmps } from "../hooks/useLmps";
import { adaptLmpsToDashboard } from "../adapters/lmpsDashboardAdapter";

type DashboardLmpsPageProps = {
  token?: string;
};

export function DashboardLmpsPage({ token }: DashboardLmpsPageProps) {
  const [dateStart, setDateStart] = useState("2025-07-16");
  const [dateEnd, setDateEnd] = useState("2026-03-13");
  const [status, setStatus] = useState("Todos");

  const { items, loading, refreshing, error, reload } = useLmps({
    token,
    date_start: dateStart || undefined,
    date_end: dateEnd || undefined
  });

  const metrics = useMemo(
    () => adaptLmpsToDashboard(items, status),
    [items, status]
  );

  const hasData = items.length > 0;

  return (
    <main className="dashboard-lmps dashboard-page">
      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        status={status}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onStatusChange={setStatus}
        onRefresh={reload}
      />

      {refreshing && hasData && (
        <section className="lmps-charts-grid">
          <div className="lmps-refreshing-banner">Atualizando dados...</div>
        </section>
      )}

      <section className="lmps-kpi-grid">
        <KpiCard
          title="% LMP Dentro do Prazo"
          value={`${metrics.percentDentroPrazo.toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })}%`}
          subtitle="Percentual consolidado"
          icon={<CircleGauge size={22} />}
        />
        <KpiCard
          title="Lead Time Médio Útil"
          value={`${metrics.avgLeadTime.toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })} dias`}
          subtitle="Média geral"
          icon={<Clock3 size={22} />}
        />
        <KpiCard
          title="Total de Propostas"
          value={String(metrics.totalLmps)}
          subtitle="Período filtrado"
          icon={<BarChart3 size={22} />}
        />
      </section>

      {loading && !hasData ? (
        <section className="lmps-charts-grid">
          <ChartCard title="Carregando">
            <div className="lmps-state-box">Carregando dashboard...</div>
          </ChartCard>
        </section>
      ) : error && !hasData ? (
        <section className="lmps-charts-grid">
          <ChartCard title="Erro">
            <div className="lmps-state-box lmps-state-box-error">{error}</div>
          </ChartCard>
        </section>
      ) : (
        <>
          {error && hasData && (
            <section className="lmps-charts-grid">
              <div className="lmps-state-box lmps-state-box-error">
                Não foi possível atualizar os dados. Exibindo última carga válida. {error}
              </div>
            </section>
          )}

          <section className="lmps-charts-grid lmps-charts-grid-top">
            <ChartCard title="Contagem por Nível">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={metrics.levelData}
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    dataKey="value"
                    nameKey="name"
                    label
                  >
                    {metrics.levelData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Contagem por Status">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={metrics.statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    dataKey="value"
                    nameKey="name"
                    label
                  >
                    {metrics.statusData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Média de Lead Time Útil por Nível">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={metrics.leadByLevel}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="nivel" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="valor" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>

          <section className="lmps-charts-grid">
            <ChartCard title="Evolução de Lead Time Útil e Quantidade de Propostas">
              <ResponsiveContainer width="100%" height={340}>
                <LineChart data={metrics.evolutionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="periodo" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="mediaLead"
                    name="Média Lead Time"
                    strokeWidth={3}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="propostas"
                    name="Nº Propostas"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>
        </>
      )}
    </main>
  );
}