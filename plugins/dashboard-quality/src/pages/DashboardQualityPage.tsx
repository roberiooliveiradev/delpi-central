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
import { ModuleShortcut, PPM_SHORTCUT_HREF } from "../components/ModuleShortcut";
import { QUALITY_ROUTES } from "../constants/routes";
import { QUALITY_SI_INDICATORS } from "../constants/siIndicatorIds";
import {
  QualityExportButtons,
  buildDashboardExportContext,
} from "../export";
import {
  formatQualityKpiValue,
  formatQualityPercentKpi,
} from "../export/qualityDashboardSheets";
import { useDepartmentIndicatorScores } from "../hooks/useDepartmentIndicatorScores";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityDashboard } from "../hooks/useQualityDashboard";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useQualityFilters } from "../hooks/useQualityFilters";
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
  formatKpiGoalExportFragments,
  joinKpiExportContext,
  pickSiIddScoreLabel,
} from "../utils/goalDisplay";
import { resolveApiBranch } from "../utils/branchClientFilters";
import {
  formatDecimal,
} from "../utils/format";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
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

  const { scoresById: siScoresById } = useDepartmentIndicatorScores("quality", {
    competence,
    dateStart,
    dateEnd,
    branches: selectedBranches,
  });

  const printDisabled = loading && !ppmInternal;

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const activeApiBranch = resolveApiBranch(selectedBranches);
  const branchLabel = formatBranchFilterLabel(selectedBranches);

  const isBusy = loading || refreshing;
  const hasData = ppmInternal !== null;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

  const kpiExportRows = useMemo(
    () => {
      const dateOpts = { dateStart, dateEnd };
      const ppmInternalGoal = buildKpiGoalPresentationWithBranchIdd(
        `Devolvido: ${formatDecimal(ppmInternal?.total_devolvido_un)} un · ${periodLabel}`,
        ppmInternal,
        {
          realizedValue: ppmInternal?.ppm,
          activeBranch: activeApiBranch,
          branches: ppmInternalBranches,
          iddScoreLabel: pickSiIddScoreLabel(
            siScoresById,
            QUALITY_SI_INDICATORS.ppmInternal,
          ),
          ...dateOpts,
        },
      );
      const ppmExternalGoal = buildKpiGoalPresentationWithBranchIdd(
        `Devolvido: ${formatDecimal(ppmExternal?.total_devolvido_un)} un · ${periodLabel}`,
        ppmExternal,
        {
          realizedValue: ppmExternal?.ppm,
          activeBranch: activeApiBranch,
          branches: ppmExternalBranches,
          iddScoreLabel: pickSiIddScoreLabel(
            siScoresById,
            QUALITY_SI_INDICATORS.ppmExternal,
          ),
          ...dateOpts,
        },
      );
      const kaizenIdeasGoal = buildKpiGoalPresentationWithBranchIdd(
        periodLabel,
        kaizen?.ideas_goal ?? kaizen,
        {
          realizedValue: kaizen?.total_kaizens,
          activeBranch: activeApiBranch,
          branches: kaizenIdeasBranches,
          iddScoreLabel: pickSiIddScoreLabel(
            siScoresById,
            QUALITY_SI_INDICATORS.kaizenIdeas,
          ),
          ...dateOpts,
        },
      );
      const audit5sGoal = buildKpiGoalPresentationWithBranchIdd(
        periodLabel,
        audit5s,
        {
          realizedValue: audit5s?.average_score,
          activeBranch: activeApiBranch,
          branches: audit5sBranches,
          iddScoreLabel: pickSiIddScoreLabel(
            siScoresById,
            QUALITY_SI_INDICATORS.audit5s,
          ),
          ...dateOpts,
        },
      );

      return [
      {
        indicador: "PPM interno",
        valor: formatQualityKpiValue(ppmInternal?.ppm),
        contexto: joinKpiExportContext(
          `Devolvido: ${formatDecimal(ppmInternal?.total_devolvido_un)} un · ${branchLabel} · ${periodLabel}`,
          ...formatKpiGoalExportFragments(ppmInternalGoal),
        ),
      },
      {
        indicador: "PPM externo",
        valor: formatQualityKpiValue(ppmExternal?.ppm),
        contexto: joinKpiExportContext(
          `Devolvido: ${formatDecimal(ppmExternal?.total_devolvido_un)} un · ${branchLabel} · ${periodLabel}`,
          ...formatKpiGoalExportFragments(ppmExternalGoal),
        ),
      },
      {
        indicador: "Kaizens",
        valor: formatQualityKpiValue(kaizen?.total_kaizens, (v) => String(Math.round(v))),
        contexto: joinKpiExportContext(
          `Economia: ${formatDecimal(kaizen?.total_savings)} · ${branchLabel} · ${periodLabel}`,
          ...formatKpiGoalExportFragments(kaizenIdeasGoal),
        ),
      },
      {
        indicador: "Auditoria 5S",
        valor: formatQualityPercentKpi(audit5s?.average_score),
        contexto: joinKpiExportContext(
          `${branchLabel} · ${periodLabel}`,
          ...formatKpiGoalExportFragments(audit5sGoal),
        ),
      },
    ];
    },
    [
      activeApiBranch,
      audit5s,
      audit5sBranches,
      branchLabel,
      dateEnd,
      dateStart,
      kaizen,
      kaizenIdeasBranches,
      periodLabel,
      ppmExternal,
      ppmExternalBranches,
      ppmInternal,
      ppmInternalBranches,
      siScoresById,
    ],
  );

  const dashboardExportContext = useMemo(
    () =>
      buildDashboardExportContext(
        {
          documentTitle: "dashboard-qualidade",
          periodLabel,
          scopeLabel: branchLabel,
        },
        kpiExportRows,
        [],
      ),
    [branchLabel, kpiExportRows, periodLabel],
  );

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
        exportActions={
          <QualityExportButtons
            variant="dashboard"
            context={dashboardExportContext}
            disabled={loading && !hasData}
          />
        }
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

      <section className="dq-kpi-section" aria-busy={isBusy}>
        <div className="dq-kpi-grid">
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
                dateStart,
                dateEnd,
                iddScoreLabel: pickSiIddScoreLabel(
                  siScoresById,
                  QUALITY_SI_INDICATORS.ppmInternal,
                ),
              },
            )}
            icon={<Factory size={22} />}
            loading={isBusy}
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
                dateStart,
                dateEnd,
                iddScoreLabel: pickSiIddScoreLabel(
                  siScoresById,
                  QUALITY_SI_INDICATORS.ppmExternal,
                ),
              },
            )}
            icon={<Truck size={22} />}
            loading={isBusy}
          />
        </div>
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
              dateStart,
              dateEnd,
              iddScoreLabel: pickSiIddScoreLabel(
                siScoresById,
                QUALITY_SI_INDICATORS.kaizenIdeas,
              ),
            },
          )}
          icon={<Lightbulb size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Ganhos financeiros do kaizen"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.kaizenFinancialGains}
          value={formatDashboardMetricValue(kaizen?.total_savings, kaizen)}
          {...buildKpiGoalPresentationWithBranchIdd(periodLabel, kaizen, {
            realizedValue: kaizen?.total_savings,
            activeBranch: activeApiBranch,
            branches: kaizenSavingsBranches,
            dateStart,
            dateEnd,
            iddScoreLabel: pickSiIddScoreLabel(
              siScoresById,
              QUALITY_SI_INDICATORS.kaizenFinancial,
            ),
          })}
          icon={<Wallet size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Auditoria 5S"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.audit5sScore}
          value={formatDashboardMetricValue(audit5s?.average_score, audit5s)}
          {...buildKpiGoalPresentationWithBranchIdd(periodLabel, audit5s, {
            realizedValue: audit5s?.average_score,
            activeBranch: activeApiBranch,
            branches: audit5sBranches,
            dateStart,
            dateEnd,
            iddScoreLabel: pickSiIddScoreLabel(
              siScoresById,
              QUALITY_SI_INDICATORS.audit5s,
            ),
          })}
          icon={<ClipboardCheck size={22} />}
          loading={isBusy}
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
