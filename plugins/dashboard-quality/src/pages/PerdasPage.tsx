import { useMemo } from "react";
import { Factory, Recycle } from "lucide-react";

import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { QUALITY_ROUTES } from "../constants/routes";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import { usePerdasPage } from "../hooks/usePerdasPage";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import { formatBranchFilterLabel, resolveApiBranch } from "../utils/branchClientFilters";
import { formatPeriodLabel } from "../utils/dates";
import { formatDecimal } from "../utils/format";
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";

const SCRAP_MONITORING_HREF = "/apps/scrap-monitoring";
const RETRABALHO_HREF = "/apps/controle-retrabalhos";

type PerdasPageProps = {
  pathname?: string;
};

function formatPctOrDash(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${formatDecimal(value)}%`;
}

export function PerdasPage({ pathname }: PerdasPageProps) {
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

  const { branches: branchOptions, loading: branchesLoading } =
    useQualityBranches(apiParams);

  const {
    scrap,
    rework,
    scrapBranches,
    reworkBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  } = usePerdasPage(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd],
  );
  const branchLabel = formatBranchFilterLabel(selectedBranches);
  const activeApiBranch = resolveApiBranch(selectedBranches);
  const hasData = scrap !== null || rework !== null;
  const isBusy = loading || refreshing;
  const initialLoadingProgress = useLoadingProgress(
    loading && !hasData,
    requestProgress,
  );
  const refreshLoadingProgress = useLoadingProgress(
    refreshing && hasData,
    requestProgress,
  );

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <FilterBar
        filterState={filterState}
        currentPath={pathname ?? QUALITY_ROUTES.perdas}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={selectedBranches}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        printDisabled={loading && !hasData}
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

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando perdas"
          description="Recalculando custo de refugo e retrabalho sobre o ROL."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando perdas"
          description="Buscando custo de refugo × ROL e custo de retrabalho × ROL."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dq-kpi-section" aria-busy={isBusy}>
        <div className="dq-kpi-grid">
          <KpiCard
            title="Custo de Refugo × ROL"
            titleHint={QUALITY_HELP_TOOLTIPS.kpis.scrapCostPct}
            value={formatDashboardMetricValue(scrap?.scrap_cost_pct, scrap)}
            {...buildKpiGoalPresentationWithBranchIdd(
              `Custo: R$ ${formatDecimal(scrap?.scrap_cost)} · ${branchLabel} · ${periodLabel}`,
              scrap,
              {
                realizedValue: scrap?.scrap_cost_pct,
                activeBranch: activeApiBranch,
                branches: scrapBranches,
              },
            )}
            icon={<Factory size={22} />}
            loading={isBusy}
          />
          <KpiCard
            title="Custo de Retrabalho × ROL"
            titleHint={QUALITY_HELP_TOOLTIPS.kpis.reworkCostPct}
            value={formatDashboardMetricValue(rework?.rework_cost_pct, rework)}
            {...buildKpiGoalPresentationWithBranchIdd(
              `Custo: R$ ${formatDecimal(rework?.rework_cost)} · ${branchLabel} · ${periodLabel}`,
              rework,
              {
                realizedValue: rework?.rework_cost_pct,
                activeBranch: activeApiBranch,
                branches: reworkBranches,
              },
            )}
            icon={<Recycle size={22} />}
            loading={isBusy}
          />
        </div>
      </section>

      <section className="dq-module-shortcuts" aria-label="Acompanhar refugos e retrabalhos">
        <h2 className="dq-section-title">Acompanhar</h2>
        <p className="dq-section-subtitle">
          Detalhamento operacional nos plugins de refugo e retrabalho
          {hasData ? ` · período ${periodLabel}` : ""}.
        </p>
        <div className="dq-module-shortcut-grid">
          <a
            href={SCRAP_MONITORING_HREF}
            className="dq-card dq-module-shortcut dq-module-shortcut--link"
          >
            <h3 className="dq-module-shortcut__title">Acompanhamento de Refugos</h3>
            <p className="dq-module-shortcut__description">
              Rankings, séries e registros de refugo no TOTVS
              {scrap?.scrap_cost_pct != null
                ? ` · KPI atual ${formatPctOrDash(scrap.scrap_cost_pct)}`
                : ""}
              .
            </p>
          </a>
          <a
            href={RETRABALHO_HREF}
            className="dq-card dq-module-shortcut dq-module-shortcut--link"
          >
            <h3 className="dq-module-shortcut__title">Controle de Retrabalhos</h3>
            <p className="dq-module-shortcut__description">
              Horas, custos e detalhamento de retrabalho
              {rework?.rework_cost_pct != null
                ? ` · KPI atual ${formatPctOrDash(rework.rework_cost_pct)}`
                : ""}
              .
            </p>
          </a>
        </div>
      </section>
    </div>
  );
}
