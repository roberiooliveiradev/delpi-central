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
  type HomeAttentionCard,
} from "../api/homeAttention";
import { navigatePluginView } from "../app/pluginNavigation";
import type { PluginRoutableView } from "../app/pluginRoutes";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import {
  HelpTooltip,
  SuppliesActionButton,
  SuppliesCatalogSearchBar,
  SuppliesEmptyState,
  SuppliesHubChipRow,
  SuppliesLoadingCard,
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
  type HomeFavoriteItem,
} from "../features/home/homeFavorites";
import {
  loadHomeFavoritesFromStorage,
  subscribeHomeFavorites,
  toggleHomeFavorite,
} from "../app/homeFavoritesStore";
import {
  loadHomeAttention,
  subscribeHomeAttention,
  type HomeAttentionState,
} from "../app/homeAttentionStore";
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

function isNavigationTarget(viewId: string): viewId is PluginRoutableView {
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

function LabelWithHelp({
  label,
  help,
  ariaLabel,
}: {
  label: string;
  help: string;
  ariaLabel: string;
}) {
  return (
    <span className="sp-label-with-help">
      <span>{label}</span>
      <HelpTooltip content={help} ariaLabel={ariaLabel} placement="bottom" />
    </span>
  );
}

export function HomePage({ basePath }: HomePageProps) {
  const session = useSuppliesSession();
  const hubCaps = useMemo(
    () => toHubCapabilities(session.capabilities),
    [session.capabilities],
  );
  const sections = useMemo(() => resolveHomePathSections(hubCaps), [hubCaps]);
  const [query, setQuery] = useState("");
  const [attention, setAttention] = useState<HomeAttentionState>(() => ({
    loading: true,
    error: null,
    cards: [],
    partialFailures: [],
  }));
  const [recents, setRecents] = useState<RecentHubView[]>(() =>
    typeof window !== "undefined" ? readRecentViews() : [],
  );
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);

  useEffect(() => subscribeHomeFavorites(setFavorites), []);
  useEffect(() => subscribeHomeAttention(setAttention), []);

  useEffect(() => {
    loadHomeFavoritesFromStorage();
  }, []);

  const reloadAttention = useCallback(() => {
    void loadHomeAttention();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadHomeAttention(controller.signal);
    return () => controller.abort();
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
    (route: Pick<HubRouteDef, "viewId" | "label">) => {
      setRecents(pushRecentView({ viewId: route.viewId, label: route.label }));
      navigatePluginView(route.viewId, { basePath });
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

  const goToCard = (card: HomeAttentionCard) => {
    if (!isNavigationTarget(card.viewId) || card.status === "unavailable") return;
    navigateRoute({ viewId: card.viewId, label: card.title });
  };

  const attentionCards = attention.cards;
  const attentionLoading = attention.loading;
  const attentionError = attention.error;
  const attentionReady = !attentionLoading;
  const hasAttention = attentionCards.length > 0;
  const showAttentionPanel = attentionReady && !attentionError && hasAttention;
  const showQueueOk = attentionReady && !attentionError && !hasAttention;
  const partialMessages = attention.partialFailures
    .map((item) => item.message?.trim())
    .filter((value): value is string => Boolean(value));

  return (
    <section className="sp-page-stack sp-home-layout" aria-label="Início">
      <div className="sp-home-stack">
        {showAttentionPanel ? (
          <SuppliesSectionCard
            title={HOME.attentionTitle}
            subtitle={HOME.attentionSubtitle}
            hint={SP_HELP.home.attention}
            actions={
              <SuppliesActionButton variant="ghost" onClick={reloadAttention}>
                {HOME.attentionRefresh}
              </SuppliesActionButton>
            }
          >
            {partialMessages.length > 0 ? (
              <SuppliesStateBanner>{HOME.attentionPartial}</SuppliesStateBanner>
            ) : null}
            <ul className="sp-home-attention-list">
              {attentionCards.map((card) => (
                <li key={card.id}>
                  <button
                    type="button"
                    className="sp-home-attention-card"
                    disabled={card.status === "unavailable"}
                    onClick={() => goToCard(card)}
                    title={card.description}
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
            <LabelWithHelp
              label={HOME.attentionQueueOk}
              help={SP_HELP.home.queueOk}
              ariaLabel={HOME.queueOkHelpAriaLabel}
            />
          </div>
        ) : null}

        {attentionLoading ? (
          <SuppliesLoadingCard title={HOME.attentionLoading} variant="panel" />
        ) : null}

        {attentionError ? (
          <div className="sp-home-attention-error">
            <SuppliesStateBanner variant="error">{HOME.attentionError}</SuppliesStateBanner>
            <SuppliesActionButton variant="ghost" onClick={reloadAttention}>
              {HOME.attentionRefresh}
            </SuppliesActionButton>
          </div>
        ) : null}

        <SuppliesSectionCard
          title={HOME.pathsTitle}
          subtitle={HOME.pathsSubtitle}
          hint={SP_HELP.home.paths}
        >
          <div className="sp-home-paths">
            <div className="sp-home-search">
              <div className="sp-home-search__label">
                <LabelWithHelp
                  label={HOME.searchLabel}
                  help={SP_HELP.home.search}
                  ariaLabel={HOME.searchHelpAriaLabel}
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

            {visibleFavorites.length > 0 ? (
              <SuppliesHubChipRow
                label={
                  <LabelWithHelp
                    label={HOME.favoritesTitle}
                    help={SP_HELP.home.favorites}
                    ariaLabel={HOME.favoritesHelpAriaLabel}
                  />
                }
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
                      toggleHomeFavorite({
                        viewId: item.viewId,
                        label: item.label,
                      })
                    }
                    removeLabel={HOME.unpinLabel}
                  />
                ))}
              </SuppliesHubChipRow>
            ) : null}

            {visibleRecents.length > 0 ? (
              <SuppliesHubChipRow
                label={
                  <LabelWithHelp
                    label={HOME.recentsTitle}
                    help={SP_HELP.home.recents}
                    ariaLabel={HOME.recentsHelpAriaLabel}
                  />
                }
                aria-label={HOME.recentsTitle}
              >
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
