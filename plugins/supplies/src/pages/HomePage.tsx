import { useEffect, useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import {
  getHomeAttention,
  type HomeAttentionCard,
} from "../api/homeAttention";
import { navigatePluginView } from "../app/pluginNavigation";
import type { PluginNavigationTarget } from "../app/pluginRoutes";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import { SuppliesEmptyState, SuppliesStateBanner } from "../app/suppliesUi";
import { SP_HELP } from "../content/helpTooltips";
import {
  collectSearchHits,
  findHubRouteById,
  HUB_CONTENT,
  pickOnboardingShortcuts,
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
  const onboarding = useMemo(() => pickOnboardingShortcuts(hubCaps), [hubCaps]);
  const [query, setQuery] = useState("");
  const [attentionCards, setAttentionCards] = useState<HomeAttentionCard[]>([]);
  const [attentionLoading, setAttentionLoading] = useState(true);
  const [attentionError, setAttentionError] = useState<string | null>(null);
  const [recents, setRecents] = useState<RecentHubView[]>(() =>
    typeof window !== "undefined" ? readRecentViews() : [],
  );
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>(() =>
    typeof window !== "undefined" ? readFavorites() : [],
  );

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
          error instanceof Error ? error.message : HUB_CONTENT.home.attentionError,
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setAttentionLoading(false);
      });
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

  const searchHits = useMemo(
    () => collectSearchHits(sections, query, 12),
    [query, sections],
  );

  const visibleSections: HubSectionDef[] = query.trim()
    ? sections
        .map((section) => ({
          ...section,
          routes: section.routes.filter((route) =>
            searchHits.some((hit) => hit.id === route.id),
          ),
        }))
        .filter((section) => section.routes.length > 0)
    : sections;

  function goTo(viewId: PluginNavigationTarget, label: string) {
    setRecents(pushRecentView({ viewId, label }));
    navigatePluginView(viewId, { basePath });
  }

  function goToRoute(route: HubRouteDef) {
    goTo(route.viewId, route.label);
  }

  function goToCard(card: HomeAttentionCard) {
    if (!isNavigationTarget(card.viewId) || card.status === "unavailable") return;
    goTo(card.viewId, card.title);
  }

  function onToggleFavorite(route: HubRouteDef) {
    setFavorites(toggleFavorite({ viewId: route.viewId, label: route.label }, favorites));
  }

  const favoriteViewIds = new Set(visibleFavorites.map((item) => item.viewId));

  return (
    <div className="sp-page-stack sp-home">
      <header className="sp-home__hero">
        <p className="sp-home__eyebrow">{HUB_CONTENT.home.eyebrow}</p>
        <h1>
          {HUB_CONTENT.home.title}{" "}
          <HelpTooltip
            content={SP_HELP.homeVsOverview}
            ariaLabel={HUB_CONTENT.home.helpAriaLabel}
          />
        </h1>
        <p className="sp-home__description">{HUB_CONTENT.home.description}</p>
        {onboarding.length > 0 ? (
          <div className="sp-home__onboarding" aria-label={HUB_CONTENT.home.onboardingTitle}>
            {onboarding.map((route) => (
              <button
                key={route.id}
                type="button"
                className="sp-home__chip"
                onClick={() => goToRoute(route)}
              >
                {route.label}
              </button>
            ))}
          </div>
        ) : null}
      </header>

      <section className="sp-home__attention" aria-label={HUB_CONTENT.home.attentionTitle}>
        <h2>
          {HUB_CONTENT.home.attentionTitle}{" "}
          <HelpTooltip
            content={SP_HELP.homeAttention}
            ariaLabel="Ajuda: bloco Atenção"
          />
        </h2>
        {attentionLoading ? (
          <SuppliesStateBanner>Carregando atenção…</SuppliesStateBanner>
        ) : null}
        {attentionError ? (
          <SuppliesStateBanner variant="error">
            {HUB_CONTENT.home.attentionError}
          </SuppliesStateBanner>
        ) : null}
        {!attentionLoading && !attentionError && attentionCards.length === 0 ? (
          <SuppliesEmptyState
            title={HUB_CONTENT.home.attentionEmpty}
            message={HUB_CONTENT.home.pathsSubtitle}
          />
        ) : null}
        {attentionCards.length > 0 ? (
          <ul className="sp-home__attention-list">
            {attentionCards.map((card) => (
              <li key={card.id}>
                <button
                  type="button"
                  className="sp-home__attention-card"
                  disabled={card.status === "unavailable"}
                  onClick={() => goToCard(card)}
                >
                  <span className="sp-home__attention-title">{card.title}</span>
                  <span className="sp-home__attention-desc">{card.description}</span>
                  <span className="sp-home__attention-count">
                    {card.count == null ? "—" : String(card.count)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="sp-home__paths" aria-label={HUB_CONTENT.home.pathsTitle}>
        <div className="sp-home__paths-head">
          <div>
            <h2>{HUB_CONTENT.home.pathsTitle}</h2>
            <p>{HUB_CONTENT.home.pathsSubtitle}</p>
          </div>
          <label className="sp-home__search">
            <span className="sp-visually-hidden">{HUB_CONTENT.home.searchPlaceholder}</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={HUB_CONTENT.home.searchPlaceholder}
            />
          </label>
        </div>

        {visibleFavorites.length > 0 || visibleRecents.length > 0 ? (
          <div className="sp-home__shortcuts">
            {visibleFavorites.length > 0 ? (
              <div>
                <h3>{HUB_CONTENT.home.favoritesTitle}</h3>
                <ul className="sp-home__route-list">
                  {visibleFavorites.map((item) => (
                    <li key={item.viewId}>
                      <button
                        type="button"
                        className="sp-home__route"
                        onClick={() => goTo(item.viewId, item.label)}
                      >
                        {item.label}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="sp-home__muted">{HUB_CONTENT.home.favoritesEmpty}</p>
            )}
            {visibleRecents.length > 0 ? (
              <div>
                <h3>{HUB_CONTENT.home.recentsTitle}</h3>
                <ul className="sp-home__route-list">
                  {visibleRecents.map((item) => (
                    <li key={`${item.viewId}-${item.at}`}>
                      <button
                        type="button"
                        className="sp-home__route"
                        onClick={() => goTo(item.viewId, item.label)}
                      >
                        {item.label}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}

        {visibleSections.length === 0 ? (
          <SuppliesEmptyState
            title={query.trim() ? HUB_CONTENT.home.searchEmpty : HUB_CONTENT.home.pathsEmpty}
            message={HUB_CONTENT.home.pathsSubtitle}
          />
        ) : (
          visibleSections.map((section) => (
            <div key={section.id} className="sp-home__section">
              <h3>{section.title}</h3>
              {section.description ? <p>{section.description}</p> : null}
              <ul className="sp-home__route-list">
                {section.routes.map((route) => (
                  <li key={route.id} className="sp-home__route-row">
                    <button
                      type="button"
                      className="sp-home__route"
                      onClick={() => {
                        const target = findHubRouteById(sections, route.id) ?? route;
                        goToRoute(target);
                      }}
                    >
                      {route.label}
                    </button>
                    <button
                      type="button"
                      className="sp-home__fav"
                      aria-pressed={favoriteViewIds.has(route.viewId)}
                      aria-label={
                        favoriteViewIds.has(route.viewId)
                          ? `Remover ${route.label} dos favoritos`
                          : `Favoritar ${route.label}`
                      }
                      onClick={() => onToggleFavorite(route)}
                    >
                      {favoriteViewIds.has(route.viewId) ? "★" : "☆"}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </section>

      {session.allowedUnits.length > 0 ? (
        <SuppliesStateBanner>
          Filiais no seu escopo: {session.allowedUnits.join(", ")}.
        </SuppliesStateBanner>
      ) : null}
    </div>
  );
}
