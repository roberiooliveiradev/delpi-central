import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ClipboardList,
  Package,
  ShoppingCart,
  Users,
} from "lucide-react";

import { navigatePluginView } from "../app/pluginNavigation";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import {
  SuppliesCatalogSearchBar,
  SuppliesEmptyState,
  SuppliesRecentAccessStrip,
  SuppliesSectionHintLabel,
  SuppliesSectionCard,
  SuppliesSectionRouteCard,
} from "../app/suppliesUi";
import { SP_HELP } from "../content/helpTooltips";
import {
  collectSearchHits,
  findHubRouteById,
  HUB_CONTENT,
  resolveHomePathSections,
  type HubRouteDef,
  type HubSectionDef,
} from "../content/pluginRouteCatalog";
import { toHubCapabilities } from "../features/home/homeCatalog";
import {
  filterFavoritesByCaps,
  type HomeFavoriteItem,
} from "../features/home/homeFavorites";
import {
  loadHomeFavoritesFromStorage,
  subscribeHomeFavorites,
  toggleHomeFavorite,
} from "../app/homeFavoritesStore";
import {
  filterRecentsByCaps,
  pushRecentView,
  readRecentViews,
  type RecentHubView,
} from "../features/home/homeRecentViews";

type HomePageProps = {
  basePath: string;
};

const HOME = HUB_CONTENT.home;

const SECTION_ICONS: Record<string, ReactNode> = {
  attention: <ClipboardList size={20} strokeWidth={1.75} aria-hidden="true" />,
  analytics: <BarChart3 size={20} strokeWidth={1.75} aria-hidden="true" />,
  purchase_requests: <ShoppingCart size={20} strokeWidth={1.75} aria-hidden="true" />,
  operations: <Package size={20} strokeWidth={1.75} aria-hidden="true" />,
  administration: <BriefcaseBusiness size={20} strokeWidth={1.75} aria-hidden="true" />,
  help: <BookOpen size={20} strokeWidth={1.75} aria-hidden="true" />,
};

const SECTION_HINTS: Record<string, string> = {
  attention: SP_HELP.home.sections.attention,
  analytics: SP_HELP.home.sections.analytics,
  purchase_requests: SP_HELP.home.sections.purchase_requests,
  operations: SP_HELP.home.sections.operations,
  administration: SP_HELP.home.sections.administration,
  help: SP_HELP.home.sections.help,
};

export function HomePage({ basePath }: HomePageProps) {
  const session = useSuppliesSession();
  const hubCaps = useMemo(
    () => toHubCapabilities(session.capabilities),
    [session.capabilities],
  );
  const sections = useMemo(() => resolveHomePathSections(hubCaps), [hubCaps]);
  const [query, setQuery] = useState("");
  const [recents, setRecents] = useState<RecentHubView[]>(() =>
    typeof window !== "undefined" ? readRecentViews() : [],
  );
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);

  useEffect(() => subscribeHomeFavorites(setFavorites), []);

  useEffect(() => {
    loadHomeFavoritesFromStorage();
  }, []);

  const visibleRecents = useMemo(
    () => filterRecentsByCaps(recents, hubCaps),
    [recents, hubCaps],
  );
  const visibleFavorites = useMemo(
    () => filterFavoritesByCaps(favorites, hubCaps),
    [favorites, hubCaps],
  );
  const favoriteKeys = useMemo(
    () => new Set(visibleFavorites.map((item) => item.viewId)),
    [visibleFavorites],
  );

  const searchHits = useMemo(
    () => collectSearchHits(sections, query, 12),
    [query, sections],
  );

  const filteredSections: HubSectionDef[] = query.trim()
    ? sections
        .map((section) => ({
          ...section,
          routes: section.routes.filter((route) =>
            searchHits.some((hit) => hit.id === route.id),
          ),
        }))
        .filter((section) => section.routes.length > 0)
    : sections;

  const navigateRoute = useCallback(
    (route: Pick<HubRouteDef, "viewId" | "label">, search?: string) => {
      setRecents(pushRecentView({ viewId: route.viewId, label: route.label }));
      navigatePluginView(route.viewId, { basePath, search });
    },
    [basePath],
  );

  const onToggleFavorite = useCallback((route: HubRouteDef) => {
    toggleHomeFavorite({ viewId: route.viewId, label: route.label });
  }, []);

  const mapSectionRoutes = useCallback(
    (section: HubSectionDef) =>
      section.routes.map((route) => ({
        id: route.id,
        label: route.label,
        pinned: favoriteKeys.has(route.viewId),
        pinLabel: HOME.pinLabel,
        unpinLabel: HOME.unpinLabel,
        onPinClick: () => onToggleFavorite(route),
        onClick: () => navigateRoute(route),
      })),
    [favoriteKeys, navigateRoute, onToggleFavorite],
  );

  return (
    <section className="sp-page-stack sp-home-layout" aria-label="Início">
      <div className="sp-home-stack">
        <SuppliesSectionCard
          title={HOME.pathsTitle}
          subtitle={HOME.pathsSubtitle}
          hint={SP_HELP.home.paths}
        >
          <div className="sp-home-paths">
            <div className="sp-home-search">
              <div className="sp-home-search__label">
                <SuppliesSectionHintLabel
                  label={HOME.searchLabel}
                  hint={SP_HELP.home.search}
                />
              </div>
              <SuppliesCatalogSearchBar
                value={query}
                onChange={setQuery}
                hits={searchHits.map((hit) => ({
                  id: hit.id,
                  label: hit.label,
                  groupLabel: hit.groupLabel,
                }))}
                onSelectHit={(id) => {
                  const route = findHubRouteById(sections, id);
                  if (route) navigateRoute(route);
                }}
                placeholder={HOME.searchPlaceholder}
                clearLabel={HOME.clearSearch}
                emptyHitsLabel={HOME.searchEmpty}
                aria-label={HOME.searchAriaLabel}
              />
            </div>

            <SuppliesRecentAccessStrip
              label={
                <SuppliesSectionHintLabel
                  label={HOME.recentsTitle}
                  hint={SP_HELP.home.recents}
                />
              }
              aria-label={HOME.recentsTitle}
              items={visibleRecents.map((item) => ({
                id: item.viewId,
                label: item.label,
              }))}
              onSelect={(id: string) => {
                const item = visibleRecents.find((entry) => entry.viewId === id);
                if (!item) return;
                navigateRoute({ viewId: item.viewId, label: item.label });
              }}
            />

            {sections.length === 0 ? (
              <SuppliesEmptyState title={HOME.pathsEmpty} message={HOME.pathsSubtitle} />
            ) : filteredSections.length === 0 ? (
              <SuppliesEmptyState title={HOME.searchEmpty} message={HOME.pathsSubtitle} />
            ) : (
              <div className="sp-home-sections-grid" aria-label={HOME.pathsGridAriaLabel}>
                {filteredSections.map((section) => (
                  <SuppliesSectionRouteCard
                    key={section.id}
                    title={section.title}
                    description={section.description}
                    hint={SECTION_HINTS[section.id]}
                    icon={SECTION_ICONS[section.id] ?? <Users size={20} aria-hidden="true" />}
                    routes={mapSectionRoutes(section)}
                  />
                ))}
              </div>
            )}
          </div>
        </SuppliesSectionCard>
      </div>
    </section>
  );
}
