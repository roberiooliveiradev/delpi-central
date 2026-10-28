import { useMemo } from "react";
import { ClipboardList } from "lucide-react";

import { buildEngineeringPath, navigateEngineeringView } from "../../app/engineeringRoutes";
import { HOME_COPY } from "../../content/engineeringRouteCatalog";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringLoadingState,
  EngineeringMetricStrip,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
  EngineeringSectionRouteCard,
  EngineeringStateBanner,
} from "../../ui/engineeringUi";
import { buildHeroHighlights, buildOverviewRows } from "../home/homeViewModel";
import { useHomeData } from "../home/useHomeData";

type OverviewPageProps = {
  basePath: string;
};

/** Visão geral — somente dados autorizados da engineering-api. Nenhuma
 * métrica é inventada: seção indisponível/negada aparece com seu estado
 * oficial, sem número. */
export function OverviewPage({ basePath }: OverviewPageProps) {
  const copy = HOME_COPY.overview;
  const { state, refreshing, reload } = useHomeData();
  const home = state.phase === "ready" ? state.home : null;

  const metrics = useMemo(
    () => (home ? buildHeroHighlights(home.sections, false) : []),
    [home],
  );
  const rows = useMemo(() => (home ? buildOverviewRows(home) : []), [home]);

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
          >
            {HOME_COPY.hero.refreshLabel}
          </EngineeringActionButton>
        }
      />

      {state.phase === "loading" ? (
        <EngineeringLoadingState message={copy.loading} />
      ) : null}

      {state.phase === "error" ? (
        <EngineeringStateBanner variant="error">
          {state.error.message || copy.errorFallback}
        </EngineeringStateBanner>
      ) : null}

      {home ? (
        <>
          <EngineeringMetricStrip
            items={metrics}
            aria-label={copy.metricsAriaLabel}
          />

          <EngineeringSectionCard
            title={copy.sourcesTitle}
            subtitle={copy.sourcesSubtitle}
          >
            <div className="engineering-home-sections-grid">
              {rows.map((row) => (
                <EngineeringSectionRouteCard
                  key={row.key}
                  title={row.title}
                  description={row.detail || row.statusLabel}
                  icon={<ClipboardList size={20} aria-hidden="true" />}
                  badge={row.statusLabel}
                  routes={[]}
                />
              ))}
            </div>
            {rows.length === 0 ? <EngineeringEmptyState /> : null}
          </EngineeringSectionCard>
        </>
      ) : null}
    </>
  );
}
