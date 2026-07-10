import { useCallback, useMemo, useState } from "react";
import { useChartGranularitySelection } from "@delpi/plugin-ui/index";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BarChart3, CircleGauge, Clock3 } from "lucide-react";

import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { DataSourceBanner } from "../components/DataSourceBanner";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { EngineeringStatusAlerts } from "../components/EngineeringStatusAlerts";
import { LmpFilters } from "../components/LmpFilters";
import { CHART_COLORS } from "../constants/chartColors";
import { ENGINEERING_ROUTES } from "../constants/routes";
import { useEngineeringFilters } from "../hooks/useEngineeringFilters";
import { useLmpsDashboard } from "../hooks/useLmpsDashboard";
import type { LmpDashboardItem } from "../types/lmp";
import { buildLmpFallbackCharts } from "../utils/lmpCharts";
import { aggregateLmpEvolutionSeries } from "../utils/lmpEvolutionSeries";
import {
  buildLmpDashboardRowKey,
  formatCycleIndex,
  formatDashboardRevision,
  formatListingKind,
  formatLmpApiDate,
  parseLmpDateNumber,
} from "../utils/lmpDisplay";
import { formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { resolveApiBranch } from "../utils/branchClientFilters";
import {
  matchesMultiFilter,
  needsClientSideMultiFilter,
  resolveScalarApiFilter,
} from "../utils/lmpClientFilters";
import { formatDecimal, formatInteger } from "../utils/format";
import { ENGINEERING_HELP_TOOLTIPS } from "../content/helpTooltips";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode, normalizeOperationalUnitCode } from "../utils/operationalUnitLabels";

const PIE_HEIGHT = 320;
const PIE_RADIUS = 110;
const BAR_HEIGHT = 320;
const LINE_HEIGHT = 380;
const PRIMARY_COLOR = "#089bdb";
const SECONDARY_COLOR = "#003866";

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

type LmpPageProps = { pathname?: string };

