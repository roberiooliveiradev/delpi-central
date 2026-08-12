import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  ArrowRight,
  BarChart3,
  CircleAlert,
  ClipboardList,
  Clock,
  FileText,
  Settings,
  Sun,
  TriangleAlert,
  Users,
} from "lucide-react";
import { EmptyState, SectionCard } from "@delpi/plugin-ui/index";

import { getHomeFavorites, putHomeFavorites, type HomeFavoriteItem } from "../../api/homeFavoritesApi";
import { getOpenOrders } from "../../api/openOrdersApi";
import { useHomeHeroMetrics } from "../../app/HomeHeroMetricsContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import type { PluginNavigationTarget } from "../../app/pluginRoutes";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialAlertQueue,
  CommercialCatalogSearchBar,
  CommercialHubChipRow,
  CommercialLoadingCard,
  CommercialRouteChip,
  CommercialScopeChipBar,
  CommercialSectionRouteCard,
  CommercialWorklistItem,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { CM_HELP } from "../../content/helpTooltips";
import { resolveHubRouteIcon } from "../../content/hubRouteIcons";
import {
  collectSearchHits,
  filterRouteCatalog,
  findHubRouteById,
  hubRouteLabelByView,
  HUB_CONTENT,
  resolveHomeContextualCta,
  resolveHubSections,
  type HubRouteDef,
  type HubSectionDef,
  type HubSectionId,
} from "../../content/pluginRouteCatalog";
import { useWorklistPreview } from "../../hooks/useWorklistPreview";
import { formatDisplayDate } from "../../utils/dates";
import type { OpenOrdersData } from "../../types/openOrders";
import {
  filterRecentsByCaps,
  pushRecentView,
  readRecentViews,
  type RecentHubView,
} from "./homeRecentViews";
import { readHomeSearchQuery, writeHomeSearchQuery } from "./homeSearchQuery";

type HomePageProps = {
  basePath: string;
  showAdmin: boolean;
  showWorklist: boolean;
  showProposals?: boolean;
  showAnalytics?: boolean;
  showCustomers?: boolean;
};

type HomeOrdersSummary = {
  totalLinhas: number;
  valorAberto: number;
  atrasos: number;
};

const emptySummary: HomeOrdersSummary = { totalLinhas: 0, valorAberto: 0, atrasos: 0 };
const EVENTS = HUB_CONTENT.events;
const FEATURES = HUB_CONTENT.features;

const SECTION_ICONS: Record<HubSectionId, ReactNode> = {
  operations: <ClipboardList size={20} strokeWidth={1.75} aria-hidden="true" />,
  management: <BarChart3 size={20} strokeWidth={1.75} aria-hidden="true" />,
  documents: <FileText size={20} strokeWidth={1.75} aria-hidden="true" />,
  administration: <Settings size={20} strokeWidth={1.75} aria-hidden="true" />,
};

function summaryFromOpenOrders(data: OpenOrdersData): HomeOrdersSummary {
  const items = data.items ?? [];
  const summary = data.summary as
    | (OpenOrdersData["summary"] & { linhas_em_atraso?: number })
    | undefined;
  const lateFromItems = items.filter((item) => {
    const status = `${item.status ?? ""} ${item.tipo_pedido ?? ""}`.toLowerCase();
    return status.includes("atras");
  }).length;
  return {
    totalLinhas: summary?.total_linhas ?? items.length,
    valorAberto: summary?.valor_total_aberto ?? 0,
    atrasos: summary?.linhas_em_atraso ?? lateFromItems,
  };
}

function favoriteKey(item: { viewId: string; search?: string }): string {
  return `${item.viewId}::${item.search ?? ""}`;
}

