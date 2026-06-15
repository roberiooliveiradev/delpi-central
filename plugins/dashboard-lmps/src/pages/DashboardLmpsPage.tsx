import { useCallback, useEffect, useMemo, useState } from "react";
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
import { ChartToolbar } from "../components/ChartToolbar";
import { FilterBar } from "../components/FilterBar";
import { DataTableSection } from "../components/DataTableSection";
import type { DataTableColumn } from "../components/DataTable";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { CHART_COLORS } from "../constants/chartColors";
import { buildLmpDetailPath } from "../constants/routes";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useClientTableSort } from "../hooks/useClientTableSort";
import { useLmpsDashboard } from "../hooks/useLmpsDashboard";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import type { ChartGranularity } from "../types/chart";
import type { LmpDashboardItem } from "../types/lmp";
import { buildLmpFallbackCharts, parseLmpDateNumber } from "../utils/lmpCharts";
import {
  formatPeriodLabel,
} from "../utils/dates";
import { formatGoalSubtitle } from "../utils/goalDisplay";
import { exportLmpsDashboardCsv } from "../utils/exportLmpsCsv";
import { aggregateLmpEvolutionSeries } from "../utils/lmpEvolutionSeries";
import { suggestGranularity } from "../utils/periodBuckets";
import { readLmpsFilters, type LmpsFilterUrlState } from "../utils/filterUrl";
import { navigateLmps } from "../utils/navigation";

const PRIMARY_CHART_COLOR = "#089bdb";
const SECONDARY_CHART_COLOR = "#003866";

const PIE_CHART_HEIGHT = 320;
const PIE_OUTER_RADIUS = 110;
const BAR_CHART_HEIGHT = 320;
const LINE_CHART_HEIGHT = 380;
const CHART_FONT_SIZE = 14;
const FILTER_DEBOUNCE_MS = 400;

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

function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "-";
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

