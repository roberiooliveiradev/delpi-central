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
import { useLmpsDashboard } from "../hooks/useLmpsDashboard";
import type { LmpDashboardItem } from "../types/lmp";

type DashboardLmpsPageProps = {
  token?: string;
};

const PRIMARY_CHART_COLOR = "#089bdb";
const SECONDARY_CHART_COLOR = "#003866";

function formatDate(value?: string | null): string {
  if (!value || value.length !== 8) return "-";

  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);

  return `${day}/${month}/${year}`;
}

function getPeriodo(dateValue?: string | null): string | null {
  if (!dateValue || dateValue.length !== 8) return null;

  const year = Number(dateValue.slice(0, 4));
  const month = Number(dateValue.slice(4, 6));
  const day = Number(dateValue.slice(6, 8));

  if (!year || !month || !day) return null;

  const date = new Date(year, month - 1, day);

  return date.toLocaleDateString("pt-BR", {
    month: "short",
    year: "2-digit"
  });
}

export function DashboardLmpsPage({ token }: DashboardLmpsPageProps) {
  const [dateStart, setDateStart] = useState("2025-07-16");
  const [dateEnd, setDateEnd] = useState("2026-03-13");
  const [status, setStatus] = useState("Todos");

  const { items, summary, charts, loading, refreshing, error, reload } =
    useLmpsDashboard({
      token,
      date_start: dateStart || undefined,
      date_end: dateEnd || undefined,
      status
    });

  const dashboardItems = items as LmpDashboardItem[];
  const hasData = dashboardItems.length > 0;

  const fallbackCharts = useMemo(() => {
    const levelOrder = ["Nível 1", "Nível 2", "Nível 3"];
    const statusOrder = ["Pontual", "Atrasado", "Andamento"];

    const levelData = levelOrder.map((name) => ({
      name,
      value: dashboardItems.filter((item) => item.nivel === name).length
    }));

    const statusData = statusOrder.map((name) => ({
      name,
      value: dashboardItems.filter((item) => item.status === name).length
    }));

    const leadByLevel = levelOrder.map((nivel) => {
      const itemsByLevel = dashboardItems.filter(
        (item) => item.nivel === nivel && item.lead_time_util != null
      );

      const avg =
        itemsByLevel.length > 0
          ? itemsByLevel.reduce((acc, item) => acc + (item.lead_time_util ?? 0), 0) /
            itemsByLevel.length
          : 0;

      return {
        nivel,
        valor: Number(avg.toFixed(2))
      };
    });

    const evolutionMap = new Map<
      string,
      { totalLead: number; leadCount: number; propostas: number }
    >();

    for (const item of dashboardItems) {
      const periodo = getPeriodo(item.start_date);
      if (!periodo) continue;

      const current = evolutionMap.get(periodo) ?? {
        totalLead: 0,
        leadCount: 0,
        propostas: 0
      };

      current.propostas += 1;

      if (item.lead_time_util != null) {
        current.totalLead += item.lead_time_util;
        current.leadCount += 1;
      }

      evolutionMap.set(periodo, current);
    }

    const evolutionData = Array.from(evolutionMap.entries()).map(([periodo, value]) => ({
      periodo,
      mediaLead: value.leadCount
        ? Number((value.totalLead / value.leadCount).toFixed(2))
        : 0,
      propostas: value.propostas
    }));

    return {
      levelData,
      statusData,
      leadByLevel,
      evolutionData
    };
  }, [dashboardItems]);

  const resolvedCharts = {
    levelData: charts?.levelData ?? fallbackCharts.levelData,
    statusData: charts?.statusData ?? fallbackCharts.statusData,
    leadByLevel: charts?.leadByLevel ?? fallbackCharts.leadByLevel,
    evolutionData: charts?.evolutionData ?? fallbackCharts.evolutionData
  };

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
          value={`${(summary?.percent_dentro_prazo ?? 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })}%`}
          subtitle="Percentual consolidado"
          icon={<CircleGauge size={22} />}
        />
        <KpiCard
          title="Lead Time Médio Útil"
          value={`${(summary?.avg_lead_time ?? 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })} dias`}
          subtitle="Média geral"
          icon={<Clock3 size={22} />}
        />
        <KpiCard
          title="Total de Propostas"
          value={String(summary?.total_lmps ?? 0)}
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
                    data={resolvedCharts.levelData}
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    dataKey="value"
                    nameKey="name"
                    label
                  >
                    {resolvedCharts.levelData.map((entry, index) => (
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
                    data={resolvedCharts.statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    dataKey="value"
                    nameKey="name"
                    label
                  >
                    {resolvedCharts.statusData.map((entry, index) => (
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
                <BarChart data={resolvedCharts.leadByLevel}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="nivel" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="valor" radius={[8, 8, 0, 0]} fill={PRIMARY_CHART_COLOR} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>

          <section className="lmps-charts-grid">
            <ChartCard title="Evolução de Lead Time Útil e Quantidade de Propostas">
              <ResponsiveContainer width="100%" height={340}>
                <LineChart data={resolvedCharts.evolutionData}>
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
                    stroke={PRIMARY_CHART_COLOR}
                    dot={{ r: 4, strokeWidth: 2, fill: "#ffffff" }}
                    activeDot={{ r: 3 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="propostas"
                    name="Nº Propostas"
                    strokeWidth={4}
                    stroke={SECONDARY_CHART_COLOR}
                    dot={{ r: 4, strokeWidth: 2, fill: "#ffffff" }}
                    activeDot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>

          <section className="lmps-charts-grid">
            <ChartCard title="LMPs filtradas">
              <div className="lmps-table-wrapper">
                <table className="lmps-table">
                  <thead>
                    <tr>
                      <th>Nº Proposta</th>
                      <th>Descrição</th>
                      <th>Data Início</th>
                      <th>Data Fim</th>
                      <th>Status Engenharia</th>
                      <th>Qtd PI</th>
                      <th>Nível</th>
                      <th>SLA</th>
                      <th>Data Limite</th>
                      <th>Lead Time Útil</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardItems.length === 0 ? (
                      <tr>
                        <td colSpan={11}>Nenhuma LMP encontrada para os filtros informados.</td>
                      </tr>
                    ) : (
                      dashboardItems.map((item) => (
                        <tr key={item.sale_number}>
                          <td>{item.sale_number}</td>
                          <td>{item.sale_description}</td>
                          <td>{formatDate(item.start_date)}</td>
                          <td>{formatDate(item.end_date)}</td>
                          <td>{item.engineering_status ?? "-"}</td>
                          <td>{item.qtd_pi ?? 0}</td>
                          <td>{item.nivel}</td>
                          <td>{item.dias_uteis_sla}</td>
                          <td>{formatDate(item.data_limite)}</td>
                          <td>{item.lead_time_util ?? "-"}</td>
                          <td>{item.status}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </ChartCard>
          </section>
        </>
      )}
    </main>
  );
}