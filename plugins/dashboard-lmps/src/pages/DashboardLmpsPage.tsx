import { useEffect, useMemo, useState } from "react";
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
  Legend,
} from "recharts";

import { KpiCard } from "../components/KpiCard";
import { ChartCard } from "../components/ChartCard";
import { FilterBar } from "../components/FilterBar";
import { DataTableSection } from "../components/DataTableSection";
import type { DataTableColumn } from "../components/DataTable";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { CHART_COLORS } from "../constants/chartColors";
import { useLmpsDashboard } from "../hooks/useLmpsDashboard";
import type { LmpDashboardItem } from "../types/lmp";

const PRIMARY_CHART_COLOR = "#089bdb";
const SECONDARY_CHART_COLOR = "#003866";

const PIE_CHART_HEIGHT = 320;
const PIE_OUTER_RADIUS = 110;
const BAR_CHART_HEIGHT = 320;
const LINE_CHART_HEIGHT = 380;
const CHART_FONT_SIZE = 14;

const AXIS_TICK_PROPS = { fontSize: CHART_FONT_SIZE };
const TOOLTIP_STYLE = { fontSize: CHART_FONT_SIZE };
const LEGEND_STYLE = { fontSize: CHART_FONT_SIZE };

function formatDate(value?: string | null): string {
  if (!value || value.length !== 8) return "-";

  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);

  return `${day}/${month}/${year}`;
}

function formatDateToInput(value?: string | null): string {
  if (!value || value.length !== 8) return "";
  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);
  return `${year}-${month}-${day}`;
}

function getTodayInputValue(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseDateNumber(value?: string | null): number {
  if (!value) return 0;

  const normalized = value.replaceAll("-", "");
  if (normalized.length !== 8) return 0;

  const parsed = Number(normalized);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "-";
}

function matchesListingType(
  item: LmpDashboardItem,
  listingType: string
): boolean {
  if (listingType === "Todos") return true;

  const kind = item.listing_kind;
  if (listingType === "Amostra") return kind === "AMOSTRA";
  if (listingType === "LMP") return kind === "LMP";
  if (listingType === "Outro") return kind === "OUTRO";
  return true;
}

function matchesDashboardStatus(
  item: LmpDashboardItem,
  statusFilter: string
): boolean {
  if (statusFilter === "Todos") return true;
  return item.status === statusFilter;
}

function matchesDashboardFilters(
  item: LmpDashboardItem,
  listingType: string,
  statusFilter: string
): boolean {
  return (
    matchesListingType(item, listingType) &&
    matchesDashboardStatus(item, statusFilter)
  );
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
    year: "2-digit",
  });
}

function renderPieLabel({
  name,
  percent,
}: {
  name?: string;
  percent?: number;
}) {
  if (!name || percent == null) return "";
  return `${name} ${(percent * 100).toFixed(0)}%`;
}

