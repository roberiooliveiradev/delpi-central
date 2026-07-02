import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Clock,
  Coins,
  Lightbulb,
  Percent,
} from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { DateField } from "../../components/DateField";
import { HelpTooltip } from "../../components/HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { KpiCard } from "../../components/KpiCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { ChartGranularityToggle } from "../../components/ChartGranularityToggle";
import { ChartSeriesViewport } from "../../components/ChartSeriesViewport";
import { RankingBarChart } from "../../components/RankingBarChart";
import { CollapsiblePanel } from "../../components/CollapsiblePanel";
import { DashboardToolbarMenu } from "../../components/DashboardToolbarMenu";
import { PageHeader } from "../../components/PageHeader";
import { SegmentToggle } from "../../components/SegmentToggle";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import {
  downloadDashboardCsv,
  downloadDashboardExcel,
  fetchDashboardAlertas,
  fetchDashboardEvolucao,
  fetchDashboardPorFamilia,
  fetchDashboardProcessos,
  fetchDashboardResumo,
  fetchOptions,
  recalcularDashboard,
  type DashboardAlertItem,
  type DashboardEvolucaoItem,
  type DashboardFamiliaItem,
  type DashboardProcessoItem,
  type DashboardResumo,
  type OptionsData,
} from "../../data/api/transformometroApi";
import type { ChartGranularity } from "../../types/chart";
import { CHART_MEASURE_OPTIONS, type ChartMeasure } from "../../types/chartMeasure";
import {
  formatCurrency,
  formatDecimal,
  formatHours,
  formatRoiRatio,
} from "../../utils/format";
import { buildEvolucaoSavingsSeries } from "../../utils/evolucaoChartSeries";
import { useChartSeriesWindow } from "../../hooks/useChartSeriesWindow";
import { currentMonthFilterRange } from "../../utils/dashboardFilters";
import { horasEconomizadasDiaria } from "../../utils/calcRules";
import { suggestGranularity } from "../../utils/periodBuckets";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { buildProcessoPath } from "../../utils/routeParser";
import { filterSetoresByFilial } from "../../utils/setores";
import {
  buildDashboardQueryParams,
  canSelectConsolidatedView,
  defaultDashboardFilialFilter,
} from "../../utils/dashboardViewScope";

const CHART_COLORS = [
  "#1aa7d9",
  "#0b4f80",
  "#4fc3f7",
  "#8a18ff",
  "#2e7d32",
  "#ff9f00",
];
const ECONOMIA_COLOR = "#4fc3f7";
const INVESTIMENTO_COLOR = "#ff6b6b";
const HORAS_COLOR = "#8a18ff";
const CHART_HEIGHT = 300;

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

type Filters = {
  dataInicial: string;
  dataFinal: string;
  filialId: string;
  setorId: string;
};

type DashboardViewMode = "consolidated" | "filial" | "department";

const monthRange = currentMonthFilterRange();
const defaultFilters: Filters = {
  dataInicial: monthRange.dataInicial,
  dataFinal: monthRange.dataFinal,
  filialId: "",
  setorId: "",
};

const VIEW_OPTIONS: { value: DashboardViewMode; label: string }[] = [
  { value: "consolidated", label: "Consolidado" },
  { value: "filial", label: "Unidade" },
  { value: "department", label: "Departamento" },
];

type TopDailyPoint = {
  name: string;
  value: number;
};

function formatPeriod(filters: Filters) {
  return `${filters.dataInicial.split("-").reverse().join("/")} — ${filters.dataFinal
    .split("-")
    .reverse()
    .join("/")}`;
}

function chartHint(
  periodLabel: string,
  measure: ChartMeasure,
  granularity: ChartGranularity,
  dayProrated: boolean,
  needsNavigation: boolean
): string {
  const parts = [periodLabel];
  if (measure === "hours") {
    parts.push("horas economizadas no recorte");
  } else if (granularity === "day" && dayProrated) {
    parts.push("visão diária proporcional aos dias do filtro");
  } else if (granularity === "month") {
    parts.push("competências mensais incluídas no recorte");
  } else {
    parts.push("soma anual das competências no recorte");
  }
  if (needsNavigation) {
    parts.push("navegue com os botões ou a rolagem do mouse no gráfico");
  }
  return parts.join(" · ");
}

