import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, Clock, Coins, Download, Lightbulb, Percent, RefreshCw } from "lucide-react";

import type { AppProps } from "../../App";
import { ChartCard } from "../../components/ChartCard";
import { DataSourceBanner } from "../../components/DataSourceBanner";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { FilterBar } from "../../components/FilterBar";
import { KpiCard } from "../../components/KpiCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { StatusAlerts } from "../../components/StatusAlerts";
import { CHART_COLORS } from "../../constants/chartColors";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  downloadDashboardCsv,
  fetchDashboardAlertas,
  fetchDashboardEvolucao,
  fetchDashboardProcessos,
  fetchDashboardResumo,
  fetchOptions,
  recalcularDashboard,
  type DashboardAlertItem,
  type DashboardEvolucaoItem,
  type DashboardProcessoItem,
  type DashboardResumo,
  type OptionsData,
} from "../../data/api/transformometroApi";
import {
  dateInputToCompetencia,
  formatPeriodLabel,
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
  monthKeyToLabel,
} from "../../utils/dates";
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
  const [recalculando, setRecalculando] = useState(false);
  const [alertas, setAlertas] = useState<DashboardAlertItem[]>([]);
  const [exportando, setExportando] = useState(false);

  const apiParams = useMemo(() => {
    const params: Record<string, string> = {};
    const inicio = dateInputToCompetencia(dateStart);
    const fim = dateInputToCompetencia(dateEnd);
    if (inicio) params.competencia_inicio = inicio;
    if (fim) params.competencia_fim = fim;
    if (branch) params.filial_id = branch;
    if (setorId) params.setor_id = setorId;
    return params;
  }, [branch, dateEnd, dateStart, setorId]);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [r, ev, proc, opts, al] = await Promise.all([
        fetchDashboardResumo(getAccessToken, apiParams),
        fetchDashboardEvolucao(getAccessToken, apiParams),
        fetchDashboardProcessos(getAccessToken, apiParams),
        fetchOptions(getAccessToken),
        fetchDashboardAlertas(getAccessToken, {
          ...apiParams,
          meses_consecutivos: "3",
        }),
      ]);
      setResumo(r);
      setEvolucao(ev.items);
      setProcessos(proc.items);
      setOptions(opts);
      setAlertas(al.items);
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

  async function handleExportCsv() {
    setExportando(true);
    setError(null);
    try {
      const blob = await downloadDashboardCsv(getAccessToken, apiParams);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "transformometro-dashboard.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar CSV");
    } finally {
      setExportando(false);
    }
  }

  async function handleRecalcular() {
    setRecalculando(true);
    setError(null);
    try {
      await recalcularDashboard(getAccessToken);
      setLoading(true);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao recalcular");
    } finally {
      setRecalculando(false);
    }
  }

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const isBusy = loading || refreshing;
  const hasData = resumo !== null || evolucao.length > 0 || processos.length > 0;

  const savingsChartData = useMemo(
    () =>
      evolucao.map((item) => ({
        name: monthKeyToLabel(item.competencia),
        bruta: item.economia_bruta,
        liquida: item.economia_liquida_mes,
      })),
    [evolucao]
  );

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

  const processColumns = useMemo<DataTableColumn<DashboardProcessoItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        render: (row) => row.codigo_processo ?? "—",
      },
      {
        key: "nome",
        header: "Processo",
        className: "ds-table__col--wide",
        render: (row) => row.nome_processo ?? "—",
      },
      {
        key: "daily",
        header: "Economia/dia",
        className: "ds-table__col--numeric",
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
        key: "month",
        header: "Líquida no mês",
        className: "ds-table__col--numeric",
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
        header: "Bruta no mês",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.economia_bruta),
      },
    ],
    []
  );

  return (
    <div className="dashboard-transformometro dashboard-page">
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
            <button
              type="button"
              className="ds-ghost-btn"
              disabled={exportando || isBusy}
              onClick={() => void handleExportCsv()}
            >
              <Download size={16} />
              {exportando ? "Exportando…" : "Exportar CSV"}
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              disabled={recalculando || isBusy}
              onClick={() => void handleRecalcular()}
            >
              <RefreshCw size={16} />
              {recalculando ? "Recalculando…" : "Recalcular"}
            </button>
          </>
        }
      />

      <DataSourceBanner />

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={hasData}
        onRetry={() => void load()}
      />

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando dashboard"
          description="Atualizando KPIs, gráficos e ranking de processos."
          variant="compact"
          sticky
        />
      ) : null}

      {alertas.length > 0 ? (
        <section className="ds-card ds-alert-panel">
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
          title="Investimento único"
          value={formatCurrency(resumo?.investimento_unico_total)}
          subtitle="Soma no período"
          icon={<Coins size={22} />}
          loading={isBusy && !resumo}
        />
      </section>

      <section className="ds-chart-section">
        <ChartCard title="Economia no período" hint={periodLabel}>
          {savingsChartData.length === 0 && !isBusy ? (
            <p className="ds-state-box">
              Sem dados no período. Cadastre processos, execute Recalcular e ajuste os
              filtros de data.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={savingsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => formatCurrency(Number(v))} width={72} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Line
                  type="monotone"
                  dataKey="bruta"
                  name="Bruta"
                  stroke={CHART_COLORS[1]}
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="liquida"
                  name="Líquida"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      {topDailyChart.length > 0 ? (
        <section className="ds-charts-grid ds-charts-grid--single">
          <ChartCard title="Top economia diária" hint="10 maiores no recorte">
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={topDailyChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v))} />
                <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} maxBarSize={28}>
                  {topDailyChart.map((_, index) => (
                    <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </section>
      ) : null}

      <DataTableSection
        title="Processos no recorte"
        hint="Competência mais recente ou período filtrado"
        columns={processColumns}
        rows={processos}
        rowKey={(row) => row.processo_id}
        loading={loading}
        refreshing={refreshing}
        emptyMessage="Nenhum processo com economia calculada. Cadastre revisões e medições, depois Recalcular."
      />
    </div>
  );
}
