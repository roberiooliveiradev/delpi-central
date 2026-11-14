import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { formatPortalGreeting } from "@delpi/plugin-ui/index";
import {
  BookOpen,
  Briefcase,
  ChartColumn,
  ChartNoAxesCombined,
  ClipboardCheck,
  ClipboardList,
  ClipboardX,
  Compass,
  House,
  LifeBuoy,
  Package,
  PackagePlus,
  RefreshCw,

} from "lucide-react";

import { getDisplayNameFromAccessToken } from "../../app/authDisplayName";
import { openCatalogRoute } from "../../app/openCatalogRoute";
import {
  getFavoriteRouteIds,
  subscribeFavorites,
  toggleFavorite,
} from "../../app/favoritesStore";
import { pushRecentView, readRecentViews } from "../../app/recentViews";
import {
  filterSectionsByQuery,
  HOME_COPY,
  searchCatalog,
  type CatalogRoute,
  type CatalogSection,
} from "../../content/engineeringRouteCatalog";
import {
  buildPrcQueueUrl,
  navigatePrcHref,
  EMPTY_PRC_QUEUE_URL,
} from "../product-registration/prcNavigate";
import {
  EngineeringActionButton,
  EngineeringCatalogSearchBar,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringRecentAccessStrip,
  EngineeringSectionCard,
  EngineeringSectionRouteCard,
  EngineeringStateBanner,
} from "../../ui/engineeringUi";
import {
  buildHeroHighlights,
  buildPendingQueueIndicator,
} from "./homeViewModel";
import { useHomeData } from "./useHomeData";

const SECTION_ICONS: Record<string, ReactNode> = {
  work: <Briefcase size={20} aria-hidden="true" />,
  insights: <Compass size={20} aria-hidden="true" />,
  support: <LifeBuoy size={20} aria-hidden="true" />,
};

const ROUTE_ICONS: Record<string, ReactNode> = {
  my_requests: <ClipboardList size={16} aria-hidden="true" />,
  lmps: <ClipboardCheck size={16} aria-hidden="true" />,
  nonconformities: <ClipboardX size={16} aria-hidden="true" />,
  "product-registration": <PackagePlus size={16} aria-hidden="true" />,
  products: <Package size={16} aria-hidden="true" />,
  overview: <ChartColumn size={16} aria-hidden="true" />,
  dashboard: <ChartNoAxesCombined size={16} aria-hidden="true" />,
  home: <House size={16} aria-hidden="true" />,
  help: <BookOpen size={16} aria-hidden="true" />,

};

function openPendingQueue(basePath: string): void {
  navigatePrcHref(
    buildPrcQueueUrl(basePath, { ...EMPTY_PRC_QUEUE_URL, view: "pending" }),
  );
}

type HomePageProps = {
  basePath: string;
  sections: readonly CatalogSection[];
  getAccessToken?: () => string | undefined;
  onOpenRoute: (route: CatalogRoute) => void;
};

