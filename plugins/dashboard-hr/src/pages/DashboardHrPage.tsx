import { useMemo } from "react";
import {
  Award,
  BookOpen,
  Smile,
  TrendingDown,
  UserMinus,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { CHART_COLORS } from "../constants/chartColors";
import { useHrDashboard } from "../hooks/useHrDashboard";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useHrFilters } from "../hooks/useHrFilters";
import type { HrBranchMetrics } from "../types/hr";
import { formatPeriodLabel } from "../utils/dates";
import { averageNullable, formatDecimal, formatPercent } from "../utils/format";

const CHART_HEIGHT = 280;

function pickBranchMetrics(
  snapshot: { branches: HrBranchMetrics[] } | null | undefined,
  branch: string
): HrBranchMetrics | null {
  if (!snapshot?.branches?.length) return null;
  if (branch) {
    return snapshot.branches.find((item) => item.branch_code === branch) ?? null;
  }
  return null;
}

function aggregateFromBranches(
  branches: HrBranchMetrics[],
  field: keyof Pick<
    HrBranchMetrics,
    | "absenteeism_pct"
    | "turnover_pct"
    | "training_hours_per_collaborator"
    | "active_pdi_pct"
  >
): number | null {
  return averageNullable(branches.map((item) => item[field]));
}

export function DashboardHrPage() {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
  } = useHrFilters();

  const { snapshot, branchOptions, loading, refreshing, requestProgress, error, reload } =
    useHrDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const isBusy = loading || refreshing;
  const hasData = snapshot !== null;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);
  const selectedBranch = pickBranchMetrics(snapshot, branch);

  const absenteeism = selectedBranch
    ? selectedBranch.absenteeism_pct
    : aggregateFromBranches(snapshot?.branches ?? [], "absenteeism_pct");

  const turnover = selectedBranch
    ? selectedBranch.turnover_pct
    : aggregateFromBranches(snapshot?.branches ?? [], "turnover_pct");

  const trainingHours = selectedBranch
    ? selectedBranch.training_hours_per_collaborator
    : aggregateFromBranches(
        snapshot?.branches ?? [],
        "training_hours_per_collaborator"
      );

  const activePdi = selectedBranch
    ? selectedBranch.active_pdi_pct
    : snapshot?.active_pdi_pct ??
      aggregateFromBranches(snapshot?.branches ?? [], "active_pdi_pct");

  const satisfaction = snapshot?.internal_satisfaction_pct ?? null;

  const branchChartData = useMemo(
    () =>
      (snapshot?.branches ?? []).map((item) => ({
        name: `Filial ${item.branch_code}`,
        absenteismo: item.absenteeism_pct ?? 0,
        turnover: item.turnover_pct ?? 0,
      })),
    [snapshot?.branches]
  );

  const trainingChartData = useMemo(
    () =>
      (snapshot?.branches ?? []).map((item) => ({
        name: `Filial ${item.branch_code}`,
        horas: item.training_hours_per_collaborator ?? 0,
      })),
    [snapshot?.branches]
  );

  const showBranchCharts = !branch && branchChartData.length > 0;

  return (
    <div className="dashboard-hr dashboard-page">
      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branchOptions={branchOptions}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
        refreshing={refreshing}
      />

      <DataSourceBanner />

      {error ? (
        <section className="dh-state dh-state--error" role="alert">
          <p>{error}</p>
          <button className="dh-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </section>
      ) : null}

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando indicadores de RH"
          description="Recalculando absenteísmo, turnover e treinamento com os filtros selecionados."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores de RH"
          description="Buscando absenteísmo, turnover, satisfação, PDI e horas de treinamento."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dh-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Absenteísmo"
          value={formatPercent(absenteeism)}
          subtitle={periodLabel}
          icon={<UserMinus size={22} />}
          loading={loading}
        />
        <KpiCard
          title="Turnover"
          value={formatPercent(turnover)}
          subtitle={periodLabel}
          icon={<TrendingDown size={22} />}
          loading={loading}
        />
        <KpiCard
          title="Satisfação interna"
          value={formatPercent(satisfaction)}
          subtitle="Consolidado no período"
          icon={<Smile size={22} />}
          loading={loading}
        />
        <KpiCard
          title="PDI ativos"
          value={formatPercent(activePdi)}
          subtitle={branch ? `Filial ${branch}` : "Média das filiais"}
          icon={<Award size={22} />}
          loading={loading}
        />
        <KpiCard
          title="Horas treinamento / colaborador"
          value={formatDecimal(trainingHours, 2)}
          subtitle={periodLabel}
          icon={<BookOpen size={22} />}
          loading={loading}
        />
      </section>

      {showBranchCharts ? (
        <section className="dh-charts-grid">
          <ChartCard
            title="Absenteísmo e turnover por filial"
            hint="Comparativo percentual no período."
          >
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={branchChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="absenteismo"
                  name="Absenteísmo %"
                  fill={CHART_COLORS[0]}
                  radius={[6, 6, 0, 0]}
                />
                <Bar
                  dataKey="turnover"
                  name="Turnover %"
                  fill={CHART_COLORS[1]}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Treinamento por filial"
            hint="Média de horas por participação."
          >
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={trainingChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar
                  dataKey="horas"
                  name="Horas"
                  fill={CHART_COLORS[2]}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </section>
      ) : null}

      <section className="dh-card dh-table-section">
        <div className="dh-table-section__header">
          <h2 className="dh-section-title">Detalhamento por filial</h2>
          <span className="dh-table-section__meta">
            {(snapshot?.branches.length ?? 0).toLocaleString("pt-BR")} filial(is)
          </span>
        </div>
        <div className="dh-table-wrap">
          <table className="dh-table">
            <thead>
              <tr>
                <th>Filial</th>
                <th className="dh-table__col--numeric">Absenteísmo</th>
                <th className="dh-table__col--numeric">Turnover</th>
                <th className="dh-table__col--numeric">Treinamento (h)</th>
                <th className="dh-table__col--numeric">PDI ativos</th>
              </tr>
            </thead>
            <tbody>
              {(snapshot?.branches ?? []).map((row) => (
                <tr key={row.branch_code}>
                  <td>{row.branch_code}</td>
                  <td className="dh-table__col--numeric">
                    {formatPercent(row.absenteeism_pct)}
                  </td>
                  <td className="dh-table__col--numeric">
                    {formatPercent(row.turnover_pct)}
                  </td>
                  <td className="dh-table__col--numeric">
                    {formatDecimal(row.training_hours_per_collaborator, 2)}
                  </td>
                  <td className="dh-table__col--numeric">
                    {formatPercent(row.active_pdi_pct)}
                  </td>
                </tr>
              ))}
              {!loading && (snapshot?.branches.length ?? 0) === 0 ? (
                <tr>
                  <td colSpan={5} className="dh-table__empty">
                    Nenhum dado de RH para o período selecionado.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
