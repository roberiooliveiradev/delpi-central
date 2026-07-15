import { useMemo } from "react";
import {
  Award,
  BookOpen,
  ClipboardCheck,
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
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
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
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import {
  buildHrMetricIddSlices,
  buildHrSatisfactionIddSlices,
} from "../utils/hrBranchIdd";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import { averageNullable, formatDecimal, formatPercent, sumNullable } from "../utils/format";
import { HR_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  HrExportButtons,
  buildDashboardExportContext,
} from "../export";
import { buildHrBranchesExportPayload } from "../export/hrDashboardSheets";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

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
    | "active_pdi_count"
    | "performance_reviews_completion_pct"
  >,
  mode: "average" | "sum" = "average"
): number | null {
  const values = branches.map((item) => item[field]);
  return mode === "sum" ? sumNullable(values) : averageNullable(values);
}

export function DashboardHrPage() {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    apiParams,
  } = useHrFilters();

  const { snapshot, branchGoalSnapshots, branchOptions, loading, refreshing, requestProgress, error, reload } =
    useHrDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = formatBranchFilterLabel(branches);

  const isBusy = loading || refreshing;
  const hasData = snapshot !== null;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);
  const selectedBranch =
    branches.length === 1 ? pickBranchMetrics(snapshot, branches[0]) : null;
  const activeApiBranch = resolveApiBranch(branches);

  const absenteeismBranches = useMemo(
    () =>
      buildHrMetricIddSlices(
        snapshot,
        branchGoalSnapshots,
        "absenteeism_pct",
        "absenteeism_pct",
      ),
    [snapshot, branchGoalSnapshots],
  );
  const turnoverBranches = useMemo(
    () =>
      buildHrMetricIddSlices(
        snapshot,
        branchGoalSnapshots,
        "turnover_pct",
        "turnover_pct",
      ),
    [snapshot, branchGoalSnapshots],
  );
  const satisfactionBranches = useMemo(
    () => buildHrSatisfactionIddSlices(snapshot, branchGoalSnapshots),
    [snapshot, branchGoalSnapshots],
  );
  const activePdiBranches = useMemo(
    () =>
      buildHrMetricIddSlices(
        snapshot,
        branchGoalSnapshots,
        "active_pdi_count",
        "active_pdi_count",
      ),
    [snapshot, branchGoalSnapshots],
  );
  const performanceReviewsBranches = useMemo(
    () =>
      buildHrMetricIddSlices(
        snapshot,
        branchGoalSnapshots,
        "performance_reviews_completion_pct",
        "performance_reviews_completion_pct",
      ),
    [snapshot, branchGoalSnapshots],
  );
  const trainingHoursBranches = useMemo(
    () =>
      buildHrMetricIddSlices(
        snapshot,
        branchGoalSnapshots,
        "training_hours_per_collaborator",
        "training_hours_per_collaborator",
      ),
    [snapshot, branchGoalSnapshots],
  );

  const activeBranches = useMemo(() => {
    const all = snapshot?.branches ?? [];
    if (branches.length === 0) return all;
    return all.filter((item) => branches.includes(item.branch_code));
  }, [snapshot?.branches, branches]);

  const absenteeism = selectedBranch
    ? selectedBranch.absenteeism_pct
    : aggregateFromBranches(activeBranches, "absenteeism_pct");

  const turnover = selectedBranch
    ? selectedBranch.turnover_pct
    : aggregateFromBranches(activeBranches, "turnover_pct");

  const trainingHours = selectedBranch
    ? selectedBranch.training_hours_per_collaborator
    : aggregateFromBranches(
        activeBranches,
        "training_hours_per_collaborator"
      );

  const activePdiCount = selectedBranch
    ? selectedBranch.active_pdi_count
    : snapshot?.active_pdi_count ??
      aggregateFromBranches(activeBranches, "active_pdi_count", "sum");

  const performanceReviewsCompletion = selectedBranch
    ? selectedBranch.performance_reviews_completion_pct
    : snapshot?.performance_reviews_completion_pct ??
      aggregateFromBranches(
        activeBranches,
        "performance_reviews_completion_pct",
        "average"
      );

  const satisfaction = snapshot?.internal_satisfaction_pct ?? null;

  const branchChartData = useMemo(
    () =>
      (snapshot?.branches ?? []).map((item) => ({
        name: formatOperationalUnitCode(item.branch_code, item.branch_code),
        absenteismo: item.absenteeism_pct ?? 0,
        turnover: item.turnover_pct ?? 0,
      })),
    [snapshot?.branches]
  );

  const trainingChartData = useMemo(
    () =>
      (snapshot?.branches ?? []).map((item) => ({
        name: formatOperationalUnitCode(item.branch_code, item.branch_code),
        horas: item.training_hours_per_collaborator ?? 0,
      })),
    [snapshot?.branches]
  );

  const showBranchCharts = branches.length === 0 && branchChartData.length > 0;

  const branchTableRows = useMemo(
    () => snapshot?.branches ?? [],
    [snapshot?.branches]
  );

  const branchColumns = useMemo<DataTableColumn<HrBranchMetrics>[]>(
    () => [
      {
        key: "branch_code",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        headerHint: HR_HELP_TOOLTIPS.table.branch,
        render: (row) => formatOperationalUnitCode(row.branch_code),
      },
      {
        key: "absenteeism_pct",
        header: "Absenteísmo",
        className: "dh-table__col--numeric",
        render: (row) => formatPercent(row.absenteeism_pct),
      },
      {
        key: "turnover_pct",
        header: "Turnover",
        className: "dh-table__col--numeric",
        render: (row) => formatPercent(row.turnover_pct),
      },
      {
        key: "training_hours_per_collaborator",
        header: "Treinamento (h)",
        className: "dh-table__col--numeric",
        render: (row) => formatDecimal(row.training_hours_per_collaborator, 2),
      },
      {
        key: "active_pdi_count",
        header: "PDIs ativos",
        className: "dh-table__col--numeric",
        render: (row) => formatDecimal(row.active_pdi_count, 0),
      },
      {
        key: "performance_reviews_completion_pct",
        header: "Avaliações concluídas",
        className: "dh-table__col--numeric",
        render: (row) => formatPercent(row.performance_reviews_completion_pct),
      },
    ],
    []
  );

  const kpiExportRows = useMemo(
    () => [
      {
        indicador: "Absenteísmo",
        valor: formatPercent(absenteeism),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Turnover",
        valor: formatPercent(turnover),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Satisfação interna",
        valor: formatPercent(satisfaction),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "PDIs ativos",
        valor: formatDecimal(activePdiCount, 0),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Avaliações concluídas",
        valor: formatPercent(performanceReviewsCompletion),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Horas de treinamento / colaborador",
        valor: formatDecimal(trainingHours, 2),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
    ],
    [
      absenteeism,
      activePdiCount,
      branchLabel,
      performanceReviewsCompletion,
      periodLabel,
      satisfaction,
      trainingHours,
      turnover,
    ],
  );

  const dashboardExportContext = useMemo(
    () =>
      buildDashboardExportContext(
        {
          documentTitle: "dashboard-rh",
          periodLabel,
          scopeLabel: branchLabel,
        },
        kpiExportRows,
        branchTableRows.length > 0
          ? [buildHrBranchesExportPayload(branchTableRows)]
          : [],
      ),
    [branchLabel, branchTableRows, kpiExportRows, periodLabel],
  );

  return (
    <div className="dashboard-hr dashboard-page">
      <FilterBar
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        branchOptions={branchOptions}
        onCompetenceChange={setCompetence}
        onBranchesChange={setBranches}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onRefresh={reload}
        refreshing={refreshing}
        exportActions={
          <HrExportButtons
            variant="dashboard"
            context={dashboardExportContext}
            disabled={loading && !hasData}
          />
        }
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
          description="Buscando absenteísmo, turnover, satisfação, PDIs, avaliações e horas de treinamento."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dh-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Absenteísmo"
          titleHint={HR_HELP_TOOLTIPS.kpis.absenteeism}
          value={formatDashboardMetricValue(
            absenteeism,
            snapshot?.goals_by_metric?.absenteeism_pct,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            periodLabel,
            snapshot?.goals_by_metric?.absenteeism_pct,
            {
              realizedValue: absenteeism,
              activeBranch: activeApiBranch,
              branches: absenteeismBranches,
            },
          )}
          icon={<UserMinus size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Turnover"
          titleHint={HR_HELP_TOOLTIPS.kpis.turnover}
          value={formatDashboardMetricValue(
            turnover,
            snapshot?.goals_by_metric?.turnover_pct,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            periodLabel,
            snapshot?.goals_by_metric?.turnover_pct,
            {
              realizedValue: turnover,
              activeBranch: activeApiBranch,
              branches: turnoverBranches,
            },
          )}
          icon={<TrendingDown size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Satisfação interna"
          titleHint={HR_HELP_TOOLTIPS.kpis.internalSatisfaction}
          value={formatDashboardMetricValue(
            satisfaction,
            snapshot?.goals_by_metric?.internal_satisfaction_pct,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            "Consolidado no período",
            snapshot?.goals_by_metric?.internal_satisfaction_pct,
            {
              realizedValue: satisfaction,
              activeBranch: activeApiBranch,
              branches: satisfactionBranches,
            },
          )}
          icon={<Smile size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Número de PDIs ativos"
          titleHint={HR_HELP_TOOLTIPS.kpis.activePdi}
          value={formatDashboardMetricValue(
            activePdiCount,
            snapshot?.goals_by_metric?.active_pdi_count,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            branches.length === 1
              ? formatOperationalUnitCode(branches[0], branches[0])
              : branches.length > 1
                ? branches.map((b) => formatOperationalUnitCode(b, b)).join(", ")
                : "Soma das unidades",
            snapshot?.goals_by_metric?.active_pdi_count,
            {
              realizedValue: activePdiCount,
              activeBranch: activeApiBranch,
              branches: activePdiBranches,
            },
          )}
          icon={<Award size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="% de Avaliações de Desempenho Concluídas"
          titleHint={HR_HELP_TOOLTIPS.kpis.performanceReviews}
          value={formatDashboardMetricValue(
            performanceReviewsCompletion,
            snapshot?.goals_by_metric?.performance_reviews_completion_pct,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            branches.length === 1
              ? formatOperationalUnitCode(branches[0], branches[0])
              : branches.length > 1
                ? branches.map((b) => formatOperationalUnitCode(b, b)).join(", ")
                : "Média das unidades",
            snapshot?.goals_by_metric?.performance_reviews_completion_pct,
            {
              realizedValue: performanceReviewsCompletion,
              activeBranch: activeApiBranch,
              branches: performanceReviewsBranches,
            },
          )}
          icon={<ClipboardCheck size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Horas treinamento / colaborador"
          titleHint={HR_HELP_TOOLTIPS.kpis.trainingHours}
          value={formatDashboardMetricValue(
            trainingHours,
            snapshot?.goals_by_metric?.training_hours_per_collaborator,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            periodLabel,
            snapshot?.goals_by_metric?.training_hours_per_collaborator,
            {
              realizedValue: trainingHours,
              activeBranch: activeApiBranch,
              branches: trainingHoursBranches,
            },
          )}
          icon={<BookOpen size={22} />}
          loading={isBusy}
        />
      </section>

      {showBranchCharts ? (
        <section className="dh-charts-grid">
          <ChartCard
            title="Absenteísmo e turnover por unidade"
            titleHint={HR_HELP_TOOLTIPS.charts.absenteeismTurnoverByBranch}
            hint="Comparativo percentual no período."
          >
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={branchChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
                <YAxis tick={{ fontSize: 11 }} />
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
            title="Treinamento por unidade"
            titleHint={HR_HELP_TOOLTIPS.charts.trainingByBranch}
            hint="Média de horas por participação."
          >
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={trainingChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
                <YAxis tick={{ fontSize: 11 }} />
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

      <DataTableSection
        columnPreferencesKey="dashboard-hr:DashboardHrPage:detalhamento-por-unidade:v1"
        title="Detalhamento por unidade"
        titleHint={HR_HELP_TOOLTIPS.table.section}
        hint={periodLabel}
        columns={branchColumns}
        rows={branchTableRows}
        rowKey={(row) => row.branch_code}
        loading={loading && !hasData}
        refreshing={refreshing && hasData}
        emptyMessage="Nenhum dado de RH para o período selecionado."
        searchPlaceholder="Buscar unidade…"
        searchHint={HR_HELP_TOOLTIPS.table.search}
        getSearchText={(row) => row.branch_code}
      />
    </div>
  );
}