export function HomePage({
  basePath,
  sections,
  getAccessToken,
  onOpenRoute,
}: HomePageProps) {
  const copy = HOME_COPY;
  const { state, refreshing, reload } = useHomeData();
  const [searchQuery, setSearchQuery] = useState("");
  const [favoriteIds, setFavoriteIds] = useState<ReadonlySet<string>>(() =>
    getFavoriteRouteIds(),
  );
  const [recents, setRecents] = useState(() => readRecentViews());
  const [displayName] = useState<string | null>(() =>
    getDisplayNameFromAccessToken(getAccessToken?.()),
  );

  useEffect(
    () =>
      subscribeFavorites(() => {
        setFavoriteIds(getFavoriteRouteIds());
      }),
    [],
  );

  const knownRouteIds = useMemo(
    () =>
      new Set(
        sections.flatMap((section) => section.routes.map((r) => r.id)),
      ),
    [sections],
  );

  const visibleRecents = useMemo(
    () => recents.filter((item) => knownRouteIds.has(item.routeId)),
    [recents, knownRouteIds],
  );

  const openRoute = useCallback(
    (route: CatalogRoute) => {
      if (route.comingSoon) return;
      setRecents(
        pushRecentView({ routeId: route.id, label: route.label }),
      );
      if (route.target.kind === "internal") {
        onOpenRoute(route);
      } else {
        openCatalogRoute(route, basePath);
      }
    },
    [basePath, onOpenRoute],
  );

  const home = state.phase === "ready" ? state.home : null;
  const loading = state.phase === "loading";

  const greeting = formatPortalGreeting({
    displayName,
    fallback: copy.hero.fallbackGreeting,
  });

  const highlights = useMemo(
    () => (home ? buildHeroHighlights(home.sections, false) : undefined),
    [home],
  );

  const pendingIndicator = useMemo(
    () => (home ? buildPendingQueueIndicator(home.sections) : null),
    [home],
  );

  const filteredSections = useMemo(
    () => filterSectionsByQuery(sections, searchQuery),
    [sections, searchQuery],
  );
  const searchHits = useMemo(
    () => searchCatalog(searchQuery, sections),
    [searchQuery, sections],
  );

  return (
    <>
      <EngineeringPageHero
        aria-label={copy.hero.eyebrow}
        eyebrow={copy.hero.eyebrow}
        title={greeting}
        description={copy.hero.description}
        highlights={highlights}
        actions={
          <EngineeringActionButton
            variant="ghost"
            onClick={reload}
            disabled={refreshing}
            aria-label={
              refreshing
                ? copy.hero.refreshingLabel
                : copy.hero.refreshLabel
            }
          >
            <RefreshCw size={16} aria-hidden="true" />
            {refreshing
              ? copy.hero.refreshingLabel
              : copy.hero.refreshLabel}
          </EngineeringActionButton>
        }
      />

      {loading ? (
        <EngineeringLoadingActivityCard
          title={copy.loading.title}
          description={copy.loading.description}
        />
      ) : null}

      {state.phase === "error" ? (
        <EngineeringStateBanner variant="error">
          {state.error.message}
        </EngineeringStateBanner>
      ) : null}

      {home ? (
        <>
          {pendingIndicator && pendingIndicator.kind !== "hidden" ? (
            <EngineeringSectionCard
              title={copy.pending.title}
              subtitle={copy.pending.subtitle}
            >
              <div className="engineering-home-pending">
                {pendingIndicator.kind === "ready" ? (
                  <>
                    <p className="engineering-home-pending__count">
                      <strong aria-live="polite">
                        {pendingIndicator.total}
                      </strong>{" "}
                      {pendingIndicator.total === 1
                        ? copy.pending.countSingular
                        : copy.pending.countPlural}
                    </p>
                    <EngineeringActionButton
                      variant="primary"
                      onClick={() => openPendingQueue(basePath)}
                    >
                      {copy.pending.openLabel}
                    </EngineeringActionButton>
                  </>
                ) : pendingIndicator.kind === "empty" ? (
                  <p className="engineering-home-pending__state" role="status">
                    {copy.pending.emptyLabel}
                  </p>
                ) : (
                  <p className="engineering-home-pending__state" role="status">
                    {pendingIndicator.message}
                  </p>
                )}
              </div>
            </EngineeringSectionCard>
          ) : null}

          <EngineeringSectionCard
            title={copy.features.title}
            subtitle={copy.features.subtitle}
          >
            <div className="engineering-home-paths">
              <EngineeringCatalogSearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                hits={searchHits}
                onSelectHit={(routeId) => {
                  const route = sections
                    .flatMap((s) => s.routes)
                    .find((r) => r.id === routeId);
                  if (route) openRoute(route);
                }}
                placeholder={copy.features.searchPlaceholder}
                clearLabel={copy.features.clearSearch}
                emptyHitsLabel={copy.features.searchEmpty}
                aria-label={copy.features.searchAriaLabel}
              />

              <EngineeringRecentAccessStrip
                label={copy.features.recentsTitle}
                aria-label={copy.features.recentsTitle}
                items={visibleRecents.map((item) => ({
                  id: item.routeId,
                  label: item.label,
                }))}
                onSelect={(routeId) => {
                  const route = sections
                    .flatMap((s) => s.routes)
                    .find((r) => r.id === routeId);
                  if (route) openRoute(route);
                }}
              />

              {filteredSections.length === 0 ? (
                <EngineeringEmptyState
                  message={
                    searchQuery
                      ? copy.features.searchEmpty
                      : copy.features.emptyCatalog
                  }
                />
              ) : (
                <div
                  className="engineering-home-sections-grid"
                  aria-label={copy.features.gridAriaLabel}
                >
                  {filteredSections.map((section) => (
                    <EngineeringSectionRouteCard
                      key={section.id}
                      title={section.title}
                      description={section.description}
                      icon={SECTION_ICONS[section.id] ?? (
                        <ClipboardList size={20} aria-hidden="true" />
                      )}
                      routes={section.routes.map((route) => ({
                        id: route.id,
                        label: route.label,
                        icon: ROUTE_ICONS[route.id],
                        disabled: route.comingSoon,
                        badge: route.comingSoon
                          ? copy.features.comingSoonBadge
                          : undefined,
                        kind: "navigate",
                        pinned: favoriteIds.has(route.id),
                        pinLabel: copy.features.pinLabel,
                        unpinLabel: copy.features.unpinLabel,
                        onPinClick: () => toggleFavorite(route.id),
                        onClick: () => openRoute(route),
                      }))}
                    />
                  ))}
                </div>
              )}
            </div>
          </EngineeringSectionCard>
        </>
      ) : null}
    </>
  );
}
