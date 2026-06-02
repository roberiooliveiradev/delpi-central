import { useCallback, useEffect, useMemo, useState } from "react";
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
import {
  AlertTriangle,
  Clock,
  Coins,
  Download,
  FileSpreadsheet,
  Lightbulb,
  Percent,
} from "lucide-react";

import type { AppProps } from "../../App";
import { ChartCard } from "../../components/ChartCard";
import { ChartGranularityToggle } from "../../components/ChartGranularityToggle";
import { DataSourceBanner } from "../../components/DataSourceBanner";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { FilterBar } from "../../components/FilterBar";
import { KpiCard } from "../../components/KpiCard";
import { PrintReportButton } from "../../components/PrintReportButton";
import { PrintReportSummary } from "../../components/PrintReportSummary";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  useLoadingProgress,
  type RequestProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { CHART_COLORS } from "../../constants/chartColors";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { buildProcessoPath } from "../../utils/routeParser";
import {
  downloadDashboardCsv,
  downloadDashboardExcel,
  fetchDashboardAlertas,
  fetchDashboardEvolucao,
  fetchDashboardPorFamilia,
  fetchDashboardProcessos,
  fetchDashboardResumo,
  fetchOptions,
  type DashboardAlertItem,
  type DashboardEvolucaoItem,
  type DashboardFamiliaItem,
  type DashboardProcessoItem,
  type DashboardResumo,
  type OptionsData,
} from "../../data/api/transformometroApi";
import type { ChartGranularity } from "../../types/chart";
import {
  formatDisplayDate,
  formatPeriodLabel,
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "../../utils/dates";
import { buildEvolucaoSavingsSeries } from "../../utils/evolucaoChartSeries";
import { suggestGranularity } from "../../utils/periodBuckets";
import { formatCurrency, formatDecimal, formatInteger, formatPercent } from "../../utils/format";

const CHART_HEIGHT = 320;

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function DashboardPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [dateStart, setDateStart] = useState(getFirstDayOfMonthInputValue);
  const [dateEnd, setDateEnd] = useState(getTodayInputValue);
  const [branch, setBranch] = useState("");
  const [setorId, setSetorId] = useState("");
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [evolucao, setEvolucao] = useState<DashboardEvolucaoItem[]>([]);
  const [processos, setProcessos] = useState<DashboardProcessoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [alertas, setAlertas] = useState<DashboardAlertItem[]>([]);
  const [porFamilia, setPorFamilia] = useState<DashboardFamiliaItem[]>([]);
  const [exportando, setExportando] = useState(false);
  const [savingsGranularity, setSavingsGranularity] = useState<ChartGranularity>(() =>
    suggestGranularity(getFirstDayOfMonthInputValue(), getTodayInputValue())
  );
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const apiParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (dateStart) params.competencia_inicio = dateStart;
    if (dateEnd) params.competencia_fim = dateEnd;
    if (branch) params.filial_id = branch;
    if (setorId) params.setor_id = setorId;
    return params;
  }, [branch, dateEnd, dateStart, setorId]);

  const load = useCallback(async () => {
    const controller = new AbortController();
    setRefreshing(true);
    setError(null);
    try {
      const results = await runParallelWithProgress(
        [
          async () => fetchDashboardResumo(getAccessToken, apiParams),
          async () => fetchDashboardEvolucao(getAccessToken, apiParams),
          async () => fetchDashboardProcessos(getAccessToken, apiParams),
          async () => fetchOptions(getAccessToken),
          async () =>
            fetchDashboardAlertas(getAccessToken, {
              ...apiParams,
              meses_consecutivos: "3",
            }),
          async () => fetchDashboardPorFamilia(getAccessToken, apiParams),
        ] as ReadonlyArray<(signal: AbortSignal) => Promise<unknown>>,
        controller.signal,
        setRequestProgress
      );

      const [r, ev, proc, opts, al, fam] = results.map((result) => {
        if (result.status === "rejected") {
          throw result.reason;
        }
        return result.value;
      });

      setResumo(r as DashboardResumo);
      setEvolucao((ev as { items: DashboardEvolucaoItem[] }).items);
      setProcessos((proc as { items: DashboardProcessoItem[] }).items);
      setOptions(opts as OptionsData);
      setAlertas((al as { items: DashboardAlertItem[] }).items);
      setPorFamilia((fam as { items: DashboardFamiliaItem[] }).items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [apiParams, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setSavingsGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  async function handleExportCsv() {
    setExportando(true);
    setError(null);
    try {
      await downloadDashboardCsv(getAccessToken, apiParams);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar CSV");
    } finally {
      setExportando(false);
    }
  }

  async function handleExportExcel() {
    setExportando(true);
    setError(null);
    try {
      await downloadDashboardExcel(getAccessToken, apiParams);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar Excel");
    } finally {
      setExportando(false);
    }
  }

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const printBranchLabel = useMemo(() => {
    if (!branch) return "Consolidado";
    const found = options?.filiais?.find((f) => f.id === branch);
    return found ? `${found.id} — ${found.label}` : branch;
  }, [branch, options?.filiais]);
  const printSetorLabel = setorId || "Todos";
  const isBusy = loading || refreshing;
  const hasData = resumo !== null || evolucao.length > 0 || processos.length > 0;
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

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
    if (savingsGranularity === "year") {
      parts.push("soma por ano");
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
        .slice(0, 10)
        .map((item) => ({
          name:
            (item.nome_processo?.length ?? 0) > 28
              ? `${item.nome_processo.slice(0, 28)}…`
              : item.nome_processo,
          value: item.economia_diaria ?? 0,
        })),
    [processos]
  );

  const familiaColumns = useMemo<DataTableColumn<DashboardFamiliaItem>[]>(
    () => [
      { key: "familia", header: "Família", render: (row) => row.familia_processo, sortable: true },
      {
        key: "processos",
        header: "Processos",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.processos,
        render: (row) => formatInteger(row.processos),
      },
      {
        key: "bruta",
        header: "Economia bruta",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.economia_bruta,
        render: (row) => formatCurrency(row.economia_bruta),
      },
      {
        key: "liquida",
        header: "Economia líquida",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.economia_liquida_mes,
        render: (row) => {
          const negative = row.economia_liquida_mes < 0;
          return (
            <span className={negative ? "ds-table__value--negative" : undefined}>
              {formatCurrency(row.economia_liquida_mes)}
            </span>
          );
        },
      },
    ],
    []
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
              onClick={(event) => {
                event.stopPropagation();
                onNavigate(buildProcessoPath(row.processo_id));
              }}
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
              onClick={(event) => {
                event.stopPropagation();
                onNavigate(buildProcessoPath(row.processo_id));
              }}
            >
              {row.nome_processo ?? "—"}
            </button>
          ) : (
            row.nome_processo ?? "—"
          ),
      },
      {
        key: "implantacao",
        header: "Implantação",
        sortable: true,
        sortValue: (row) => row.data_implantacao ?? "",
        render: (row) => formatDisplayDate(row.data_implantacao),
      },
      {
        key: "daily",
        header: "Economia/dia",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.economia_diaria ?? 0,
        render: (row) => {
          const value = row.economia_diaria;
          const negative = value != null && value < 0;
          return (
            <span className={negative ? "ds-table__value--negative" : undefined}>
              {formatCurrency(value)}
            </span>
          );
        },
      },
      {
        key: "investimentos",
        header: "Invest. vigentes",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => (row.investimento_unico_mes ?? 0) + (row.custo_recorrente_mes ?? 0),
        render: (row) =>
          formatCurrency((row.investimento_unico_mes ?? 0) + (row.custo_recorrente_mes ?? 0)),
      },
      {
        key: "recursos",
        header: "Recursos vigentes",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.custo_recursos_compartilhados_mes ?? 0,
        render: (row) => formatCurrency(row.custo_recursos_compartilhados_mes ?? 0),
      },
      {
        key: "month",
        header: "Líquida no recorte",
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
        key: "bruta",
        header: "Bruta no recorte",
        sortable: true,
        className: "ds-table__col--numeric",
        sortValue: (row) => row.economia_bruta ?? 0,
        render: (row) => formatCurrency(row.economia_bruta),
      },
    ],
    [onNavigate]
  );

  return (
    <TransformometroShell printRoot>
      <FilterBar
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.dashboard}
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
        refreshing={refreshing}
        headerActions={
          <>
            <PrintReportButton disabled={isBusy && !hasData} />
            <button
              type="button"
              className="ds-ghost-btn"
              disabled={exportando || isBusy}
              onClick={() => void handleExportCsv()}
            >
              <Download size={16} />
              {exportando ? "Exportando…" : "CSV"}
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              disabled={exportando || isBusy}
              onClick={() => void handleExportExcel()}
            >
              <FileSpreadsheet size={16} />
              Excel
            </button>
          </>
        }
      />

      <PrintReportSummary
        title="Dashboard Transformômetro"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branchLabel={printBranchLabel}
        setorLabel={printSetorLabel}
      />

      <div className="ds-no-print">
        <DataSourceBanner />
      </div>

      <div className="ds-no-print">
        <StatusAlerts
        error={error}
        loading={loading}
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={() => void load()}
        />
      </div>

      {refreshing && hasData ? (
        <div className="ds-no-print">
          <LoadingActivityCard
            title="Atualizando dashboard"
            description="Atualizando KPIs, gráficos e ranking de processos."
            variant="compact"
            sticky
            progressPercent={refreshLoadingProgress}
          />
        </div>
      ) : null}

      {alertas.length > 0 ? (
        <section className="ds-card ds-alert-panel ds-no-print">
          <h2 className="ds-section-title">
            <AlertTriangle size={18} />
            Alertas — economia líquida negativa (≥3 meses)
          </h2>
          <ul className="ds-alert-list">
            {alertas.map((item) => (
              <li key={item.processo_id}>
                <strong>{item.codigo_processo}</strong> — {item.nome_processo}:{" "}
                {item.months} meses ({item.competencia_inicio} → {item.competencia_fim}), acumulado{" "}
                {formatCurrency(item.economia_liquida_acumulada)}
                {item.familia_processo ? ` · família ${item.familia_processo}` : ""}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Economia líquida"
          value={formatCurrency(resumo?.economia_liquida_total)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Economia bruta"
          value={formatCurrency(resumo?.economia_bruta_total)}
          subtitle="No recorte de competências"
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
        <KpiCard
          title="Soluções implementadas"
          value={formatInteger(resumo?.solucoes_implementadas)}
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
          title="ROI médio"
          value={formatPercent(resumo?.roi_medio, 1)}
          subtitle="Fórmula spec (acumulado)"
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

      <section className="ds-charts-grid">
        <ChartCard
          title="Economia vs Investimento"
          hint={savingsChartHint}
          toolbar={
            <div className="ds-no-print">
              <ChartGranularityToggle
                idPrefix="tm-dashboard-savings"
                value={savingsGranularity}
                onChange={setSavingsGranularity}
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
                <YAxis tickFormatter={(v) => formatCurrency(Number(v))} width={72} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Area
                  type="monotone"
                  dataKey="liquida"
                  name="Economia líquida"
                  stroke={CHART_COLORS[0]}
                  fill={CHART_COLORS[0]}
                  fillOpacity={0.5}
                />
                <Area
                  type="monotone"
                  dataKey="investimento"
                  name="Investimento"
                  stroke={CHART_COLORS[4]}
                  fill={CHART_COLORS[4]}
                  fillOpacity={0.5}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard
          title="Top economia diária"
          hint={topDailyChart.length > 0 ? "10 maiores no recorte" : "Sem ranking no período"}
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
      </section>

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
