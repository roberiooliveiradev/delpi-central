import { useMemo } from "react";
import {
  ClipboardCheck,
  Factory,
  Lightbulb,
  Truck,
  Wallet,
} from "lucide-react";

import { FilterBar } from "../components/FilterBar";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { KpiCard } from "../components/KpiCard";
import { PpmSparkline } from "../components/PpmSparkline";
import { ModuleShortcut, PPM_SHORTCUT_HREF } from "../components/ModuleShortcut";
import { QUALITY_ROUTES } from "../constants/routes";
import { CHART_COLORS } from "../constants/chartColors";
import { usePpmChartSeries } from "../hooks/usePpmChartSeries";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityDashboard } from "../hooks/useQualityDashboard";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useQualityFilters } from "../hooks/useQualityFilters";
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { resolveApiBranch } from "../utils/branchClientFilters";
import {
  formatDecimal,
} from "../utils/format";
import { formatPeriodLabel } from "../utils/dates";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";

const MODULE_SHORTCUTS = [
  {
    title: "PPM detalhado",
    description: "Listagem interna e externa com paginação.",
    href: PPM_SHORTCUT_HREF,
  },
  {
    title: "Não conformidades",
    description: "Consulta analítica de NC no Protheus.",
    href: QUALITY_ROUTES.nonconformities,
  },
  {
    title: "Kaizens",
    description: "Lista e filtros por status e setor.",
    href: QUALITY_ROUTES.kaizen,
  },
  {
    title: "Auditoria 5S",
    description: "Histórico e notas por área.",
    href: QUALITY_ROUTES.audit5s,
  },
] as const;

type DashboardQualityPageProps = {
  pathname?: string;
};

export function DashboardQualityPage({ pathname }: DashboardQualityPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches: selectedBranches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    apiParams,
    filterState,
  } = useQualityFilters();

  const { branches: branchOptions, loading: branchesLoading } = useQualityBranches(apiParams);

  const {
    ppmInternal,
    ppmExternal,
    kaizen,
    audit5s,
    ppmInternalBranches,
    ppmExternalBranches,
    kaizenIdeasBranches,
    kaizenSavingsBranches,
    audit5sBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  } = useQualityDashboard(apiParams);

  const printDisabled = loading && !ppmInternal;

  const internalSparkline = usePpmChartSeries({
    type: "internal",
    filters: apiParams,
    granularity: "month",
  });

  const externalSparkline = usePpmChartSeries({
    type: "external",
    filters: apiParams,
    granularity: "month",
  });

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const activeApiBranch = resolveApiBranch(selectedBranches);

  const isBusy = loading || refreshing;
  const hasData = ppmInternal !== null;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <FilterBar
        filterState={filterState}
        currentPath={pathname ?? QUALITY_ROUTES.home}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={selectedBranches}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        printDisabled={printDisabled}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onRefresh={reload}
        refreshing={refreshing}
      />

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="dq-state dq-state--warning" role="status">
          <p>Alguns indicadores não carregaram. Os demais permanecem disponíveis.</p>
        </div>
      ) : null}

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando indicadores de qualidade"
          description="Recalculando PPM, kaizens e auditorias 5S com os filtros selecionados."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores de qualidade"
          description="Buscando PPM interno e externo, kaizens e auditorias 5S."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dq-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="PPM interno"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.ppmInternal}
          value={formatDashboardMetricValue(ppmInternal?.ppm, ppmInternal)}
          {...buildKpiGoalPresentationWithBranchIdd(
            `Devolvido: ${formatDecimal(ppmInternal?.total_devolvido_un)} un · ${periodLabel}`,
            ppmInternal,
            {
              realizedValue: ppmInternal?.ppm,
              activeBranch: activeApiBranch,
              branches: ppmInternalBranches,
            },
          )}
          icon={<Factory size={22} />}
          loading={isBusy && !ppmInternal}
          footer={
            <PpmSparkline
              data={internalSparkline.points}
              loading={internalSparkline.loading}
            />
          }
        />
        <KpiCard
          title="PPM externo"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.ppmExternal}
          value={formatDashboardMetricValue(ppmExternal?.ppm, ppmExternal)}
          {...buildKpiGoalPresentationWithBranchIdd(
            `Devolvido: ${formatDecimal(ppmExternal?.total_devolvido_un)} un · ${periodLabel}`,
            ppmExternal,
            {
              realizedValue: ppmExternal?.ppm,
              activeBranch: activeApiBranch,
              branches: ppmExternalBranches,
            },
          )}
          icon={<Truck size={22} />}
          loading={isBusy && !ppmExternal}
          footer={
            <PpmSparkline
              data={externalSparkline.points}
              color={CHART_COLORS[1]}
              loading={externalSparkline.loading}
            />
          }
        />
      </section>

      <section className="dq-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Ideias aprovadas para Kaizen/mês"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.kaizenIdeas}
          value={formatDashboardMetricValue(
            kaizen?.total_kaizens,
            kaizen?.ideas_goal ?? kaizen,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            periodLabel,
            kaizen?.ideas_goal ?? kaizen,
            {
              realizedValue: kaizen?.total_kaizens,
              activeBranch: activeApiBranch,
              branches: kaizenIdeasBranches,
            },
          )}
          icon={<Lightbulb size={22} />}
          loading={isBusy && !kaizen}
        />
        <KpiCard
          title="Ganhos financeiros do kaizen"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.kaizenFinancialGains}
          value={formatDashboardMetricValue(kaizen?.total_savings, kaizen)}
          {...buildKpiGoalPresentationWithBranchIdd(periodLabel, kaizen, {
            realizedValue: kaizen?.total_savings,
            activeBranch: activeApiBranch,
            branches: kaizenSavingsBranches,
          })}
          icon={<Wallet size={22} />}
          loading={isBusy && !kaizen}
        />
        <KpiCard
          title="Auditoria 5S"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.audit5sScore}
          value={formatDashboardMetricValue(audit5s?.average_score, audit5s)}
          {...buildKpiGoalPresentationWithBranchIdd(periodLabel, audit5s, {
            realizedValue: audit5s?.average_score,
            activeBranch: activeApiBranch,
            branches: audit5sBranches,
          })}
          icon={<ClipboardCheck size={22} />}
          loading={isBusy && !audit5s}
        />
      </section>

      <section className="dq-shortcuts-section">
        <h2 className="dq-section-title">Módulos</h2>
        <div className="dq-shortcuts-grid">
          {MODULE_SHORTCUTS.map((item) => (
            <ModuleShortcut key={item.title} {...item} filterState={filterState} />
          ))}
        </div>
      </section>
    </div>
  );
}