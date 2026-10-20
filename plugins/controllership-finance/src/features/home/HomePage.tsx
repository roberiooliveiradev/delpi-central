import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { CalendarCheck2, Landmark } from "lucide-react";

import { useViewerContext } from "../../app/ViewerContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import {
  CfActionButton,
  CfCatalogSearchBar,
  CfEmptyState,
  CfEventsSection,
  CfLoadingCard,
  CfRecentAccessStrip,
  CfSectionCard,
  CfSectionRouteCard,
  CfStateBanner,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import {
  collectSearchHits,
  filterRouteCatalog,
  findHubRouteById,
  HUB_CONTENT,
  resolveHubSections,
  type HubRouteDef,
  type HubSectionDef,
  type HubSectionId,
} from "../../content/pluginRouteCatalog";
import {
  filterRecentsByCaps,
  pushRecentView,
  readRecentViews,
  type RecentHubView,
} from "./homeRecentViews";
import { readHomeSearchQuery, writeHomeSearchQuery } from "./homeSearchQuery";

type HomePageProps = {
  basePath: string;
};

const EVENTS = HUB_CONTENT.events;
const FEATURES = HUB_CONTENT.features;

const SECTION_ICONS: Record<HubSectionId, ReactNode> = {
  portal: <Landmark size={20} strokeWidth={1.75} aria-hidden="true" />,
  closing: <CalendarCheck2 size={20} strokeWidth={1.75} aria-hidden="true" />,
};

const FORBIDDEN_STATUS = 403;

export function HomePage({ basePath }: HomePageProps) {
  const { viewer, loading, errorStatus, reload } = useViewerContext();
  const [searchQuery, setSearchQuery] = useState(() =>
    typeof window !== "undefined" ? readHomeSearchQuery() : "",
  );
  const [recents, setRecents] = useState<RecentHubView[]>(() =>
    typeof window !== "undefined" ? readRecentViews() : [],
  );

  const capabilities = useMemo(
    () => ({ manage: viewer?.capabilities.manage === true }),
    [viewer],
  );

  const sections = useMemo(() => resolveHubSections(capabilities), [capabilities]);

  useEffect(() => {
    writeHomeSearchQuery(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    setRecents(
      pushRecentView({
        viewId: "home",
        label: "Início",
      }),
    );
  }, []);

  const recordVisit = useCallback(
    (
      viewId: HubRouteDef["viewId"],
      search: string | undefined,
      label: string | undefined,
    ) => {
      setRecents(
        pushRecentView({
          viewId,
          search,
          label: label ?? "Início",
        }),
      );
    },
    [],
  );

  const navigateRoute = useCallback(
    (route: Pick<HubRouteDef, "viewId" | "search" | "label">) => {
      recordVisit(route.viewId, route.search, route.label);
      navigatePluginView(route.viewId, { basePath, search: route.search });
    },
    [basePath, recordVisit],
  );

  const filteredSections = useMemo(
    () => filterRouteCatalog(sections, searchQuery),
    [searchQuery, sections],
  );

  const searchHits = useMemo(
    () => collectSearchHits(sections, searchQuery, 8),
    [searchQuery, sections],
  );

  const visibleRecents = useMemo(
    () => filterRecentsByCaps(recents, capabilities),
    [capabilities, recents],
  );

  const mapSectionRoutes = useCallback(
    (section: HubSectionDef) =>
      section.routes.map((route) => ({
        id: route.id,
        label: route.label,
        kind: route.kind,
        onClick: () => navigateRoute(route),
      })),
    [navigateRoute],
  );

  if (loading) {
    return (
      <section className="cf-page-stack cf-home-layout" aria-label="Início">
        <CfLoadingCard title="Carregando contexto…" variant="panel" />
      </section>
    );
  }

  if (errorStatus === FORBIDDEN_STATUS) {
    return (
      <section className="cf-page-stack cf-home-layout" aria-label="Início">
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Acesso restrito</p>
          <p className="cf-banner-text">
            Você não tem permissão para acessar o Portal Controladoria &amp;
            Finanças.
          </p>
        </CfStateBanner>
      </section>
    );
  }

  return (
    <section className="cf-page-stack cf-home-layout" aria-label="Início">
      <div className="cf-home-stack">
        {errorStatus != null ? (
          <CfStateBanner>
            <p className="cf-banner-title">Contexto indisponível</p>
            <p className="cf-banner-text">
              Não foi possível carregar os dados do seu perfil. A navegação
              permanece disponível.
            </p>
            <CfActionButton variant="ghost" onClick={reload}>
              Tentar novamente
            </CfActionButton>
          </CfStateBanner>
        ) : null}

        <CfEventsSection
          title={EVENTS.title}
          subtitle={EVENTS.subtitle}
          hint={CF_HELP.home.events}
          items={[]}
          omitWhenEmpty={false}
          emptyMessage={EVENTS.unavailable}
          listAriaLabel={EVENTS.listAriaLabel}
        />

        <CfSectionCard
          title={FEATURES.title}
          subtitle={FEATURES.subtitle}
          hint={CF_HELP.home.shortcuts}
        >
          <div className="cf-home-paths">
            <CfCatalogSearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              hits={searchHits.map((hit) => ({
                id: hit.id,
                label: hit.label,
                groupLabel: hit.groupLabel,
              }))}
              onSelectHit={(id: string) => {
                const route = findHubRouteById(sections, id);
                if (route) navigateRoute(route);
              }}
              placeholder={FEATURES.searchPlaceholder}
              clearLabel={FEATURES.clearSearch}
              emptyHitsLabel={FEATURES.searchEmpty}
              aria-label={FEATURES.searchAriaLabel}
            />

            <CfRecentAccessStrip
              label={FEATURES.recentsTitle}
              aria-label={FEATURES.recentsTitle}
              items={visibleRecents.map((item) => ({
                id: `${item.viewId}::${item.search ?? ""}`,
                label: item.label,
                icon: SECTION_ICONS.portal,
              }))}
              onSelect={(id: string) => {
                const item = visibleRecents.find(
                  (entry) => `${entry.viewId}::${entry.search ?? ""}` === id,
                );
                if (!item) return;
                navigateRoute({
                  viewId: item.viewId,
                  search: item.search,
                  label: item.label,
                });
              }}
            />

            {sections.length === 0 ? (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage={FEATURES.empty}
              />
            ) : filteredSections.length === 0 ? (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage={FEATURES.searchEmpty}
              />
            ) : (
              <div
                className="cf-home-sections-grid"
                aria-label={FEATURES.gridAriaLabel}
              >
                {filteredSections.map((section) => (
                  <CfSectionRouteCard
                    key={section.id}
                    title={section.title}
                    description={section.description}
                    icon={
                      SECTION_ICONS[section.id] ?? (
                        <Landmark size={20} aria-hidden="true" />
                      )
                    }
                    routes={mapSectionRoutes(section)}
                  />
                ))}
              </div>
            )}
          </div>
        </CfSectionCard>
      </div>
    </section>
  );
}