export function HomePage({
  basePath,
  showAdmin,
  showWorklist,
  showProposals = false,
  showAnalytics = false,
  showCustomers = false,
}: HomePageProps) {
  const { sellerIdFilter } = usePortfolioScope();
  const { setMetrics, resetMetrics } = useHomeHeroMetrics();
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [summary, setSummary] = useState<HomeOrdersSummary>(emptySummary);
  const worklist = useWorklistPreview({ enabled: showWorklist });
  const [searchQuery, setSearchQuery] = useState(() =>
    typeof window !== "undefined" ? readHomeSearchQuery() : "",
  );
  const [recents, setRecents] = useState<RecentHubView[]>(() =>
    typeof window !== "undefined" ? readRecentViews() : [],
  );
  const [favorites, setFavorites] = useState<HomeFavoriteItem[]>([]);
  const [favoritesError, setFavoritesError] = useState<string | null>(null);

  const capabilities = useMemo(
    () => ({
      analytics: showAnalytics,
      worklist: showWorklist,
      proposals: showProposals,
      customers: showCustomers,
      admin: showAdmin,
    }),
    [showAdmin, showAnalytics, showCustomers, showProposals, showWorklist],
  );

  const sections = useMemo(() => resolveHubSections(capabilities), [capabilities]);

  const reloadOrders = useCallback(() => {
    const controller = new AbortController();
    setOrdersLoading(true);
    setOrdersError(null);
    void getOpenOrders(controller.signal, { sellerId: sellerIdFilter })
      .then((data) => {
        if (controller.signal.aborted) return;
        setSummary(summaryFromOpenOrders(data));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOrdersError(err instanceof Error ? err.message : "Erro ao carregar pedidos.");
        setSummary(emptySummary);
      })
      .finally(() => {
        if (!controller.signal.aborted) setOrdersLoading(false);
      });
    return () => controller.abort();
  }, [sellerIdFilter]);

  useEffect(() => reloadOrders(), [reloadOrders]);

  useEffect(() => {
    const controller = new AbortController();
    void getHomeFavorites(controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) {
          setFavorites(items);
          setFavoritesError(null);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setFavorites([]);
          setFavoritesError(FEATURES.favoritesLoadError);
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => writeHomeSearchQuery(searchQuery), 200);
    return () => window.clearTimeout(handle);
  }, [searchQuery]);

  const eventsReady = !ordersLoading && (!showWorklist || !worklist.loading);

  useEffect(() => {
    if (!eventsReady) {
      setMetrics({
        valorAberto: null,
        atrasos: null,
        followUps: null,
        ready: false,
        contextualCta: null,
      });
      return;
    }
    const contextualCta = resolveHomeContextualCta({
      ready: true,
      ordersLate: ordersError ? null : summary.atrasos,
      tasksOverdue: showWorklist && !worklist.error ? worklist.counts.overdue : null,
      tasksToday: showWorklist && !worklist.error ? worklist.counts.today : null,
    });
    setMetrics({
      valorAberto: ordersError ? null : summary.valorAberto,
      atrasos: ordersError ? null : summary.atrasos,
      followUps: showWorklist ? (worklist.error ? null : worklist.counts.open) : null,
      ready: true,
      contextualCta,
    });
  }, [
    eventsReady,
    ordersError,
    setMetrics,
    showWorklist,
    summary.atrasos,
    summary.valorAberto,
    worklist.counts.open,
    worklist.counts.overdue,
    worklist.counts.today,
    worklist.error,
  ]);

  useEffect(() => () => resetMetrics(), [resetMetrics]);

  const openMyTasks = useCallback(
    (bucket?: "overdue" | "today") =>
      navigatePluginView("my_tasks", {
        basePath,
        search: bucket ? `?bucket=${bucket}` : undefined,
      }),
    [basePath],
  );

  const recordVisit = useCallback(
    (viewId: PluginNavigationTarget, search: string | undefined, label: string) => {
      setRecents(
        pushRecentView({
          viewId,
          search,
          label,
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

  const alerts = useMemo(() => {
    if (!eventsReady) return [];
    const items = [];
    if (summary.atrasos > 0) {
      items.push({
        id: "late-orders",
        title: `${summary.atrasos} linha(s) em atraso`,
        description: "Revise pedidos em aberto e priorize entregas vencidas.",
        tone: "warning" as const,
        leadingIcon: <TriangleAlert size={18} strokeWidth={1.75} aria-hidden="true" />,
        actionLabel: "Ver atrasos",
        onAction: () => navigateRoute({
          viewId: "open_orders",
          search: "?focus=late",
          label: hubRouteLabelByView("open_orders", "?focus=late") ?? "Em atraso",
        }),
      });
    }
    if (showWorklist && worklist.counts.overdue > 0) {
      items.push({
        id: "overdue-tasks",
        title: `${worklist.counts.overdue} follow-up(s) atrasado(s)`,
        description: "Conclua ou reagende na fila de Minhas tarefas.",
        tone: "danger" as const,
        leadingIcon: <CircleAlert size={18} strokeWidth={1.75} aria-hidden="true" />,
        actionLabel: EVENTS.openOverdue,
        onAction: () => openMyTasks("overdue"),
      });
    }
    if (summary.totalLinhas === 0 && !ordersError && showCustomers) {
      items.push({
        id: "no-orders",
        title: "Nenhum pedido em aberto na carteira",
        description: "Abra a carteira para acompanhar clientes.",
        tone: "neutral" as const,
        leadingIcon: <Users size={18} strokeWidth={1.75} aria-hidden="true" />,
        actionLabel: "Ver carteira",
        onAction: () =>
          navigateRoute({
            viewId: "customers",
            label: hubRouteLabelByView("customers") ?? "Minha Carteira",
          }),
      });
    }
    return items;
  }, [
    eventsReady,
    navigateRoute,
    openMyTasks,
    ordersError,
    showCustomers,
    showWorklist,
    summary.atrasos,
    summary.totalLinhas,
    worklist.counts.overdue,
  ]);

  const queueChips = useMemo(() => {
    const { overdue, today, later } = worklist.counts;
    const total = overdue + today + later;
    if (total === 0) return [];
    const withIcon = (icon: ReactNode, text: string) => (
      <span className="cm-home-queue-chip-label">
        {icon}
        {text}
      </span>
    );
    return [
      {
        id: "overdue",
        label: withIcon(
          <Clock size={14} strokeWidth={1.75} aria-hidden="true" />,
          `${EVENTS.buckets.overdue} ${overdue.toLocaleString("pt-BR")}`,
        ),
        active: overdue > 0,
        onSelect: () => openMyTasks("overdue"),
      },
      {
        id: "today",
        label: withIcon(
          <Sun size={14} strokeWidth={1.75} aria-hidden="true" />,
          `${EVENTS.buckets.today} ${today.toLocaleString("pt-BR")}`,
        ),
        active: today > 0,
        onSelect: () => openMyTasks("today"),
      },
      {
        id: "later",
        label: withIcon(
          <ArrowRight size={14} strokeWidth={1.75} aria-hidden="true" />,
          `${EVENTS.buckets.later} ${later.toLocaleString("pt-BR")}`,
        ),
        active: later > 0,
        onSelect: () => openMyTasks(),
      },
    ];
  }, [openMyTasks, worklist.counts]);

  const badgeFor = useCallback(
    (route: HubRouteDef): number | undefined => {
      if (!route.badgeKey || ordersLoading || (showWorklist && worklist.loading)) {
        return undefined;
      }
      if (route.badgeKey === "orders_late") {
        if (ordersError) return undefined;
        return summary.atrasos > 0 ? summary.atrasos : undefined;
      }
      if (!showWorklist || worklist.error) return undefined;
      if (route.badgeKey === "tasks_overdue") {
        return worklist.counts.overdue > 0 ? worklist.counts.overdue : undefined;
      }
      if (route.badgeKey === "tasks_today") {
        return worklist.counts.today > 0 ? worklist.counts.today : undefined;
      }
      return undefined;
    },
    [
      ordersError,
      ordersLoading,
      showWorklist,
      summary.atrasos,
      worklist.counts.overdue,
      worklist.counts.today,
      worklist.error,
      worklist.loading,
    ],
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

  const favoriteKeys = useMemo(
    () => new Set(favorites.map((item) => favoriteKey(item))),
    [favorites],
  );

  const toggleFavorite = useCallback(
    async (route: { viewId: PluginNavigationTarget; search?: string }) => {
      const item: HomeFavoriteItem = {
        viewId: route.viewId,
        search: route.search,
      };
      const key = favoriteKey(item);
      const previous = favorites;
      const next = favoriteKeys.has(key)
        ? favorites.filter((entry) => favoriteKey(entry) !== key)
        : [...favorites, item].slice(0, 20);
      setFavorites(next);
      try {
        const saved = await putHomeFavorites(next);
        setFavorites(saved);
        setFavoritesError(null);
      } catch {
        setFavorites(previous);
        setFavoritesError(FEATURES.favoritesSaveError);
      }
    },
    [favoriteKeys, favorites],
  );

  const mapSectionRoutes = useCallback(
    (section: HubSectionDef) =>
      section.routes.map((route) => ({
        id: route.id,
        label: route.label,
        kind: route.kind,
        badge: badgeFor(route),
        pinned: favoriteKeys.has(favoriteKey(route)),
        pinLabel: FEATURES.pinLabel,
        unpinLabel: FEATURES.unpinLabel,
        onPinClick: () => {
          void toggleFavorite(route);
        },
        onClick: () => navigateRoute(route),
      })),
    [badgeFor, favoriteKeys, navigateRoute, toggleFavorite],
  );

  const hasEvents = alerts.length > 0 || worklist.items.length > 0;
  const showEventsPanel = eventsReady && hasEvents;
  const showQueueOk = eventsReady && !hasEvents;

  return (
    <section className="cm-page-stack cm-home-layout" aria-label="Início">
      <div className="cm-home-stack">
        {showEventsPanel ? (
          <SectionCard
            title={EVENTS.title}
            subtitle={EVENTS.subtitle}
            hint={CM_HELP.home.alerts}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
            actions={
              <>
                <CommercialActionButton
                  variant="ghost"
                  onClick={() => {
                    reloadOrders();
                    worklist.reload();
                  }}
                >
                  {EVENTS.refresh}
                </CommercialActionButton>
                {showWorklist ? (
                  <CommercialActionButton variant="primary" onClick={() => openMyTasks()}>
                    {EVENTS.cta}
                  </CommercialActionButton>
                ) : null}
              </>
            }
          >
            <div className="cm-home-events-panel">
              {alerts.length > 0 ? <CommercialAlertQueue items={alerts} /> : null}
              {showWorklist && worklist.items.length > 0 ? (
                <>
                  {queueChips.length > 0 ? (
                    <CommercialScopeChipBar label={EVENTS.queueLabel} chips={queueChips} />
                  ) : null}
                  <div className="cm-home-events-list" aria-label={EVENTS.listAriaLabel}>
                    {worklist.items.map(({ task, bucket }) => (
                      <CommercialWorklistItem
                        key={task.id}
                        title={task.title}
                        leadingIcon={
                          <ClipboardList size={18} strokeWidth={1.75} aria-hidden="true" />
                        }
                        tone={
                          bucket === "overdue"
                            ? "danger"
                            : bucket === "today"
                              ? "warning"
                              : "neutral"
                        }
                        meta={[
                          bucket === "overdue"
                            ? EVENTS.buckets.overdue
                            : bucket === "today"
                              ? EVENTS.buckets.today
                              : EVENTS.buckets.later,
                          task.due_at
                            ? formatDisplayDate(task.due_at)
                            : EVENTS.noDueDate,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                        primaryActionLabel={EVENTS.openTask}
                        onPrimaryAction={() =>
                          openMyTasks(bucket === "later" ? undefined : bucket)
                        }
                      />
                    ))}
                  </div>
                </>
              ) : null}
            </div>
          </SectionCard>
        ) : null}

        {showQueueOk ? (
          <div className="cm-home-queue-ok" role="status">
            <span>{EVENTS.queueOkTitle}</span>
            {showWorklist ? (
              <CommercialActionButton variant="ghost" onClick={() => openMyTasks()}>
                {EVENTS.queueOkCta}
              </CommercialActionButton>
            ) : null}
          </div>
        ) : null}

        {!eventsReady ? (
          <CommercialLoadingCard title={EVENTS.loading} variant="panel" />
        ) : null}

        <SectionCard
          title={FEATURES.title}
          subtitle={FEATURES.subtitle}
          hint={CM_HELP.home.shortcuts}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <div className="cm-home-paths">
            <CommercialCatalogSearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              hits={searchHits.map((hit) => ({
                id: hit.id,
                label: hit.label,
                groupLabel: hit.groupLabel,
              }))}
              onSelectHit={(id) => {
                const route = findHubRouteById(sections, id);
                if (route) navigateRoute(route);
              }}
              placeholder={FEATURES.searchPlaceholder}
              clearLabel={FEATURES.clearSearch}
              emptyHitsLabel={FEATURES.searchEmpty}
              aria-label={FEATURES.searchAriaLabel}
            />

            {favoritesError ? (
              <p className="cm-home-inline-error" role="status">
                {favoritesError}
              </p>
            ) : null}

            {favorites.length > 0 ? (
              <CommercialHubChipRow
                label={FEATURES.favoritesTitle}
                aria-label={FEATURES.favoritesTitle}
              >
                {favorites.map((item) => {
                  const label =
                    hubRouteLabelByView(item.viewId, item.search) ?? item.viewId;
                  return (
                    <CommercialRouteChip
                      key={favoriteKey(item)}
                      tone="pinned"
                      label={label}
                      onNavigate={() =>
                        navigateRoute({
                          viewId: item.viewId,
                          search: item.search,
                          label,
                        })
                      }
                      onRemove={() => {
                        void toggleFavorite(item);
                      }}
                      removeLabel={FEATURES.unpinLabel}
                    />
                  );
                })}
              </CommercialHubChipRow>
            ) : null}

            {visibleRecents.length > 0 ? (
              <CommercialHubChipRow
                label={FEATURES.recentsTitle}
                aria-label={FEATURES.recentsTitle}
              >
                {visibleRecents.map((item) => (
                  <CommercialRouteChip
                    key={`${favoriteKey(item)}-${item.at}`}
                    tone="recent"
                    label={item.label}
                    leadingIcon={resolveHubRouteIcon(item.viewId)}
                    onNavigate={() =>
                      navigateRoute({
                        viewId: item.viewId,
                        search: item.search,
                        label: item.label,
                      })
                    }
                  />
                ))}
              </CommercialHubChipRow>
            ) : null}

            {sections.length === 0 ? (
              <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={FEATURES.empty} />
            ) : filteredSections.length === 0 ? (
              <EmptyState
                classNames={cmEmptyStateClassNames}
                defaultMessage={FEATURES.searchEmpty}
              />
            ) : (
              <div className="cm-home-sections-grid" aria-label={FEATURES.gridAriaLabel}>
                {filteredSections.map((section) => (
                  <CommercialSectionRouteCard
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
        </SectionCard>
      </div>
    </section>
  );
}
