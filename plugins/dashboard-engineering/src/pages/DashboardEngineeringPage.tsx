import { useMemo } from "react";
import { BarChart3, CircleGauge, Clock, Coins, Lightbulb, TrendingUp } from "lucide-react";

import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { ModuleShortcut } from "../components/ModuleShortcut";
import { EngineeringStatusAlerts } from "../components/EngineeringStatusAlerts";
import { ENGINEERING_ROUTES } from "../constants/routes";
import { useEngineeringDashboard } from "../hooks/useEngineeringDashboard";
import { useEngineeringFilters } from "../hooks/useEngineeringFilters";
import { formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatBranchFilterLabel, resolveApiBranch } from "../utils/branchClientFilters";
import {
  formatDecimal,
  formatInteger,
  formatRoiRatio,
} from "../utils/format";
import { ENGINEERING_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  EngineeringExportButtons,
  buildDashboardExportContext,
} from "../export";

const SHORTCUTS = [
  {
    title: "LMPs no prazo",
    description: "Gráficos, status por nível e lista de propostas/LMPs.",
    href: ENGINEERING_ROUTES.lmp,
  },
  {
    title: "TRANSFORMA+",
    description: "Ganhos, ROI, processos e economia diária na planilha.",
    href: ENGINEERING_ROUTES.transforma,
  },
] as const;

type DashboardEngineeringPageProps = {
  pathname?: string;
};

export function DashboardEngineeringPage({ pathname }: DashboardEngineeringPageProps) {
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
    filterState,
  } = useEngineeringFilters();

  const {
    transforma,
    lmpSummary,
    lmpBranches,
    transformaSavingsBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  } = useEngineeringDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = formatBranchFilterLabel(branches);
  const activeApiBranch = resolveApiBranch(branches);
  const isBusy = loading || refreshing;
  const hasData = transforma !== null || lmpSummary !== null;

  const kpiExportRows = useMemo(
    () => [
      {
        indicador: "% LMP dentro do prazo",
        valor: formatDashboardMetricValue(
          lmpSummary?.percent_dentro_prazo,
          lmpSummary,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Lead time médio (dias úteis)",
        valor: formatDecimal(lmpSummary?.avg_lead_time, 2),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Total de propostas",
        valor: formatInteger(
          lmpSummary?.total_items ?? lmpSummary?.total_lmps,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Ganhos brutos TRANSFORMA+",
        valor: formatDashboardMetricValue(
          transforma?.total_gross_savings_in_period,
          transforma,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Soluções implementadas",
        valor: formatInteger(transforma?.implemented_solutions_count),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "ROI médio TRANSFORMA+",
        valor: formatRoiRatio(transforma?.average_roi, 1),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
    ],
    [branchLabel, lmpSummary, periodLabel, transforma],
  );

  const dashboardExportContext = useMemo(
    () =>
      buildDashboardExportContext(
        {
          documentTitle: "dashboard-engenharia",
          periodLabel,
          scopeLabel: branchLabel,
        },
        kpiExportRows,
      ),
    [branchLabel, kpiExportRows, periodLabel],
  );

  return (
    <div className="dashboard-engineering dashboard-page">
      <FilterBar
        subtitle="Indicadores estratégicos de engenharia (LMP e TRANSFORMA+)"
        currentPath={pathname ?? ENGINEERING_ROUTES.home}
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
        exportActions={
          <EngineeringExportButtons
            variant="dashboard"
            context={dashboardExportContext}
            disabled={loading && !hasData}
          />
        }
      />
      <DataSourceBanner variant="all" />
      <EngineeringStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando visão geral"
        refreshDescription="Atualizando KPIs de LMP e TRANSFORMA+."
      />
      {Object.keys(sectionErrors).length > 0 && hasData ? (
        <div className="ds-state ds-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="% LMP dentro do prazo"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.lmpOnTime}
          value={formatDashboardMetricValue(
            lmpSummary?.percent_dentro_prazo,
            lmpSummary,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${branchLabel} · ${periodLabel}`,
            lmpSummary,
            {
              realizedValue: lmpSummary?.percent_dentro_prazo,
              activeBranch: activeApiBranch,
              branches: lmpBranches,
            },
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Lead time médio (dias úteis)"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.avgLeadTime}
          value={formatDecimal(lmpSummary?.avg_lead_time, 2)}
          contextLabel="Média no período"
          icon={<Clock size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Total de propostas"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.totalProposals}
          value={formatInteger(
            lmpSummary?.total_items ?? lmpSummary?.total_lmps
          )}
          contextLabel="LMPs / amostras no recorte"
          icon={<BarChart3 size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Ganhos brutos TRANSFORMA+"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.transformaSavings}
          value={formatDashboardMetricValue(
            transforma?.total_gross_savings_in_period,
            transforma,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${branchLabel} · ${periodLabel}`,
            transforma,
            {
              realizedValue: transforma?.total_gross_savings_in_period,
              activeBranch: activeApiBranch,
              branches: transformaSavingsBranches,
            },
          )}
          icon={<Coins size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Soluções implementadas"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.implementedSolutions}
          value={formatInteger(transforma?.implemented_solutions_count)}
          contextLabel="Melhorias na planilha"
          icon={<Lightbulb size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="ROI médio TRANSFORMA+"
          titleHint={ENGINEERING_HELP_TOOLTIPS.kpis.averageRoi}
          value={formatRoiRatio(transforma?.average_roi, 1)}
          {...buildKpiGoalPresentation(
            "No período filtrado",
            transforma,
            (v) => formatRoiRatio(v, 1),
            {
              realizedValue: transforma?.average_roi,
              showGoal: false,
            },
          )}
          icon={<TrendingUp size={22} />}
          loading={isBusy}
        />
      </section>
      <section className="ds-shortcuts-grid">
        {SHORTCUTS.map((item) => (
          <ModuleShortcut
            key={item.href}
            title={item.title}
            description={item.description}
            href={item.href}
            filterState={filterState}
          />
        ))}
      </section>
    </div>
  );
}