import { useMemo, type ReactNode } from "react";
import {
  BarChart3,
  CircleGauge,
  Clock,
  Coins,
  Lightbulb,
  RefreshCw,
  TrendingUp,
} from "lucide-react";

import { buildEngineeringPath, navigateEngineeringView } from "../../app/engineeringRoutes";
import { HOME_COPY } from "../../content/engineeringRouteCatalog";
import {
  EngineeringActionButton,
  EngineeringDateField,
  EngineeringEmptyState,
  EngineeringKpiCard,
  EngineeringLoadingActivityCard,
  EngineeringMultiSelectField,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringQuickPeriodSelector,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../../ui/engineeringUi";
import { OPERATIONAL_UNIT_OPTIONS } from "@delpi/plugin-ui/index";
import { buildOverviewCards } from "./overviewViewModel";
import { useOverviewData } from "./useOverviewData";

/** Permissão Core do Portal TRANSFORMA+ — o atalho só aparece quando o
 * host comprova acesso efetivo (nunca derivado de claims do JWT). */
const TRANSFORMA_ACCESS_PERMISSION = "transformometro.access";
const TRANSFORMA_HREF = "/apps/transformometro";

const KPI_ICONS: Record<string, ReactNode> = {
  lmp_on_time: <CircleGauge size={22} aria-hidden="true" />,
  lmp_lead_time: <Clock size={22} aria-hidden="true" />,
  lmp_total_proposals: <BarChart3 size={22} aria-hidden="true" />,
  transforma_gross_savings: <Coins size={22} aria-hidden="true" />,
  transforma_solutions: <Lightbulb size={22} aria-hidden="true" />,
  transforma_roi: <TrendingUp size={22} aria-hidden="true" />,
};

type OverviewPageProps = {
  basePath: string;
  /** Permissões efetivas resolvidas pelo host/Core — só governam a
   * exibição do atalho TRANSFORMA+, nunca a autorização dos dados. */
  permissions?: readonly string[];
};

/** Visão geral — seis indicadores oficiais (3 LMP + 3 TRANSFORMA+) via
 * `GET /apps/engineering-api/v1/overview`. Estados por indicador:
 * available/empty/unavailable/forbidden — nunca zero silencioso. */
export function OverviewPage({ basePath, permissions }: OverviewPageProps) {
  const copy = HOME_COPY.overview;
  const {
    state,
    filters,
    refreshing,
    setPreset,
    setCompetence,
    setDateStart,
    setDateEnd,
    setBranch,
    reload,
  } = useOverviewData();

  const overview = state.phase === "ready" ? state.overview : null;
  const cards = useMemo(
    () => (overview ? buildOverviewCards(overview) : []),
    [overview],
  );
  const lmpCards = cards.filter((card) => card.family === "lmp");
  const transformaCards = cards.filter(
    (card) => card.family === "transforma",
  );
  const hasPartial = overview?.status === "partial";

  // Atalho TRANSFORMA+ apenas com permissão efetiva comprovada pela
  // Core/host — sem CTA desabilitado insinuando acesso (doc 18, G5.2).
  const hasTransformaAccess = useMemo(
    () => new Set(permissions ?? []).has(TRANSFORMA_ACCESS_PERMISSION),
    [permissions],
  );

  return (
    <>
      <EngineeringPagePath
        back={{
          label: "Início",
          href: buildEngineeringPath("home", basePath),
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home", { basePath });
          },
        }}
        items={[]}
        current={copy.pageTitle}
      />

      <EngineeringPageHero
        eyebrow={copy.eyebrow}
        title={copy.pageTitle}
        description={copy.description}
        actions={
          <EngineeringActionButton
            variant="ghost"
            onClick={reload}
            disabled={refreshing}
            aria-label={copy.refreshAriaLabel}
          >
            <RefreshCw size={16} aria-hidden="true" />{" "}
            {refreshing ? copy.refreshingLabel : copy.refreshLabel}
          </EngineeringActionButton>
        }
      >
        <div
          className="engineering-overview-filters"
          role="group"
          aria-label={copy.filtersAriaLabel}
        >
          <EngineeringQuickPeriodSelector
            label={copy.quickPeriodLabel}
            value={filters.preset}
            onChange={setPreset}
            idPrefix="overview-period"
          />
          <div className="engineering-overview-filters__fields">
            <EngineeringDateField
              label={copy.dateStartLabel}
              value={filters.dateStart}
              onChange={setDateStart}
            />
            <EngineeringDateField
              label={copy.dateEndLabel}
              value={filters.dateEnd}
              onChange={setDateEnd}
            />
            <EngineeringDateField
              label={copy.competenceLabel}
              type="month"
              value={filters.competence}
              onChange={setCompetence}
            />
            <EngineeringMultiSelectField
              label={copy.branchLabel}
              options={[...OPERATIONAL_UNIT_OPTIONS]}
              selectedValues={filters.branch ? [filters.branch] : []}
              onChange={(values) => setBranch(values[0] ?? "")}
              maxSelected={1}
            />
          </div>
        </div>
      </EngineeringPageHero>

      {state.phase === "loading" ? (
        <EngineeringLoadingActivityCard
          title={copy.loadingTitle}
          description={copy.loadingDescription}
        />
      ) : null}

      {state.phase === "error" ? (
        <EngineeringStateBanner variant="error">
          {state.error.message || copy.errorFallback}
        </EngineeringStateBanner>
      ) : null}

      {overview ? (
        <>
          {hasPartial ? (
            <EngineeringStateBanner variant="default">
              {copy.partialNotice}
            </EngineeringStateBanner>
          ) : null}

          <div
            className="engineering-overview-kpi-grid"
            role="list"
            aria-label={copy.kpiGridAriaLabel}
          >
            {lmpCards.map((card) => (
              <EngineeringKpiCard
                key={card.id}
                title={card.title}
                titleHint={card.titleHint}
                value={card.availability === "available" ? card.value : "—"}
                contextLabel={card.contextLabel}
                goalLabel={card.goalLabel}
                goalPrefix={card.goalPrefix}
                goalHint={card.goalHint}
                monthlyGoalLabel={card.monthlyGoalLabel}
                monthlyGoalPrefix={card.monthlyGoalPrefix}
                monthlyGoalHint={card.monthlyGoalHint}
                goalScopeBadge={card.goalScopeBadge}
                goalScopeHint={card.goalScopeHint}
                goalPerformanceBadge={card.goalPerformanceBadge}
                iddScoreLabel={card.iddScoreLabel}
                icon={KPI_ICONS[card.id]}
                loading={refreshing && card.availability === "available"}
                footer={
                  card.stateMessage ? (
                    <span className="engineering-overview-kpi-state">
                      {card.stateMessage}
                    </span>
                  ) : undefined
                }
              />
            ))}
            {transformaCards.map((card) => (
              <EngineeringKpiCard
                key={card.id}
                title={card.title}
                titleHint={card.titleHint}
                value={card.availability === "available" ? card.value : "—"}
                contextLabel={card.contextLabel}
                goalLabel={card.goalLabel}
                goalPrefix={card.goalPrefix}
                goalHint={card.goalHint}
                monthlyGoalLabel={card.monthlyGoalLabel}
                monthlyGoalPrefix={card.monthlyGoalPrefix}
                monthlyGoalHint={card.monthlyGoalHint}
                goalScopeBadge={card.goalScopeBadge}
                goalScopeHint={card.goalScopeHint}
                goalPerformanceBadge={card.goalPerformanceBadge}
                iddScoreLabel={card.iddScoreLabel}
                icon={KPI_ICONS[card.id]}
                loading={refreshing && card.availability === "available"}
                footer={
                  card.stateMessage ? (
                    <span className="engineering-overview-kpi-state">
                      {card.stateMessage}
                    </span>
                  ) : undefined
                }
              />
            ))}
          </div>
          {cards.length === 0 ? <EngineeringEmptyState /> : null}

          <EngineeringSectionCard
            title={copy.lmpDeepeningTitle}
            subtitle={copy.lmpDeepeningBody}
          >
            <EngineeringActionButton
              variant="primary"
              onClick={() => navigateEngineeringView("lmps", { basePath })}
            >
              {copy.lmpDeepeningCta}
            </EngineeringActionButton>
          </EngineeringSectionCard>

          {hasTransformaAccess ? (
            <EngineeringSectionCard
              title={copy.transformaDeepeningTitle}
              subtitle={copy.transformaDeepeningBody}
            >
              <EngineeringActionButton
                variant="primary"
                href={TRANSFORMA_HREF}
                title={copy.transformaDeepeningCta}
              >
                {copy.transformaDeepeningCta}
              </EngineeringActionButton>
            </EngineeringSectionCard>
          ) : null}
        </>
      ) : null}
    </>
  );
}