function ChartCard({
  title,
  titleHint,
  hint,
  toolbar,
  children,
}: {
  title: string;
  titleHint?: string;
  hint?: string;
  toolbar?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="ds-card ds-chart-card">
      <div className="ds-chart-card__header">
        <div>
          <h2 className="ds-section-title">
            {title}
            {titleHint ? (
              <HelpTooltip content={titleHint} ariaLabel={`Ajuda: ${title}`} />
            ) : null}
          </h2>
          {hint ? <p className="ds-hint">{hint}</p> : null}
        </div>
        {toolbar}
      </div>
      {children}
    </section>
  );
}

export function DashboardPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [evolucao, setEvolucao] = useState<DashboardEvolucaoItem[]>([]);
  const [processos, setProcessos] = useState<DashboardProcessoItem[]>([]);
  const [alertas, setAlertas] = useState<DashboardAlertItem[]>([]);
  const [porFamilia, setPorFamilia] = useState<DashboardFamiliaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [exporting, setExporting] = useState<"csv" | "excel" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingsGranularity, setSavingsGranularity] = useState<ChartGranularity>(() =>
    suggestGranularity(defaultFilters.dataInicial, defaultFilters.dataFinal)
  );
  const [savingsMeasure, setSavingsMeasure] = useState<ChartMeasure>("currency");
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [viewMode, setViewMode] = useState<DashboardViewMode>("consolidated");

  const params = useMemo(
    () =>
      buildDashboardQueryParams(
        {
          dataInicial: filters.dataInicial,
          dataFinal: filters.dataFinal,
          filialId: viewMode === "consolidated" ? "" : filters.filialId,
          setorId: viewMode === "department" ? filters.setorId : "",
        },
        options?.access_scope
      ),
    [filters, options?.access_scope, viewMode]
  );
  const periodLabel = useMemo(() => formatPeriod(filters), [filters]);
  const setoresFiltrados = useMemo(
    () => filterSetoresByFilial(options?.setores ?? [], filters.filialId),
    [options?.setores, filters.filialId]
  );

  useEffect(() => {
    let cancelled = false;
    fetchOptions(getAccessToken)
      .then((data) => {
        if (cancelled) return;
        setOptions(data);
        const defaultFilial = defaultDashboardFilialFilter(data.access_scope);
        if (defaultFilial) {
          setFilters((prev) => ({ ...prev, filialId: defaultFilial }));
          setViewMode("filial");
        }
      })
      .catch(() => {
        if (!cancelled) setOptions(null);
      });
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  useEffect(() => {
    if (viewMode === "consolidated") {
      setFilters((prev) => ({ ...prev, setorId: "" }));
    }
    if (viewMode === "filial") {
      setFilters((prev) => ({ ...prev, setorId: "" }));
    }
  }, [viewMode]);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [resumoData, evolucaoData, processosData, alertasData, familiaData] =
        await Promise.all([
          fetchDashboardResumo(getAccessToken, params),
          fetchDashboardEvolucao(getAccessToken, params),
          fetchDashboardProcessos(getAccessToken, params),
          fetchDashboardAlertas(getAccessToken, params),
          fetchDashboardPorFamilia(getAccessToken, params),
        ]);
      setResumo(resumoData);
      setEvolucao(evolucaoData.items);
      setProcessos(processosData.items);
      setAlertas(alertasData.items);
      setPorFamilia(familiaData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, params]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setSavingsGranularity(suggestGranularity(filters.dataInicial, filters.dataFinal));
  }, [filters.dataInicial, filters.dataFinal]);

  async function handleRefresh() {
    await load();
  }

  async function handleRecalcCache() {
    if (
      !window.confirm(
        "Recalcular o cache materializado (dashboard_calculos)? Pode levar alguns minutos."
      )
    ) {
      return;
    }
    setRecalculating(true);
    setError(null);
    try {
      await recalcularDashboard(getAccessToken);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao recalcular cache do dashboard");
    } finally {
      setRecalculating(false);
    }
  }

  async function handleDownloadCsv() {
    setExporting("csv");
    setError(null);
    try {
      await downloadDashboardCsv(getAccessToken, params);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar CSV");
    } finally {
      setExporting(null);
    }
  }

  async function handleDownloadExcel() {
    setExporting("excel");
    setError(null);
    try {
      await downloadDashboardExcel(getAccessToken, params);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar Excel");
    } finally {
      setExporting(null);
    }
  }

  const savingsChartSeries = useMemo(
    () =>
      buildEvolucaoSavingsSeries(
        evolucao,
        filters.dataInicial,
        filters.dataFinal,
        savingsGranularity
      ),
    [evolucao, filters.dataInicial, filters.dataFinal, savingsGranularity]
  );

  const savingsChartWindowKey = `${filters.dataInicial}|${filters.dataFinal}|${savingsGranularity}|${savingsMeasure}`;
  const savingsChartWindow = useChartSeriesWindow(
    savingsChartSeries.points,
    savingsChartWindowKey
  );
  const savingsChartData = savingsChartWindow.visible;

  const topDailyChart = useMemo<TopDailyPoint[]>(
    () =>
      [...processos]
        .filter((item) => (item.economia_diaria ?? 0) > 0)
        .sort((a, b) => (b.economia_diaria ?? 0) - (a.economia_diaria ?? 0))
        .slice(0, 10)
        .map((item) => ({
          name: item.nome_processo,
          value: item.economia_diaria ?? 0,
        })),
    [processos]
  );

  const topHorasDiariaChart = useMemo<TopDailyPoint[]>(
    () =>
      [...processos]
        .map((item) => ({
          item,
          value: horasEconomizadasDiaria(item),
        }))
        .filter((entry) => entry.value > 0)
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
        .map((entry) => ({
          name: entry.item.nome_processo,
          value: entry.value,
        })),
    [processos]
  );

  const familiaColumns = useMemo<DataTableColumn<DashboardFamiliaItem>[]>(
    () => [
      { key: "familia", header: "Família", render: (row) => row.familia_processo || "—", sortable: true },
      { key: "processos", header: "Processos", render: (row) => row.processos, sortable: true },
      {
        key: "bruta",
        header: "Economia bruta",
        render: (row) => formatCurrency(row.economia_bruta),
        sortable: true,
        className: "tm-table__money--positive",
      },
      {
        key: "liquida",
        header: "Economia líquida",
        render: (row) => formatCurrency(row.economia_liquida_mes),
        sortable: true,
        className: "tm-table__money--positive",
      },
    ],
    []
  );

  const processColumns = useMemo<DataTableColumn<DashboardProcessoItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        render: (row) => (
          <button
            type="button"
            className="ds-link-btn"
            onClick={() => onNavigate(buildProcessoPath(row.processo_id))}
          >
            {row.codigo_processo}
          </button>
        ),
        sortable: true,
        sortValue: (row) => row.codigo_processo,
      },
      {
        key: "processo",
        header: "Processo",
        render: (row) => (
          <button
            type="button"
            className="ds-link-btn"
            onClick={() => onNavigate(buildProcessoPath(row.processo_id))}
          >
            {row.nome_processo}
          </button>
        ),
        sortable: true,
        sortValue: (row) => row.nome_processo,
      },
      {
        key: "implantacao",
        header: "Implantação",
        render: (row) => row.data_implantacao?.split("-").reverse().join("/") ?? "—",
        sortable: true,
        sortValue: (row) => row.data_implantacao ?? "",
      },
      {
        key: "economia_diaria",
        header: "Economia/dia",
        render: (row) => formatCurrency(row.economia_diaria),
        sortable: true,
        sortValue: (row) => row.economia_diaria ?? 0,
        className: "tm-table__money--positive",
      },
      {
        key: "investimentos",
        header: "Invest. vigentes",
        render: (row) => formatCurrency(row.investimento_unico_mes),
        sortable: true,
        sortValue: (row) => row.investimento_unico_mes ?? 0,
        className: "tm-table__money--negative",
      },
      {
        key: "recursos",
        header: "Recursos vigentes",
        render: (row) => formatCurrency(row.custo_recursos_compartilhados_mes),
        sortable: true,
        sortValue: (row) => row.custo_recursos_compartilhados_mes ?? 0,
        className: "tm-table__money--negative",
      },
      {
        key: "liquida",
        header: "Líquida no recorte",
        render: (row) => {
          const moneyClass =
            (row.economia_liquida_mes ?? 0) < 0
              ? "tm-table__money--negative"
              : "tm-table__money--positive";
          return <span className={moneyClass}>{formatCurrency(row.economia_liquida_mes)}</span>;
        },
        sortable: true,
        sortValue: (row) => row.economia_liquida_mes ?? 0,
      },
      {
        key: "bruta",
        header: "Bruta no recorte",
        render: (row) => formatCurrency(row.economia_bruta),
        sortable: true,
        sortValue: (row) => row.economia_bruta ?? 0,
        className: "tm-table__money--positive",
      },
    ],
    [onNavigate]
  );

  const isBusy = loading || refreshing;
  const dashboardFetchProgress = useTrackedSingleFetchProgress(loading && !resumo);
  const dashboardLoadingProgress = useLoadingProgress(
    loading && !resumo,
    dashboardFetchProgress
  );

  if (loading && !resumo) {
    return (
      <TransformometroShell>
        <PageHeader
          title="Dashboard Transformômetro"
          subtitle="Economia bruta e líquida por competência — cadastro no PostgreSQL"
          currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.dashboard}
          onNavigate={onNavigate}
        />
        <LoadingActivityCard
          title="Carregando indicadores do Transformômetro"
          description="Consolidando economia, investimentos e recursos compartilhados."
          progressPercent={dashboardLoadingProgress}
        />
      </TransformometroShell>
    );
  }

  const savingsChartHint = chartHint(
    periodLabel,
    savingsMeasure,
    savingsGranularity,
    savingsChartSeries.dayProrated,
    savingsChartWindow.navigable
  );

  const savingsChartTitle =
    savingsMeasure === "hours" ? "Horas economizadas" : "Economia bruta vs Investimento";

  return (
    <TransformometroShell>
      <PageHeader
        title="Dashboard Transformômetro"
        subtitle="Economia bruta e líquida por competência — cadastro no PostgreSQL"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.dashboard}
        onNavigate={onNavigate}
        onRefresh={() => void handleRefresh()}
        refreshing={refreshing || recalculating}
        actions={
          <DashboardToolbarMenu
            exporting={exporting}
            recalculating={recalculating}
            disabled={refreshing}
            onExportCsv={() => void handleDownloadCsv()}
            onExportExcel={() => void handleDownloadExcel()}
            onRecalcCache={() => void handleRecalcCache()}
          />
        }
      />

      <section className="ds-filters-row ds-no-print">
          <SegmentToggle
            ariaLabel="Visão analítica do dashboard"
            idPrefix="tm-dashboard-view"
            options={
              canSelectConsolidatedView(options?.access_scope)
                ? VIEW_OPTIONS
                : VIEW_OPTIONS.filter((option) => option.value !== "consolidated")
            }
            value={viewMode}
            onChange={(next) => {
              setViewMode(next);
              if (next === "consolidated") {
                setFilters((prev) => ({ ...prev, filialId: "", setorId: "" }));
              }
              if (next === "filial" && !filters.filialId) {
                const fallback =
                  options?.filiais[0]?.id ?? defaultDashboardFilialFilter(options?.access_scope);
                if (fallback) {
                  setFilters((prev) => ({ ...prev, filialId: fallback, setorId: "" }));
                }
              }
            }}
          />
          <DateField
            label="Data inicial"
            value={filters.dataInicial}
            onChange={(value) => setFilters((prev) => ({ ...prev, dataInicial: value }))}
          />
          <DateField
            label="Data final"
            value={filters.dataFinal}
            onChange={(value) => setFilters((prev) => ({ ...prev, dataFinal: value }))}
          />
          <label className="ds-filter-box">
            <span className="tm-field__label">
              Unidade
              <HelpTooltip
                content={TM_HELP_TOOLTIPS.dashboard.unidade}
                ariaLabel="Ajuda: Unidade"
              />
            </span>
            <select
              value={filters.filialId}
              disabled={viewMode === "consolidated"}
              onChange={(e) => {
                const nextFilial = e.target.value;
                setFilters((prev) => ({
                  ...prev,
                  filialId: nextFilial,
                  setorId:
                    nextFilial && prev.setorId
                      ? filterSetoresByFilial(options?.setores ?? [], nextFilial).some(
                          (setor) => setor.id === prev.setorId
                        )
                        ? prev.setorId
                        : ""
                      : prev.setorId,
                }));
              }}
            >
              <option value="">Selecione…</option>
              {(options?.filiais ?? []).map((filial) => (
                <option key={filial.id} value={filial.id}>
                  {filial.id} — {filial.label}
                </option>
              ))}
            </select>
          </label>
          <label className="ds-filter-box">
            <span className="tm-field__label">
              Setor
              <HelpTooltip
                content={TM_HELP_TOOLTIPS.dashboard.setor}
                ariaLabel="Ajuda: Setor"
              />
            </span>
            <select
              value={filters.setorId}
              disabled={viewMode !== "department"}
              onChange={(e) => setFilters((prev) => ({ ...prev, setorId: e.target.value }))}
            >
              <option value="">Selecione…</option>
              {setoresFiltrados.map((setor) => (
                <option key={setor.id} value={setor.id}>
                  {setor.label}
                </option>
              ))}
            </select>
          </label>
      </section>

      <StatusAlerts
        error={error}
        loading={isBusy}
        hasData={Boolean(resumo)}
        onRetry={() => void load()}
      />

      {alertas.length > 0 ? (
        <CollapsiblePanel
          className="ds-card ds-alert-panel"
          triggerClassName="ds-alert-panel__trigger"
          bodyClassName="ds-alert-panel__body"
          header={
            <>
              <AlertTriangle size={20} aria-hidden />
              <div className="ds-alert-panel__titles">
                <h2 className="ds-section-title">Alertas — economia líquida negativa</h2>
                <p className="ds-hint">
                  Processos com pelo menos 3 meses consecutivos de líquida negativa no recorte
                  filtrado
                </p>
              </div>
              <span className="ds-alert-panel__count">{alertas.length}</span>
            </>
          }
        >
          <ul className="ds-alert-list">
            {alertas.slice(0, 12).map((alerta) => (
              <li key={alerta.processo_id} className="ds-alert-item">
                <div className="ds-alert-item__main">
                  <span className="ds-alert-item__code">{alerta.codigo_processo}</span>
                  <span className="ds-alert-item__name">{alerta.nome_processo}</span>
                </div>
                <div className="ds-alert-item__meta">
                  <span className="ds-alert-item__badge">{alerta.months} meses</span>
                  <span className="ds-alert-item__period">
                    {alerta.competencia_inicio} → {alerta.competencia_fim}
                  </span>
                  <span className="ds-alert-item__value">
                    {formatCurrency(alerta.economia_liquida_acumulada)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </CollapsiblePanel>
      ) : null}

      <section className="ds-kpi-grid">
        <KpiCard
          title="Economia líquida"
          titleHint={TM_HELP_TOOLTIPS.dashboard.kpis.economiaLiquida}
          value={formatCurrency(resumo?.economia_liquida_total)}
          subtitle={`Recorte · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Economia bruta"
          titleHint={TM_HELP_TOOLTIPS.dashboard.kpis.economiaBruta}
          value={formatCurrency(resumo?.economia_bruta_total)}
          subtitle={`Recorte · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Soluções implementadas"
          titleHint={TM_HELP_TOOLTIPS.dashboard.kpis.solucoes}
          value={formatDecimal(resumo?.solucoes_implementadas, 0)}
          subtitle="Melhoria, automação e correção"
          icon={<Lightbulb size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Horas economizadas"
          titleHint={TM_HELP_TOOLTIPS.dashboard.kpis.horas}
          value={formatDecimal(resumo?.horas_economizadas_total, 1)}
          subtitle={periodLabel}
          icon={<Clock size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="ROI acumulado"
          titleHint={TM_HELP_TOOLTIPS.dashboard.kpis.roi}
          value={formatRoiRatio(resumo?.roi_medio, 1)}
          subtitle={`Economia líquida / investimento · ${periodLabel}`}
          icon={<Percent size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Investimento total"
          titleHint={TM_HELP_TOOLTIPS.dashboard.kpis.investimento}
          value={formatCurrency(resumo?.investimento_total ?? resumo?.investimento_unico_total)}
          subtitle="Único, recorrente e recursos"
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
      </section>

      <div className="ds-charts-layout">
        <section className="ds-charts-grid ds-charts-grid--hero">
          <ChartCard
            title={savingsChartTitle}
            titleHint={TM_HELP_TOOLTIPS.dashboard.charts.savings}
            hint={savingsChartHint}
            toolbar={
              <div className="ds-chart-card__toolbar-stack ds-no-print">
                <ChartGranularityToggle
                  idPrefix="tm-dashboard-savings"
                  value={savingsGranularity}
                  onChange={setSavingsGranularity}
                />
                <SegmentToggle
                  idPrefix="tm-dashboard-measure"
                  ariaLabel="Unidade do gráfico principal"
                  options={CHART_MEASURE_OPTIONS}
                  value={savingsMeasure}
                  onChange={setSavingsMeasure}
                />
              </div>
            }
          >
            {savingsChartData.length === 0 && !isBusy ? (
              <p className="ds-state-box">
                Sem dados no período. Cadastre processos, revisões e medições e ajuste os
                filtros de data.
              </p>
            ) : (
              <ChartSeriesViewport
                navigable={savingsChartWindow.navigable}
                rangeLabel={savingsChartWindow.rangeLabel}
                page={savingsChartWindow.page}
                pageCount={savingsChartWindow.pageCount}
                total={savingsChartWindow.total}
                windowSize={savingsChartWindow.windowSize}
                offset={savingsChartWindow.offset}
                onStart={savingsChartWindow.goStart}
                onPrevPage={savingsChartWindow.goPrevPage}
                onNextPage={savingsChartWindow.goNextPage}
                onEnd={savingsChartWindow.goEnd}
                onShift={savingsChartWindow.shiftBy}
              >
                <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                  <AreaChart data={savingsChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis
                      tickFormatter={(v) =>
                        savingsMeasure === "hours"
                          ? formatHours(Number(v))
                          : formatCurrency(Number(v))
                      }
                      width={72}
                    />
                    <Tooltip
                      formatter={(v) =>
                        savingsMeasure === "hours"
                          ? formatHours(Number(v))
                          : formatCurrency(Number(v))
                      }
                    />
                    {savingsMeasure === "hours" ? (
                      <Area
                        type="monotone"
                        dataKey="horas"
                        name="Horas economizadas"
                        stroke={HORAS_COLOR}
                        fill={HORAS_COLOR}
                        fillOpacity={0.5}
                      />
                    ) : (
                      <>
                        <Area
                          type="monotone"
                          dataKey="bruta"
                          name="Economia bruta"
                          stroke={ECONOMIA_COLOR}
                          fill={ECONOMIA_COLOR}
                          fillOpacity={0.5}
                        />
                        <Area
                          type="monotone"
                          dataKey="investimento"
                          name="Investimento"
                          stroke={INVESTIMENTO_COLOR}
                          fill={INVESTIMENTO_COLOR}
                          fillOpacity={0.45}
                        />
                      </>
                    )}
                  </AreaChart>
                </ResponsiveContainer>
              </ChartSeriesViewport>
            )}
          </ChartCard>
        </section>

        <section className="ds-charts-grid ds-charts-grid--rankings">
          <ChartCard
            title="Top economia bruta diária"
            titleHint={TM_HELP_TOOLTIPS.dashboard.charts.topGross}
            hint={
              topDailyChart.length > 0
                ? "10 maiores no recorte · R$ (bruta diária)"
                : "Sem ranking no período"
            }
          >
            {topDailyChart.length === 0 && !isBusy ? (
              <p className="ds-state-box">Nenhum processo com economia diária no recorte.</p>
            ) : (
              <RankingBarChart
                data={topDailyChart}
                colors={CHART_COLORS}
                formatValue={formatCurrency}
              />
            )}
          </ChartCard>

          <ChartCard
            title="Top economia diária de horas"
            titleHint={TM_HELP_TOOLTIPS.dashboard.charts.topHours}
            hint={
              topHorasDiariaChart.length > 0
                ? "10 maiores no recorte · Horas (diária)"
                : "Sem ranking no período"
            }
          >
            {topHorasDiariaChart.length === 0 && !isBusy ? (
              <p className="ds-state-box">Nenhum processo com horas economizadas diárias no recorte.</p>
            ) : (
              <RankingBarChart
                data={topHorasDiariaChart}
                colors={CHART_COLORS}
                formatValue={formatHours}
              />
            )}
          </ChartCard>
        </section>
      </div>

      {porFamilia.length > 0 ? (
        <DataTableSection
          title="Resumo por família"
          titleHint={TM_HELP_TOOLTIPS.dashboard.charts.familia}
          hint="Processos com família preenchida no cadastro"
          columns={familiaColumns}
          rows={porFamilia}
          rowKey={(row) => row.familia_processo}
          loading={loading}
          refreshing={refreshing}
          emptyMessage=""
        />
      ) : null}

      <DataTableSection
        title="Processos no recorte"
        titleHint={TM_HELP_TOOLTIPS.dashboard.charts.processos}
        hint="Competência mais recente ou período filtrado"
        columns={processColumns}
        rows={processos}
        rowKey={(row) => row.processo_id}
        loading={loading}
        refreshing={refreshing}
        emptyMessage="Nenhum processo com economia calculada no período. Cadastre revisões e medições."
      />
    </TransformometroShell>
  );
}
