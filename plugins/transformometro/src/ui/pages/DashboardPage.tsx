import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Clock,
  Coins,
  Download,
  FileDown,
  Lightbulb,
  Percent,
  RefreshCw,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { DateField } from "../../components/DateField";
import { KpiCard } from "../../components/KpiCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { ChartGranularityToggle } from "../../components/ChartGranularityToggle";
import { CollapsiblePanel } from "../../components/CollapsiblePanel";
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
  recalcularDashboard,
  type DashboardAlertItem,
  type DashboardEvolucaoItem,
  type DashboardFamiliaItem,
  type DashboardProcessoItem,
  type DashboardResumo,
} from "../../data/api/transformometroApi";
import type { ChartGranularity } from "../../types/chart";
import { CHART_MEASURE_OPTIONS, type ChartMeasure } from "../../types/chartMeasure";
import { formatCurrency, formatDecimal, formatHours, formatPercent } from "../../utils/format";
import { buildEvolucaoSavingsSeries } from "../../utils/evolucaoChartSeries";
import { suggestGranularity } from "../../utils/periodBuckets";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { buildProcessoPath } from "../../utils/routeParser";

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

type TopDailyPoint = {
  name: string;
  value: number;
};

const today = new Date();
const formatDateInput = (date: Date) => date.toISOString().slice(0, 10);
const defaultStart = new Date(today.getFullYear(), today.getMonth() - 10, 1);
const defaultFilters: Filters = {
  dataInicial: formatDateInput(defaultStart),
  dataFinal: formatDateInput(today),
  filialId: "",
  setorId: "",
};

function buildParams(filters: Filters) {
  const params: Record<string, string> = {};
  if (filters.dataInicial) params.competencia_inicio = filters.dataInicial;
  if (filters.dataFinal) params.competencia_fim = filters.dataFinal;
  if (filters.filialId) params.filial_id = filters.filialId;
  if (filters.setorId) params.setor_id = filters.setorId;
  return params;
}

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
  truncated: boolean
): string {
  const parts = [periodLabel];
  if (measure === "hours") {
    parts.push("horas economizadas no recorte");
  } else if (granularity === "day" && dayProrated) {
    parts.push("visão diária proporcional aos dias selecionados no filtro");
  } else if (granularity === "month") {
    parts.push("competências mensais incluídas no recorte");
  } else {
    parts.push("soma anual das competências no recorte");
  }
  if (truncated) {
    parts.push("exibindo primeiros 60 períodos");
  }
  return parts.join(" · ");
}