export function DashboardLmpsPage() {
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState(getTodayInputValue());
  const [branch, setBranch] = useState("");
  const [listingType, setListingType] = useState("Todos");
  const [status, setStatus] = useState("Todos");
  const [didInitializeDateStart, setDidInitializeDateStart] = useState(false);

  const { items, summary, charts, loading, refreshing, error, reload } =
    useLmpsDashboard({
      date_start: dateStart || undefined,
      date_end: dateEnd || undefined,
      branch: branch || undefined,
      listing_type: listingType,
      status,
      autoRefreshMs: 2 * 60 * 1000,
    });

  const dashboardItems = items as LmpDashboardItem[];

  const filteredDashboardItems = useMemo(
    () =>
      dashboardItems.filter((item) =>
        matchesDashboardFilters(item, listingType, status)
      ),
    [dashboardItems, listingType, status]
  );

  const hasData = filteredDashboardItems.length > 0;

  useEffect(() => {
    if (didInitializeDateStart) return;
    if (filteredDashboardItems.length === 0) return;

    const validStartDates = filteredDashboardItems
      .map((item) => item.start_date)
      .filter((value): value is string => Boolean(value && value.length === 8))
      .sort((a, b) => parseDateNumber(a) - parseDateNumber(b));

    const oldestStartDate = validStartDates[0];
    if (!oldestStartDate) return;

    setDateStart(formatDateToInput(oldestStartDate));
    setDidInitializeDateStart(true);
  }, [filteredDashboardItems, didInitializeDateStart]);

  const sortedDashboardItems = useMemo(() => {
    return [...filteredDashboardItems].sort(
      (a, b) => parseDateNumber(b.start_date) - parseDateNumber(a.start_date)
    );
  }, [filteredDashboardItems]);

  const fallbackCharts = useMemo(() => {
    const levelOrder = ["Nível 1", "Nível 2", "Nível 3"];
    const statusOrder = ["Pontual", "Atrasado", "Andamento", "Retornada"];

    const levelData = levelOrder.map((name) => ({
      name,
      value: filteredDashboardItems.filter((item) => item.nivel === name).length,
    }));

    const statusData = statusOrder.map((name) => ({
      name,
      value: filteredDashboardItems.filter((item) => item.status === name).length,
    }));

    const leadByLevel = levelOrder.map((nivel) => {
      const itemsByLevel = filteredDashboardItems.filter(
        (item) => item.nivel === nivel && item.lead_time_util != null
      );

      const avg =
        itemsByLevel.length > 0
          ? itemsByLevel.reduce(
              (acc, item) => acc + (item.lead_time_util ?? 0),
              0
            ) / itemsByLevel.length
          : 0;

      return {
        nivel,
        valor: Number(avg.toFixed(2)),
      };
    });

    const evolutionMap = new Map<
      string,
      {
        periodo: string;
        sortKey: number;
        totalLead: number;
        leadCount: number;
        propostas: number;
      }
    >();

    for (const item of filteredDashboardItems) {
      const periodo = getPeriodo(item.start_date);
      const sortKey = parseDateNumber(item.start_date);

      if (!periodo || !sortKey) continue;

      const current = evolutionMap.get(periodo) ?? {
        periodo,
        sortKey,
        totalLead: 0,
        leadCount: 0,
        propostas: 0,
      };

      current.propostas += 1;

      if (item.lead_time_util != null) {
        current.totalLead += item.lead_time_util;
        current.leadCount += 1;
      }

      if (sortKey < current.sortKey) {
        current.sortKey = sortKey;
      }

      evolutionMap.set(periodo, current);
    }

    const evolutionData = Array.from(evolutionMap.values())
      .sort((a, b) => a.sortKey - b.sortKey)
      .map(({ periodo, totalLead, leadCount, propostas }) => ({
        periodo,
        mediaLead: leadCount ? Number((totalLead / leadCount).toFixed(2)) : 0,
        propostas,
      }));

    return {
      levelData,
      statusData,
      leadByLevel,
      evolutionData,
    };
  }, [filteredDashboardItems]);

  const resolvedCharts = {
    levelData: charts?.levelData ?? fallbackCharts.levelData,
    statusData: charts?.statusData ?? fallbackCharts.statusData,
    leadByLevel: charts?.leadByLevel ?? fallbackCharts.leadByLevel,
    evolutionData: charts?.evolutionData ?? fallbackCharts.evolutionData,
  };

  const tableColumns = useMemo<DataTableColumn<LmpDashboardItem>[]>(
    () => [
      { key: "branch", header: "Filial", render: (row) => row.branch ?? "-" },
      {
        key: "kind",
        header: "Tipo",
        render: (row) => formatListingKind(row.listing_kind),
      },
      { key: "sale", header: "Nº Proposta", render: (row) => row.sale_number },
      {
        key: "desc",
        header: "Descrição",
        className: "lmps-table__col--wide",
        render: (row) => row.sale_description,
      },
      {
        key: "start",
        header: "Data Início",
        render: (row) => formatDate(row.start_date),
      },
      {
        key: "end",
        header: "Data Fim",
        render: (row) => formatDate(row.end_date),
      },
      {
        key: "eng",
        header: "Status Engenharia",
        render: (row) => row.engineering_status ?? "-",
      },
      {
        key: "pi",
        header: "Qtd PI",
        render: (row) => String(row.qtd_pi ?? 0),
      },
      { key: "nivel", header: "Nível", render: (row) => row.nivel },
      {
        key: "sla",
        header: "Dias úteis",
        render: (row) => String(row.dias_uteis_sla),
      },
      {
        key: "limit",
        header: "Data Limite",
        render: (row) => formatDate(row.data_limite),
      },
      {
        key: "lead",
        header: "Lead Time Útil",
        render: (row) => String(row.lead_time_util ?? "-"),
      },
      { key: "status", header: "Status Classificação", render: (row) => row.status },
    ],
    []
  );

  const totalPropostas =
    summary?.total_items ??
    (status !== "Todos" || listingType !== "Todos"
      ? filteredDashboardItems.length
      : summary?.total_lmps ?? 0);

  return (
    <main className="dashboard-lmps dashboard-page">
      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        listingType={listingType}
        status={status}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onListingTypeChange={setListingType}
        onStatusChange={setStatus}
        onRefresh={reload}
      />

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando dashboard de LMPs"
          description="Os dados exibidos estão sendo atualizados com os filtros selecionados."
          variant="compact"
          sticky
        />
      ) : null}

      <section className="lmps-kpi-grid">
        <KpiCard
          title="% LMP Dentro do Prazo"
          value={`${(summary?.percent_dentro_prazo ?? 0).toLocaleString(
            "pt-BR",
            {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }
          )}%`}
          subtitle="Percentual consolidado"
          icon={<CircleGauge size={22} />}
        />
        <KpiCard
          title="Lead Time Médio Útil"
          value={`${(summary?.avg_lead_time ?? 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })} dias`}
          subtitle="Média geral"
          icon={<Clock3 size={22} />}
        />
        <KpiCard
          title="Total de Propostas"
          value={String(totalPropostas)}
          subtitle={
            status !== "Todos" || listingType !== "Todos"
              ? "Registros no filtro atual"
              : "Período filtrado"
          }
          icon={<BarChart3 size={22} />}
        />
      </section>

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando dashboard de LMPs"
          description="Buscando propostas, indicadores e gráficos no TOTVS."
        />
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
                Não foi possível atualizar os dados. Exibindo última carga válida.{" "}
                {error}
              </div>
            </section>
          )}

          <section className="lmps-charts-grid lmps-charts-grid-top">
            <ChartCard title="Contagem por Nível">
              <ResponsiveContainer width="100%" height={PIE_CHART_HEIGHT}>
                <PieChart>
                  <Pie
                    data={resolvedCharts.levelData}
                    cx="50%"
                    cy="50%"
                    outerRadius={PIE_OUTER_RADIUS}
                    dataKey="value"
                    nameKey="name"
                    label={renderPieLabel}
                  >
                    {resolvedCharts.levelData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend wrapperStyle={LEGEND_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Contagem por Status">
              <ResponsiveContainer width="100%" height={PIE_CHART_HEIGHT}>
                <PieChart>
                  <Pie
                    data={resolvedCharts.statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={PIE_OUTER_RADIUS}
                    dataKey="value"
                    nameKey="name"
                    label={renderPieLabel}
                  >
                    {resolvedCharts.statusData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend wrapperStyle={LEGEND_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Média de Lead Time Útil por Nível">
              <ResponsiveContainer width="100%" height={BAR_CHART_HEIGHT}>
                <BarChart data={resolvedCharts.leadByLevel}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="nivel" tick={AXIS_TICK_PROPS} />
                  <YAxis tick={AXIS_TICK_PROPS} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar
                    dataKey="valor"
                    radius={[8, 8, 0, 0]}
                    fill={PRIMARY_CHART_COLOR}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>

          <section className="lmps-charts-grid">
            <ChartCard title="Evolução de Lead Time Útil e Quantidade de Propostas">
              <ResponsiveContainer width="100%" height={LINE_CHART_HEIGHT}>
                <LineChart data={resolvedCharts.evolutionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="periodo" tick={AXIS_TICK_PROPS} />
                  <YAxis yAxisId="left" tick={AXIS_TICK_PROPS} />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={AXIS_TICK_PROPS}
                  />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend wrapperStyle={LEGEND_STYLE} />
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

          <DataTableSection
            title="Registros filtrados"
            columns={tableColumns}
            rows={sortedDashboardItems}
            rowKey={(row) =>
              `${row.branch ?? "sem-filial"}-${row.listing_kind ?? "sem-tipo"}-${row.sale_number}`
            }
            loading={loading && sortedDashboardItems.length === 0}
            refreshing={refreshing}
            emptyMessage="Nenhum registro encontrado para os filtros informados."
            searchPlaceholder="Buscar proposta, descrição, status…"
            getSearchText={(row) =>
              [
                row.branch,
                row.sale_number,
                row.sale_description,
                row.engineering_status,
                row.nivel,
                row.status,
                formatListingKind(row.listing_kind),
              ]
                .filter(Boolean)
                .join(" ")
            }
          />
        </>
      )}
    </main>
  );
}