export function LmpPage({ pathname }: LmpPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    filterState,
  } = useEngineeringFilters();

  const { granularity, setGranularity } = useChartGranularitySelection(
    dateStart,
    dateEnd,
  );

  const [listingTypes, setListingTypes] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [tableSearch, setTableSearch] = useState("");

  const apiListingType = resolveScalarApiFilter(listingTypes, "Todos");
  const apiStatus = resolveScalarApiFilter(statuses, "Todos");
  const clientFilterListing = needsClientSideMultiFilter(listingTypes);
  const clientFilterStatus = needsClientSideMultiFilter(statuses);

  const {
    items: rawItems,
    summary,
    charts,
    total,
    page,
    pageSize,
    setPage,
    setPageSize,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  } = useLmpsDashboard({
    date_start: dateStart || undefined,
    date_end: dateEnd || undefined,
    branch: resolveApiBranch(branches),
    listing_type: apiListingType,
    status: apiStatus,
  });

  const items = useMemo(() => {
    if (!clientFilterListing && !clientFilterStatus) return rawItems;
    return rawItems.filter((row) => {
      const kind = row.listing_kind ?? "";
      const statusValue = row.status ?? "";
      return (
        matchesMultiFilter(kind, listingTypes) &&
        matchesMultiFilter(statusValue, statuses)
      );
    });
  }, [
    clientFilterListing,
    clientFilterStatus,
    listingTypes,
    rawItems,
    statuses,
  ]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const sortedItems = useMemo(
    () =>
      [...items].sort(
        (a, b) => parseLmpDateNumber(b.start_date) - parseLmpDateNumber(a.start_date)
      ),
    [items]
  );

  const fallbackCharts = useMemo(
    () => buildLmpFallbackCharts(sortedItems),
    [sortedItems]
  );

  const resolvedCharts = useMemo(
    () => ({
      levelData: charts?.levelData ?? fallbackCharts.levelData,
      statusData: charts?.statusData ?? fallbackCharts.statusData,
      leadByLevel: charts?.leadByLevel ?? fallbackCharts.leadByLevel,
    }),
    [charts, fallbackCharts]
  );

  const evolutionChartData = useMemo(
    () => aggregateLmpEvolutionSeries(sortedItems, dateStart, dateEnd, granularity),
    [sortedItems, dateStart, dateEnd, granularity]
  );

  const totalPropostas =
    summary?.total_items ??
    summary?.total_lmps ??
    sortedItems.length;

  const tableRows = useMemo(() => {
    const query = tableSearch.trim().toLowerCase();
    if (!query) return sortedItems;

    return sortedItems.filter((row) =>
      [
        formatOperationalUnitCode(row.branch, ""),
        row.sale_number,
        row.sale_description,
        row.engineering_status,
        row.nivel,
        row.status,
        formatListingKind(row.listing_kind),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [sortedItems, tableSearch]);

  const handleLmpRowClick = useCallback(
    (row: LmpDashboardItem) => {
      if (!row.sale_number) return;
      const params = new URLSearchParams();
      if (row.branch) {
        params.set("branch", normalizeOperationalUnitCode(row.branch));
      }
      if (dateStart) params.set("date_start", dateStart);
      if (dateEnd) params.set("date_end", dateEnd);
      const query = params.toString();
      const target = `/apps/dashboard-lmps/ov/${encodeURIComponent(row.sale_number)}${
        query ? `?${query}` : ""
      }`;
      window.location.assign(target);
    },
    [dateStart, dateEnd]
  );

  const columns = useMemo<DataTableColumn<LmpDashboardItem>[]>(
    () => [
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        headerHint: ENGINEERING_HELP_TOOLTIPS.table.branch,
        render: (row) => formatOperationalUnitCode(row.branch),
      },
      {
        key: "kind",
        header: "Tipo",
        render: (row) => formatListingKind(row.listing_kind),
      },
      { key: "sale", header: "Nº proposta", render: (row) => row.sale_number },
      {
        key: "revision",
        header: "Revisão",
        className: "ds-table__col--compact",
        render: (row) => formatDashboardRevision(row),
      },
      {
        key: "cycle",
        header: "Ciclo",
        className: "ds-table__col--numeric",
        render: (row) => formatCycleIndex(row.cycle_index),
      },
      {
        key: "desc",
        header: "Descrição",
        className: "ds-table__col--wide",
        render: (row) => row.sale_description || "—",
      },
      {
        key: "start",
        header: "Início",
        render: (row) => formatLmpApiDate(row.start_date),
      },
      {
        key: "end",
        header: "Fim",
        render: (row) => formatLmpApiDate(row.end_date),
      },
      {
        key: "eng",
        header: "Status eng.",
        render: (row) => row.engineering_status ?? "—",
      },
      {
        key: "pi",
        header: "Qtd PI",
        className: "ds-table__col--numeric",
        render: (row) => String(row.qtd_pi ?? 0),
      },
      { key: "nivel", header: "Nível", render: (row) => row.nivel },
      {
        key: "sla",
        header: "Dias úteis",
        className: "ds-table__col--numeric",
        render: (row) => String(row.dias_uteis_sla),
      },
      {
        key: "limit",
        header: "Data limite",
        render: (row) => formatLmpApiDate(row.data_limite),
      },
      {
        key: "lead",
        header: "Lead time útil",
        className: "ds-table__col--numeric",
        render: (row) =>
          row.lead_time_util != null
            ? formatDecimal(row.lead_time_util, 2)
            : "—",
      },
      { key: "status", header: "Classificação", render: (row) => row.status },
    ],
    []
  );

  const isBusy = loading || refreshing;
  const hasData = summary !== null || total > 0;
  const hasCharts =
    resolvedCharts.levelData.some((d) => d.value > 0) ||
    resolvedCharts.statusData.some((d) => d.value > 0);

  return (
    <div className="dashboard-engineering dashboard-page">
      <FilterBar
        title="LMPs no prazo"
        subtitle="% de projetos/LMPs dentro do prazo e lead time útil (TOTVS)"
        currentPath={pathname ?? ENGINEERING_ROUTES.lmp}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner variant="lmp" />
      <LmpFilters
        listingTypes={listingTypes}
        statuses={statuses}
        onListingTypesChange={setListingTypes}
        onStatusesChange={setStatuses}
      />
      <EngineeringStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando LMPs"
        refreshDescription="Recalculando indicadores e gráficos com os filtros atuais."
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="% LMP dentro do prazo"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.lmpOnTime}
          value={formatDashboardMetricValue(
            summary?.percent_dentro_prazo,
            summary,
          )}
          {...buildKpiGoalPresentation(
            periodLabel,
            summary,
            undefined,
            { realizedValue: summary?.percent_dentro_prazo },
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Lead time médio útil"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.avgLeadTimeUseful}
          value={`${formatDecimal(summary?.avg_lead_time, 2)} dias`}
          contextLabel="Média no período"
          icon={<Clock3 size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Total de propostas"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.totalProposals}
          value={formatInteger(totalPropostas)}
          contextLabel={
            listingTypes.length > 0 || statuses.length > 0
              ? "Registros no filtro"
              : "Período filtrado"
          }
          icon={<BarChart3 size={22} />}
          loading={isBusy}
        />
      </section>

      {hasCharts ? (
        <>
          <section className="ds-charts-grid">
            <ChartCard title="Contagem por nível" hint={periodLabel}>
              <ResponsiveContainer width="100%" height={PIE_HEIGHT}>
                <PieChart>
                  <Pie
                    data={resolvedCharts.levelData}
                    cx="50%"
                    cy="50%"
                    outerRadius={PIE_RADIUS}
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
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Contagem por status" hint={periodLabel}>
              <ResponsiveContainer width="100%" height={PIE_HEIGHT}>
                <PieChart>
                  <Pie
                    data={resolvedCharts.statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={PIE_RADIUS}
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
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Lead time médio por nível" hint="Dias úteis">
              <ResponsiveContainer width="100%" height={BAR_HEIGHT}>
                <BarChart data={resolvedCharts.leadByLevel}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="nivel" tick={{ fontSize: 11 }} interval={0} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar
                    dataKey="valor"
                    radius={[8, 8, 0, 0]}
                    fill={PRIMARY_COLOR}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </section>

          <section className="ds-chart-section">
            <ChartCard
              title="Evolução de lead time e propostas"
              hint="Por data de início da proposta"
            >
              <ChartToolbar
                idPrefix="lmp-evolution"
                granularity={granularity}
                onGranularityChange={setGranularity}
              />
              {evolutionChartData.length === 0 && !loading ? (
                <p className="ds-state-box">Sem dados para o agrupamento selecionado.</p>
              ) : (
              <ResponsiveContainer width="100%" height={LINE_HEIGHT}>
                <LineChart data={evolutionChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="mediaLead"
                    name="Média lead time"
                    stroke={PRIMARY_COLOR}
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="propostas"
                    name="Nº propostas"
                    stroke={SECONDARY_COLOR}
                    strokeWidth={3}
                    dot={{ r: 4 }}
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
        titleHint={ENGINEERING_HELP_TOOLTIPS.table.section}
        hint={`${periodLabel} · clique na linha para abrir o detalhe da proposta`}
        columns={columns}
        rows={tableRows}
        rowKey={buildLmpDashboardRowKey}
        loading={loading && items.length === 0}
        refreshing={refreshing}
        onRowClick={handleLmpRowClick}
        emptyMessage={
          loading
            ? "Carregando registros…"
            : "Nenhum registro encontrado para os filtros informados."
        }
        searchPlaceholder="Buscar proposta, descrição, status…"
        searchHint={ENGINEERING_HELP_TOOLTIPS.table.search}
        serverSearch={{
          value: tableSearch,
          onChange: setTableSearch,
        }}
        serverPagination={{
          page,
          pageSize,
          total,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
        }}
      />
    </div>
  );
}