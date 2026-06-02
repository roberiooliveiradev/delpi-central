import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Coins,
  Layers,
  Lightbulb,
  List,
  Percent,
  Upload,
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
import { ChartCard } from "../../components/ChartCard";
import { ChartGranularityToggle } from "../../components/ChartGranularityToggle";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { DataSourceBanner } from "../../components/DataSourceBanner";
import { FilterBar } from "../../components/FilterBar";
import { KpiCard } from "../../components/KpiCard";
import { ModuleShortcut } from "../../components/ModuleShortcut";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { CHART_COLORS } from "../../constants/chartColors";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { buildProcessoPath } from "../../utils/routeParser";
import {
  fetchDashboardEvolucao,
  fetchDashboardProcessos,
  fetchDashboardResumo,
  fetchOptions,
  type DashboardEvolucaoItem,
  type DashboardProcessoItem,
  type DashboardResumo,
  type OptionsData,
} from "../../data/api/transformometroApi";
import { fetchTransformometroHealth } from "../../data/api/transformometroHealthApi";
import type { ChartGranularity } from "../../types/chart";
import {
  formatPeriodLabel,
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "../../utils/dates";
import { buildEvolucaoSavingsSeries } from "../../utils/evolucaoChartSeries";
import { suggestGranularity } from "../../utils/periodBuckets";
import { formatCurrency, formatInteger, formatPercent } from "../../utils/format";

const CHART_HEIGHT_HOME = 260;

type LoadState = "loading" | "ok" | "error";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function HomePage({ getAccessToken, pathname, onNavigate }: Props) {
  const [dateStart, setDateStart] = useState(getFirstDayOfMonthInputValue);
  const [dateEnd, setDateEnd] = useState(getTodayInputValue);
  const [branch, setBranch] = useState("");
  const [setorId, setSetorId] = useState("");
  const [state, setState] = useState<LoadState>("loading");
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [evolucao, setEvolucao] = useState<DashboardEvolucaoItem[]>([]);
  const [processos, setProcessos] = useState<DashboardProcessoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingsGranularity, setSavingsGranularity] = useState<ChartGranularity>(() =>
    suggestGranularity(getFirstDayOfMonthInputValue(), getTodayInputValue())
  );

  const apiParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (dateStart) params.competencia_inicio = dateStart;
    if (dateEnd) params.competencia_fim = dateEnd;
    if (branch) params.filial_id = branch;
    if (setorId) params.setor_id = setorId;
    return params;
  }, [dateEnd, dateStart, branch, setorId]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const load = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const [healthPayload, r, ev, proc, opts] = await Promise.all([
        fetchTransformometroHealth(getAccessToken),
        fetchDashboardResumo(getAccessToken, apiParams),
        fetchDashboardEvolucao(getAccessToken, apiParams),
        fetchDashboardProcessos(getAccessToken, apiParams),
        fetchOptions(getAccessToken),
      ]);
      setHealth(healthPayload as Record<string, unknown>);
      setResumo(r);
      setEvolucao(ev.items);
      setProcessos(proc.items);
      setOptions(opts);
      setState("ok");
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Erro ao carregar visão geral");
    }
  }, [apiParams, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setSavingsGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const savingsChart = useMemo(
    () => buildEvolucaoSavingsSeries(evolucao, dateStart, dateEnd, savingsGranularity),
    [dateEnd, dateStart, evolucao, savingsGranularity]
  );

  const savingsChartData = savingsChart.points;

  const savingsChartHint = useMemo(() => {
    const parts = [periodLabel];
    if (savingsGranularity === "day" && savingsChart.dayProrated) {
      parts.push("economia diária proporcional ao total mensal");
    }
    if (savingsChart.truncated) {
      parts.push("primeiros 60 intervalos");
    }
    return parts.join(" · ");
  }, [periodLabel, savingsChart.dayProrated, savingsChart.truncated, savingsGranularity]);

  const topDailyChart = useMemo(
    () =>
      [...processos]
        .sort((a, b) => (b.economia_diaria ?? 0) - (a.economia_diaria ?? 0))
        .slice(0, 8)
        .map((item) => ({
          name:
            (item.nome_processo?.length ?? 0) > 22
              ? `${item.nome_processo.slice(0, 22)}…`
              : item.nome_processo,
          value: item.economia_diaria ?? 0,
        })),
    [processos]
  );

  const processColumns = useMemo<DataTableColumn<DashboardProcessoItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        render: (row) =>
          row.processo_id ? (
            <button
              type="button"
              className="ds-link-btn"
              onClick={() => onNavigate(buildProcessoPath(row.processo_id))}
            >
              {row.codigo_processo ?? "—"}
            </button>
          ) : (
            row.codigo_processo ?? "—"
          ),
      },
      {
        key: "nome",
        header: "Processo",
        sortable: true,
        className: "ds-table__col--wide",
        render: (row) =>
          row.processo_id ? (
            <button
              type="button"
              className="ds-link-btn"
              onClick={() => onNavigate(buildProcessoPath(row.processo_id))}
            >
              {row.nome_processo ?? "—"}
            </button>
          ) : (
            row.nome_processo ?? "—"
          ),
      },
      {
        key: "liquida",
        header: "Líquida/mês",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.economia_liquida_mes ?? 0,
        render: (row) => {
          const value = row.economia_liquida_mes;
          const negative = value != null && value < 0;
          return (
            <span className={negative ? "ds-table__value--negative" : undefined}>
              {formatCurrency(value)}
            </span>
          );
        },
      },
      {
        key: "daily",
        header: "Economia/dia",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.economia_diaria ?? 0,
        render: (row) => formatCurrency(row.economia_diaria),
      },
    ],
    [onNavigate]
  );

  const isLoading = state === "loading";

  return (
    <TransformometroShell>
      <PageHeader
        title="Transformômetro"
        subtitle="Melhorias de processo — economia, investimento, ROI e payback"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={isLoading}
        actions={
          <button
            type="button"
            className="ds-primary-btn"
            onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.dashboard)}
          >
            <BarChart3 size={16} />
            Dashboard completo
          </button>
        }
      />

      <DataSourceBanner />

      <FilterBar
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        setorId={setorId}
        options={options}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onSetorChange={setSetorId}
        onRefresh={() => void load()}
        refreshing={isLoading}
      />

      <StatusAlerts
        error={error}
        loading={isLoading}
        hasData={resumo !== null || evolucao.length > 0}
        onRetry={() => void load()}
      />

      {state === "ok" && health && !isLoading ? (
        <section className="ds-card ds-health-card ds-health-card--inline">
          <div className="ds-health-card__status">
            <span className="ds-health-pill ds-health-pill--ok">
              API {String(health.status ?? "online")}
            </span>
            <span className="ds-health-pill">Fase {String(health.phase ?? "—")}</span>
            <span className="ds-health-pill">Módulo {String(health.module ?? "transformometro")}</span>
          </div>
          <p className="ds-hint ds-health-card__hint">
            Período automático: <strong>{periodLabel}</strong>. Ajuste filtros no dashboard
            completo.
          </p>
        </section>
      ) : null}

      <section className="ds-kpi-grid ds-kpi-grid--responsive" aria-busy={isLoading}>
        <KpiCard
          title="Economia líquida"
          value={formatCurrency(resumo?.economia_liquida_total)}
          subtitle={periodLabel}
          icon={<Coins size={22} />}
          loading={isLoading && !resumo}
        />
        <KpiCard
          title="Economia bruta"
          value={formatCurrency(resumo?.economia_bruta_total)}
          subtitle="Consolidado no período"
          icon={<Coins size={22} />}
          loading={isLoading && !resumo}
        />
        <KpiCard
          title="Soluções"
          value={formatInteger(resumo?.solucoes_implementadas)}
          subtitle="Melhoria, automação e correção"
          icon={<Lightbulb size={22} />}
          loading={isLoading && !resumo}
        />
        <KpiCard
          title="ROI médio"
          value={formatPercent(resumo?.roi_medio, 1)}
          subtitle="Acumulado no recorte"
          icon={<Percent size={22} />}
          loading={isLoading && !resumo}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard
          title="Economia vs Investimento"
          hint={savingsChartHint}
          toolbar={
            <ChartGranularityToggle
              idPrefix="tm-home-savings"
              value={savingsGranularity}
              onChange={setSavingsGranularity}
            />
          }
        >
          {savingsChartData.length === 0 && !isLoading ? (
            <p className="ds-state-box">Sem competências no período. Abra o dashboard ou recalcule.</p>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT_HOME}>
              <AreaChart data={savingsChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => formatCurrency(Number(v))} width={68} />
                <Tooltip 
                  formatter={(v) => formatCurrency(Number(v))} 
                  contentStyle={{ backgroundColor: "var(--ds-card-bg)", border: "1px solid var(--ds-card-border)" }}
                />
                <Area
                  type="monotone"
                  dataKey="liquida"
                  name="Economia Líquida"
                  fill={CHART_COLORS[0]}
                  stroke={CHART_COLORS[0]}
                  fillOpacity={0.6}
                  stackId="economia"
                />
                <Area
                  type="monotone"
                  dataKey="investimento"
                  name="Investimento"
                  fill={CHART_COLORS[4]}
                  stroke={CHART_COLORS[4]}
                  fillOpacity={0.6}
                  stackId="investimento"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Top economia diária" hint="Até 8 processos">
          {topDailyChart.length === 0 && !isLoading ? (
            <p className="ds-state-box">Nenhum processo com economia calculada.</p>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT_HOME}>
              <BarChart data={topDailyChart} layout="vertical" margin={{ left: 4, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--ds-card-border)" />
                <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v))} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={22}>
                  {topDailyChart.map((_, index) => (
                    <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        title="Destaques do período"
        hint="Clique em Dashboard completo para filtros e exportação"
        columns={processColumns}
        rows={processos}
        rowKey={(row) => row.processo_id}
        loading={isLoading}
        pageSize={10}
        emptyMessage="Nenhum processo com economia no mês. Cadastre revisões e medições."
      />

      <section className="ds-shortcuts-grid ds-shortcuts-grid--home">
        <ModuleShortcut
          title="Dashboard"
          description="Alertas, família, export CSV/Excel e recálculo."
          path={TRANSFORMOMETRO_ROUTES.dashboard}
          onNavigate={onNavigate}
          icon={<BarChart3 size={20} />}
        />
        <ModuleShortcut
          title="Processos"
          description="Revisões, medição, investimentos e vínculos."
          path={TRANSFORMOMETRO_ROUTES.processos}
          onNavigate={onNavigate}
          icon={<List size={20} />}
        />
        <ModuleShortcut
          title="Recursos"
          description="Catálogo global de licenças e ferramentas."
          path={TRANSFORMOMETRO_ROUTES.recursos}
          onNavigate={onNavigate}
          icon={<Layers size={20} />}
        />
        <ModuleShortcut
          title="Importar"
          description="Migração Transforma+ com validação."
          path={TRANSFORMOMETRO_ROUTES.import}
          onNavigate={onNavigate}
          icon={<Upload size={20} />}
        />
      </section>

      <section className="ds-card ds-cta-strip">
        <div>
          <h2 className="ds-section-title">Explorar dados</h2>
          <p className="ds-hint">
            Filtros por filial, setor, alertas de economia negativa e comparativo de revisões no
            dashboard analítico.
          </p>
        </div>
        <button
          type="button"
          className="ds-primary-btn"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.dashboard)}
        >
          Abrir dashboard
          <ArrowRight size={16} />
        </button>
      </section>
    </TransformometroShell>
  );
}
