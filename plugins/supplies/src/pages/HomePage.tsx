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

import {
  getHomeAttention,
  type HomeAttentionCard,
} from "../api/homeAttention";
import { navigatePluginView } from "../app/pluginNavigation";
import type { PluginNavigationTarget } from "../app/pluginRoutes";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import {
  SuppliesActionButton,
  SuppliesCatalogSearchBar,
  SuppliesEmptyState,
  SuppliesHubChipRow,
  SuppliesRouteChip,
  SuppliesSectionCard,
  SuppliesSectionRouteCard,
  SuppliesStateBanner,
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
  readFavorites,
  toggleFavorite,
  type HomeFavoriteItem,
} from "../features/home/homeFavorites";
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

function isNavigationTarget(viewId: string): viewId is PluginNavigationTarget {
  return [
    "home",
    "overview",
    "my_tasks",
    "purchase_requests",
    "purchase_orders",
    "deliveries",
    "suppliers",
    "products",
    "inventory",
    "safety_stock",
    "negotiations",
    "indicators",
    "administration",
    "help",
  ].includes(viewId);
}

export function HomePage({ basePath }: HomePageProps) {
  const session = useSuppliesSession();
  const hubCaps = useMemo(
    () => toHubCapabilities(session.capabilities),
    [session.capabilities],
  );
  const sections = useMemo(() => resolveHomePathSections(hubCaps), [hubCaps]);
  const [query, setQuery] = useState("");
  const [attentionCards, setAttentionCards] = useState<HomeAttentionCard[]>([]);
  const [attentionLoading, setAttentionLoading] = useState(true);
  const [attentionError, setAttentionError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [recents, setRecents] = useState<RecentHubView[]>(() =>
    typeof window !== "undefined" ? readRecentViews() : [],
  );
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>(() =>
    typeof window !== "undefined" ? readFavorites() : [],
  );

  const reloadAttention = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setAttentionLoading(true);
    setAttentionError(null);
    getHomeAttention(controller.signal)
      .then((payload) => {
        setAttentionCards(Array.isArray(payload.cards) ? payload.cards : []);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setAttentionCards([]);
        setAttentionError(
          error instanceof Error ? error.message : HOME.attentionError,
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setAttentionLoading(false);
      });
    return () => controller.abort();
  }, [reloadKey]);

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
    (route: Pick<HubRouteDef, "viewId" | "label">) => {
      setRecents(pushRecentView({ viewId: route.viewId, label: route.label }));
      navigatePluginView(route.viewId, { basePath });
    },
    [basePath],
  );

  const onToggleFavorite = useCallback((route: HubRouteDef) => {
    setFavorites((current) =>
      toggleFavorite({ viewId: route.viewId, label: route.label }, current),
    );
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

  const goToCard = (card: HomeAttentionCard) => {
    if (!isNavigationTarget(card.viewId) || card.status === "unavailable") return;
    navigateRoute({ viewId: card.viewId, label: card.title });
  };

  const attentionReady = !attentionLoading;
  const hasAttention = attentionCards.length > 0;
  const showAttentionPanel = attentionReady && !attentionError && hasAttention;
  const showQueueOk = attentionReady && !attentionError && !hasAttention;

  return (
    <section className="sp-page-stack sp-home-layout" aria-label="Início">
      <div className="sp-home-stack">
        {showAttentionPanel ? (
          <SuppliesSectionCard
            title={HOME.attentionTitle}
            subtitle={HOME.attentionSubtitle}
            hint={SP_HELP.homeAttention}
            actions={
              <SuppliesActionButton variant="ghost" onClick={reloadAttention}>
                {HOME.attentionRefresh}
              </SuppliesActionButton>
            }
          >
            <ul className="sp-home-attention-list">
              {attentionCards.map((card) => (
                <li key={card.id}>
                  <button
                    type="button"
                    className="sp-home-attention-card"
                    disabled={card.status === "unavailable"}
                    onClick={() => goToCard(card)}
                  >
                    <span className="sp-home-attention-card__title">{card.title}</span>
                    <span className="sp-home-attention-card__desc">{card.description}</span>
                    <span className="sp-home-attention-card__count">
                      {card.count == null ? "—" : String(card.count)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </SuppliesSectionCard>
        ) : null}

        {showQueueOk ? (
          <div className="sp-home-queue-ok" role="status">
            <span>{HOME.attentionQueueOk}</span>
          </div>
        ) : null}

        {attentionLoading ? (
          <SuppliesStateBanner>{HOME.attentionLoading}</SuppliesStateBanner>
        ) : null}

        {attentionError ? (
          <SuppliesStateBanner variant="error">{HOME.attentionError}</SuppliesStateBanner>
        ) : null}

        <SuppliesSectionCard
          title={HOME.pathsTitle}
          subtitle={HOME.pathsSubtitle}
          hint={SP_HELP.shell.navHome}
        >
          <div className="sp-home-paths">
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

            {visibleFavorites.length > 0 ? (
              <SuppliesHubChipRow
                label={HOME.favoritesTitle}
                aria-label={HOME.favoritesTitle}
              >
                {visibleFavorites.map((item) => (
                  <SuppliesRouteChip
                    key={item.viewId}
                    tone="pinned"
                    label={item.label}
                    onNavigate={() =>
                      navigateRoute({ viewId: item.viewId, label: item.label })
                    }
                    onRemove={() =>
                      setFavorites((current) =>
                        toggleFavorite(
                          { viewId: item.viewId, label: item.label },
                          current,
                        ),
                      )
                    }
                    removeLabel={HOME.unpinLabel}
                  />
                ))}
              </SuppliesHubChipRow>
            ) : null}

            {visibleRecents.length > 0 ? (
              <SuppliesHubChipRow label={HOME.recentsTitle} aria-label={HOME.recentsTitle}>
                {visibleRecents.map((item) => (
                  <SuppliesRouteChip
                    key={`${item.viewId}-${item.at}`}
                    tone="recent"
                    label={item.label}
                    onNavigate={() =>
                      navigateRoute({ viewId: item.viewId, label: item.label })
                    }
                  />
                ))}
              </SuppliesHubChipRow>
            ) : null}

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