export function DashboardLmpsPage({ pathname }: { pathname?: string } = {}) {
  const initialFilters = useMemo(() => readLmpsFilters(), [pathname]);
  const [dateStart, setDateStart] = useState(initialFilters.dateStart);
  const [dateEnd, setDateEnd] = useState(initialFilters.dateEnd);
  const [branch, setBranch] = useState(initialFilters.branch);
  const [listingType, setListingType] = useState(initialFilters.listingType);
  const [status, setStatus] = useState(initialFilters.status);
  const [granularity, setGranularity] = useState<ChartGranularity>("month");

  const filterState = useMemo<LmpsFilterUrlState>(
    () => ({
      dateStart,
      dateEnd,
      branch,
      listingType,
      status,
    }),
    [dateStart, dateEnd, branch, listingType, status]
  );

  const handleRowClick = useCallback(
    (row: LmpDashboardItem) => {
      navigateLmps(
        buildLmpDetailPath(row.sale_number, {
          ...filterState,
          branch: row.branch || filterState.branch,
        })
      );
    },
    [filterState]
  );

  const debouncedDateStart = useDebouncedValue(dateStart, FILTER_DEBOUNCE_MS);
  const debouncedDateEnd = useDebouncedValue(dateEnd, FILTER_DEBOUNCE_MS);

  const {
    items,
    itemsTotal,
    summary,
    charts,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  } = useLmpsDashboard({
    date_start: debouncedDateStart || undefined,
    date_end: debouncedDateEnd || undefined,
    branch: branch || undefined,
    listing_type: listingType,
    status,
  });

  const dashboardItems = items as LmpDashboardItem[];
  const tableSort = useClientTableSort({
    defaultSortKey: "start",
    defaultSortDirection: "desc",
  });
  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const chartItems = useMemo(
    () =>
      [...dashboardItems].sort(
        (a, b) => parseLmpDateNumber(b.start_date) - parseLmpDateNumber(a.start_date)
      ),
    [dashboardItems]
  );

  const hasData = chartItems.length > 0 || summary !== null;
  const isBusy = loading || refreshing;
  const initialLoadingProgress = useLoadingProgress(loading, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing, requestProgress);

  const fallbackCharts = useMemo(
    () => buildLmpFallbackCharts(chartItems),
    [chartItems]
  );

  const resolvedCharts = useMemo(
    () => ({
      levelData: charts?.levelData ?? fallbackCharts.levelData,
      statusData: charts?.statusData ?? fallbackCharts.statusData,
      leadByLevel: charts?.leadByLevel ?? fallbackCharts.leadByLevel,
    }),
    [charts, fallbackCharts]
  );

  const hasCharts =
    resolvedCharts.levelData.some((d) => d.value > 0) ||
    resolvedCharts.statusData.some((d) => d.value > 0);

  useEffect(() => {
    if (!dateStart || !dateEnd) return;
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const evolutionChartData = useMemo(
    () =>
      aggregateLmpEvolutionSeries(
        chartItems,
        dateStart || undefined,
        dateEnd || undefined,
        granularity
      ),
    [chartItems, dateStart, dateEnd, granularity]
  );

  const tableColumns = useMemo<DataTableColumn<LmpDashboardItem>[]>(
    () => [
      {
        key: "branch",
        header: "Filial",
        sortable: true,
        sortValue: (row) => row.branch ?? "",
        render: (row) => row.branch ?? "-",
      },
      {
        key: "kind",
        header: "Tipo",
        sortable: true,
        sortValue: (row) => row.listing_kind ?? "",
        render: (row) => formatListingKind(row.listing_kind),
      },
      {
        key: "sale",
        header: "Nº Proposta",
        sortable: true,
        sortValue: (row) => row.sale_number,
        render: (row) => row.sale_number,
      },
      {
        key: "desc",
        header: "Descrição",
        className: "lmps-table__col--wide",
        sortable: true,
        sortValue: (row) => row.sale_description,
        render: (row) => row.sale_description,
      },
      {
        key: "start",
        header: "Data Início",
        sortable: true,
        sortValue: (row) => parseLmpDateNumber(row.start_date),
        render: (row) => formatDate(row.start_date),
      },
      {
        key: "end",
        header: "Data Fim",
        sortable: true,
        sortValue: (row) => parseLmpDateNumber(row.end_date),
        render: (row) => formatDate(row.end_date),
      },
      {
        key: "eng",
        header: "Status Engenharia",
        sortable: true,
        sortValue: (row) => row.engineering_status ?? "",
        render: (row) => row.engineering_status ?? "-",
      },
      {
        key: "pi",
        header: "Qtd PI",
        sortable: true,
        sortValue: (row) => row.qtd_pi ?? 0,
        render: (row) => String(row.qtd_pi ?? 0),
      },
      {
        key: "nivel",
        header: "Nível",
        sortable: true,
        sortValue: (row) => Number.parseInt(row.nivel.replace(/\D/g, ""), 10) || 0,
        render: (row) => row.nivel,
      },
      {
        key: "sla",
        header: "Dias úteis",
        sortable: true,
        sortValue: (row) => row.dias_uteis_sla,
        render: (row) => String(row.dias_uteis_sla),
      },
      {
        key: "limit",
        header: "Data Limite",
        sortable: true,
        sortValue: (row) => parseLmpDateNumber(row.data_limite),
        render: (row) => formatDate(row.data_limite),
      },
      {
        key: "lead",
        header: "Lead Time Útil",
        sortable: true,
        sortValue: (row) => row.lead_time_util,
        render: (row) => String(row.lead_time_util ?? "-"),
      },
      {
        key: "status",
        header: "Status Classificação",
        sortable: true,
        sortValue: (row) => row.status,
        render: (row) => row.status,
      },
    ],
    []
  );

  const totalPropostas =
    summary?.total_items ?? summary?.total_lmps ?? (itemsTotal || dashboardItems.length);

  const handleExportCsv = useCallback(() => {
    exportLmpsDashboardCsv(chartItems, {
      dateStart: dateStart || undefined,
      dateEnd: dateEnd || undefined,
    });
  }, [chartItems, dateStart, dateEnd]);

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
        onExport={handleExportCsv}
        exportDisabled={dashboardItems.length === 0 || loading}
      />

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando dashboard de LMPs"
          description="Os dados exibidos estão sendo atualizados com os filtros selecionados."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      <section className="lmps-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="% LMP Dentro do Prazo"
          value={`${(summary?.percent_dentro_prazo ?? 0).toLocaleString(
            "pt-BR",
            {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }
          )}%`}
          subtitle={formatGoalSubtitle(periodLabel, summary, (v) =>
            `${v.toLocaleString("pt-BR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}%`,
          )}
          icon={<CircleGauge size={22} />}
        />
        <KpiCard
          title="Lead Time Médio Útil"
          value={`${(summary?.avg_lead_time ?? 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })} dias`}
          subtitle="Média no período"
          icon={<Clock3 size={22} />}
        />
        <KpiCard
          title="Total de Propostas"
          value={String(totalPropostas)}
          subtitle={
            status !== "Todos" || listingType !== "Todos"
              ? "Registros no filtro atual"
              : periodLabel
          }
          icon={<BarChart3 size={22} />}
        />
      </section>

      {loading ? (
        <LoadingActivityCard
          title="Carregando dashboard de LMPs"
          description={
            requestProgress.completed === 0
              ? "Buscando indicadores no TOTVS…"
              : requestProgress.completed === 1
              ? "Indicadores carregados. Buscando gráficos…"
              : "Gráficos carregados. Buscando registros da tabela…"
          }
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      {error && !hasData && !loading ? (
        <section className="lmps-charts-grid">
          <ChartCard title="Erro">
            <div className="lmps-state-box lmps-state-box-error">{error}</div>
          </ChartCard>
        </section>
      ) : null}

      {error && hasData && !loading ? (
        <section className="lmps-charts-grid">
          <div className="lmps-state-box lmps-state-box-error">
            Não foi possível atualizar os dados. Exibindo última carga válida.{" "}
            {error}
          </div>
        </section>
      ) : null}

      {hasCharts ? (
        <>
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
                  <ChartToolbar
                    idPrefix="lmps-evolution"
                    granularity={granularity}
                    onGranularityChange={setGranularity}
                  />
                  {evolutionChartData.length === 0 && !loading ? (
                    <div className="lmps-state-box">
                      Sem dados para o agrupamento selecionado.
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height={LINE_CHART_HEIGHT}>
                      <LineChart data={evolutionChartData}>
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
                  )}
                </ChartCard>
              </section>
            </>
          ) : null}

      <DataTableSection
        title="Registros filtrados"
        hint={periodLabel}
        columns={tableColumns}
        rows={dashboardItems}
        rowKey={(row) =>
          `${row.branch ?? "sem-filial"}-${row.listing_kind ?? "sem-tipo"}-${row.sale_number}`
        }
        loading={loading && dashboardItems.length === 0}
        refreshing={refreshing}
        clientSort={{
          sortKey: tableSort.sortKey,
          sortDirection: tableSort.sortDirection,
          onSortChange: tableSort.handleSortChange,
        }}
        emptyMessage={
          loading
            ? "Carregando registros…"
            : "Nenhum registro encontrado para os filtros informados."
        }
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
        onRowClick={handleRowClick}
        getRowClassName={() => "lmps-table__row--clickable"}
      />
    </main>
  );
}