function ChartCard({
  title,
  hint,
  toolbar,
  children,
}: {
  title: string;
  hint?: string;
  toolbar?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="ds-card ds-chart-card">
      <div className="ds-chart-card__header">
        <div>
          <h2 className="ds-section-title">{title}</h2>
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
  const [exporting, setExporting] = useState<"csv" | "excel" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingsGranularity, setSavingsGranularity] = useState<ChartGranularity>(() =>
    suggestGranularity(defaultFilters.dataInicial, defaultFilters.dataFinal)
  );
  const [savingsMeasure, setSavingsMeasure] = useState<ChartMeasure>("currency");

  const params = useMemo(() => buildParams(filters), [filters]);
  const periodLabel = useMemo(() => formatPeriod(filters), [filters]);

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

  async function handleRecalculate() {
    setRefreshing(true);
    setError(null);
    try {
      await recalcularDashboard(getAccessToken, params);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao recalcular dashboard");
    } finally {
      setRefreshing(false);
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

  const savingsChartData = savingsChartSeries.points;

  const topDailyChart = useMemo<TopDailyPoint[]>(
    () =>
      [...processos]
        .filter((item) => (item.economia_diaria ?? 0) > 0)
        .sort((a, b) => (b.economia_diaria ?? 0) - (a.economia_diaria ?? 0))
        .slice(0, 10)
        .map((item) => ({
          name: item.nome_processo.length > 28 ? `${item.nome_processo.slice(0, 25)}...` : item.nome_processo,
          value: item.economia_diaria ?? 0,
        })),
    [processos]
  );

  const topHoursChart = useMemo<TopDailyPoint[]>(
    () =>
      [...processos]
        .filter((item) => (item.horas_economizadas_mes ?? 0) > 0)
        .sort((a, b) => (b.horas_economizadas_mes ?? 0) - (a.horas_economizadas_mes ?? 0))
        .slice(0, 10)
        .map((item) => ({
          name: item.nome_processo.length > 28 ? `${item.nome_processo.slice(0, 25)}...` : item.nome_processo,
          value: item.horas_economizadas_mes ?? 0,
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
          currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
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
    savingsChartSeries.truncated
  );

  const savingsChartTitle =
    savingsMeasure === "hours" ? "Horas economizadas" : "Economia bruta vs Investimento";

  return (
    <TransformometroShell>
      <PageHeader
        title="Dashboard Transformômetro"
        subtitle="Economia bruta e líquida por competência — cadastro no PostgreSQL"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
        actions={
          <>
            <button type="button" className="ds-ghost-btn" onClick={handleDownloadCsv} disabled={exporting !== null}>
              <Download size={16} />
              {exporting === "csv" ? "Gerando..." : "CSV"}
            </button>
            <button type="button" className="ds-ghost-btn" onClick={handleDownloadExcel} disabled={exporting !== null}>
              <FileDown size={16} />
              {exporting === "excel" ? "Gerando..." : "Excel"}
            </button>
            <button type="button" className="ds-primary-btn" onClick={handleRecalculate} disabled={refreshing}>
              <RefreshCw size={16} />
              {refreshing ? "Atualizando..." : "Atualizar"}
            </button>
          </>
        }
      />

      <section className="ds-filters-row ds-no-print">
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
            Filial
            <select
              value={filters.filialId}
              onChange={(e) => setFilters((prev) => ({ ...prev, filialId: e.target.value }))}
            >
              <option value="">Consolidado</option>
              <option value="01">Filial 01</option>
              <option value="02">Filial 02</option>
            </select>
          </label>
          <label className="ds-filter-box">
            Setor
            <select
              value={filters.setorId}
              onChange={(e) => setFilters((prev) => ({ ...prev, setorId: e.target.value }))}
            >
              <option value="">Todos</option>
              <option value="engenharia">Engenharia</option>
              <option value="qualidade">Qualidade</option>
              <option value="pcp">PCP</option>
              <option value="producao">Produção</option>
              <option value="comercial">Comercial</option>
              <option value="compras">Compras</option>
              <option value="almoxarifado">Almoxarifado</option>
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
          value={formatCurrency(resumo?.economia_liquida_total)}
          subtitle={`Consolidado · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Economia bruta"
          value={formatCurrency(resumo?.economia_bruta_total)}
          subtitle={`Recorte · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Soluções implementadas"
          value={formatDecimal(resumo?.solucoes_implementadas, 0)}
          subtitle="Melhoria, automação e correção"
          icon={<Lightbulb size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Horas economizadas"
          value={formatDecimal(resumo?.horas_economizadas_total, 1)}
          subtitle={periodLabel}
          icon={<Clock size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="ROI acumulado"
          value={formatPercent(resumo?.roi_medio, 1)}
          subtitle="Economia líquida / investimento total"
          icon={<Percent size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Investimento total"
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
            )}
          </ChartCard>
        </section>

        <section className="ds-charts-grid ds-charts-grid--rankings">
          <ChartCard
            title="Top economia diária"
            hint={topDailyChart.length > 0 ? "10 maiores no recorte · R$" : "Sem ranking no período"}
          >
            {topDailyChart.length === 0 && !isBusy ? (
              <p className="ds-state-box">Nenhum processo com economia diária no recorte.</p>
            ) : (
              <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                <BarChart data={topDailyChart} layout="vertical" margin={{ left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
                  <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v))} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Bar dataKey="value" radius={[0, 8, 8, 0]} maxBarSize={28}>
                    {topDailyChart.map((_, index) => (
                      <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard
            title="Top economia de horas"
            hint={topHoursChart.length > 0 ? "10 maiores no recorte · Horas" : "Sem ranking no período"}
          >
            {topHoursChart.length === 0 && !isBusy ? (
              <p className="ds-state-box">Nenhum processo com horas economizadas no recorte.</p>
            ) : (
              <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                <BarChart data={topHoursChart} layout="vertical" margin={{ left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
                  <XAxis type="number" tickFormatter={(v) => formatHours(Number(v))} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => formatHours(Number(v))} />
                  <Bar dataKey="value" radius={[0, 8, 8, 0]} maxBarSize={28}>
                    {topHoursChart.map((_, index) => (
                      <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </section>
      </div>

      {porFamilia.length > 0 ? (
        <DataTableSection
          title="Resumo por família"
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
