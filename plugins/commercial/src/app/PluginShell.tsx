import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarCheck,
  ClipboardList,
  Home,
  MessagesSquare,
  Users,
} from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { fetchMeProfile, firstNameFromDisplay } from "../api/meApi";
import { getMyWorklist } from "../api/worklistApi";
import { getOpenOrdersTotvs } from "../api/openOrdersTotvsApi";
import { CM_HELP } from "../content/helpTooltips";
import {
  collectSearchHits,
  findHubRouteById,
  HUB_CONTENT,
  resolveHubSections,
} from "../content/pluginRouteCatalog";
import { resolveShellNavItems, SHELL_NAV_CONTENT } from "../content/shellNav";
import { formatCurrency } from "../utils/format";
import { resolveActiveNavId, type PluginNavId, type PluginView } from "./pluginRoutes";
import { navigateCustomerDetail, navigatePluginView } from "./pluginNavigation";
import { useHomeHeroMetricsOptional } from "./HomeHeroMetricsContext";
import {
  useCommercialReadyToInvoiceSync,
  useCommercialWorklistSync,
} from "./CommercialRealtimeProvider";
import { resolveMyTasksNavBadgeCount } from "./myTasksNavBadge";
import { resolveReadyToInvoiceBadgeCount } from "./myOrdersNavBadge";
import {
  CommercialActionButton,
  CommercialCommandPalette,
  CommercialPageHero,
  CommercialStatusBadge,
  CommercialTopBar,
  CommercialViewTransition,
} from "./commercialUi";
import { ShellUserPortfolioMenu } from "./ShellUserPortfolioMenu";
import { ShellFavoritesStrip } from "./ShellFavoritesStrip";

type PluginShellProps = {
  view: PluginView;
  basePath: string;
  search?: string;
  showAdmin?: boolean;
  showWorklist?: boolean;
  showAnalytics?: boolean;
  showCustomers?: boolean;
  showProposals?: boolean;
  scopeLabel?: string;
  /** Conta fora da carteira: item efêmero «Cliente» ativo. */
  ephemeralClientNav?: { codigo: string; loja: string } | null;
  children: ReactNode;
};

const NAV_HELP: Partial<Record<PluginNavId, string>> = {
  home: CM_HELP.shell.navHome,
  overview: CM_HELP.shell.navOverview,
  interaction_rooms: CM_HELP.shell.navInteractionRooms,
  my_tasks: CM_HELP.shell.navMyTasks,
  open_orders: CM_HELP.shell.navOrders,
  customers: CM_HELP.shell.navCustomers,
  client_context: CM_HELP.shell.navCustomers,
  administration: CM_HELP.shell.navAdmin,
};

const NAV_ICONS: Record<PluginNavId, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  overview: <BarChart3 size={16} strokeWidth={1.75} aria-hidden="true" />,
  interaction_rooms: <MessagesSquare size={16} strokeWidth={1.75} aria-hidden="true" />,
  my_tasks: <CalendarCheck size={16} strokeWidth={1.75} aria-hidden="true" />,
  open_orders: <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
  customers: <Users size={16} strokeWidth={1.75} aria-hidden="true" />,
  client_context: <Users size={16} strokeWidth={1.75} aria-hidden="true" />,
  administration: <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />,
};

function greetingForNow(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

export function PluginShell({
  view,
  basePath,
  showAdmin = false,
  showWorklist = false,
  showAnalytics = false,
  showCustomers = false,
  showProposals = false,
  scopeLabel,
  ephemeralClientNav = null,
  children,
}: PluginShellProps) {
  const [myTasksBadge, setMyTasksBadge] = useState(0);
  const [myOrdersBadge, setMyOrdersBadge] = useState(0);
  const [userFirstName, setUserFirstName] = useState<string | null>(null);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const homeMetrics = useHomeHeroMetricsOptional()?.metrics;

  useEffect(() => {
    if (!showWorklist) {
      setMyTasksBadge(0);
      return;
    }
    const controller = new AbortController();
    void getMyWorklist({ signal: controller.signal })
      .then((wl) => {
        setMyTasksBadge(resolveMyTasksNavBadgeCount(wl.counts));
      })
      .catch(() => {
        if (!controller.signal.aborted) setMyTasksBadge(0);
      });
    return () => controller.abort();
  }, [showWorklist, view]);

  useEffect(() => {
    const controller = new AbortController();
    void getOpenOrdersTotvs(controller.signal)
      .then((data) => {
        setMyOrdersBadge(resolveReadyToInvoiceBadgeCount(data.kanbanStageCounts));
      })
      .catch(() => {
        if (!controller.signal.aborted) setMyOrdersBadge(0);
      });
    return () => controller.abort();
  }, [view]);

  const refreshMyTasksBadge = useCallback(() => {
    if (!showWorklist) {
      setMyTasksBadge(0);
      return;
    }
    void getMyWorklist()
      .then((wl) => {
        setMyTasksBadge(resolveMyTasksNavBadgeCount(wl.counts));
      })
      .catch(() => {
        /* keep last known badge */
      });
  }, [showWorklist]);

  const refreshMyOrdersBadge = useCallback(() => {
    void getOpenOrdersTotvs()
      .then((data) => {
        setMyOrdersBadge(resolveReadyToInvoiceBadgeCount(data.kanbanStageCounts));
      })
      .catch(() => {
        /* keep last known badge */
      });
  }, []);

  useCommercialWorklistSync(refreshMyTasksBadge, showWorklist);
  useCommercialReadyToInvoiceSync(refreshMyOrdersBadge, true);

  useEffect(() => {
    const controller = new AbortController();
    void fetchMeProfile(controller.signal)
      .then((profile) => {
        const name = (profile.name ?? "").trim();
        setUserDisplayName(name || null);
        setUserFirstName(firstNameFromDisplay(name));
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setUserDisplayName(null);
          setUserFirstName(null);
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isPaletteChord =
        (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey);
      if (!isPaletteChord) return;
      if (isEditableTarget(event.target) && !paletteOpen) return;
      event.preventDefault();
      setPaletteOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen]);

  const items = resolveShellNavItems({
    analytics: showAnalytics,
    worklist: showWorklist,
    customers: showCustomers,
    admin: showAdmin,
  }).map((item) => ({
    ...item,
    count:
      item.id === "my_tasks"
        ? myTasksBadge || undefined
        : item.id === "open_orders"
          ? myOrdersBadge || undefined
          : undefined,
  }));

  if (ephemeralClientNav) {
    const insertAt = items.findIndex((item) => item.id === "customers");
    const clientItem = {
      id: "client_context" as const,
      label: SHELL_NAV_CONTENT.clientContextLabel,
      requiredCap: "always" as const,
      count: undefined as number | undefined,
    };
    if (insertAt >= 0) {
      items.splice(insertAt + 1, 0, clientItem);
    } else {
      items.push(clientItem);
    }
  }

  const activeId = resolveActiveNavId(view, {
    customerDetailOutsidePortfolio: Boolean(ephemeralClientNav),
  });
  const showGreeting = view === "home";
  const greeting = greetingForNow();
  const heroTitle = userFirstName ? `${greeting}, ${userFirstName}` : greeting;

  const heroCopy = SHELL_NAV_CONTENT.homeHero;
  const lateCount =
    homeMetrics?.ready && homeMetrics.atrasos != null ? homeMetrics.atrasos : null;
  const followUpsValue =
    homeMetrics?.ready && homeMetrics.followUps != null
      ? homeMetrics.followUps > 0
        ? `${homeMetrics.followUps.toLocaleString("pt-BR")} na fila`
        : heroCopy.highlights.followUpsClear
      : myTasksBadge > 0
        ? `${myTasksBadge} na fila`
        : "—";
  const valorValue =
    homeMetrics?.ready && homeMetrics.valorAberto != null
      ? formatCurrency(homeMetrics.valorAberto)
      : "—";
  const atrasosValue =
    lateCount != null ? lateCount.toLocaleString("pt-BR") : "—";

  const heroHighlights = [
    {
      id: "follow-ups",
      label: heroCopy.highlights.followUps,
      value: followUpsValue,
    },
    {
      id: "open-value",
      label: heroCopy.highlights.openValue,
      value: valorValue,
    },
    {
      id: "late",
      label: heroCopy.highlights.late,
      value: atrasosValue,
      tone: lateCount != null && lateCount > 0 ? ("warning" as const) : ("neutral" as const),
    },
  ];

  const contextualCta = homeMetrics?.ready ? homeMetrics.contextualCta : null;

  const catalogCaps = useMemo(
    () => ({
      analytics: showAnalytics,
      worklist: showWorklist,
      proposals: showProposals,
      customers: showCustomers,
      admin: showAdmin,
    }),
    [showAdmin, showAnalytics, showCustomers, showProposals, showWorklist],
  );

  const paletteSections = useMemo(
    () => resolveHubSections(catalogCaps),
    [catalogCaps],
  );

  const paletteHits = useMemo(
    () => collectSearchHits(paletteSections, paletteQuery, 8),
    [paletteQuery, paletteSections],
  );

  const onSelectPaletteHit = useCallback(
    (routeId: string) => {
      const route = findHubRouteById(paletteSections, routeId);
      if (!route) return;
      navigatePluginView(route.viewId, { basePath, search: route.search });
      setPaletteOpen(false);
      setPaletteQuery("");
    },
    [basePath, paletteSections],
  );

  return (
    <div className="dashboard-commercial dashboard-page">
      <div className="cm-page-stack">
        <CommercialTopBar
          aria-label={SHELL_NAV_CONTENT.ariaLabel}
          activeId={activeId ?? ""}
          items={items.map((item) => ({
            id: item.id,
            label: item.label,
            icon: NAV_ICONS[item.id],
            count: item.count,
            title: NAV_HELP[item.id]
              ? `${item.label}. ${NAV_HELP[item.id]}`
              : item.label,
            onSelect: () => {
              if (item.id === "client_context" && ephemeralClientNav) {
                navigateCustomerDetail(
                  ephemeralClientNav.codigo,
                  ephemeralClientNav.loja,
                  { basePath },
                );
                return;
              }
              if (item.id === "client_context") return;
              navigatePluginView(item.id, { basePath });
            },
          }))}
          secondary={<ShellFavoritesStrip basePath={basePath} />}
          actions={
            <ShellUserPortfolioMenu basePath={basePath} displayName={userDisplayName} />
          }
        />

        {showGreeting ? (
          <CommercialViewTransition transitionKey="home-hero" tone="page">
            <CommercialPageHero
              aria-label={heroCopy.ariaLabel}
              eyebrow={heroCopy.eyebrow}
              title={
                <>
                  {heroTitle}
                  <HelpTooltip content={CM_HELP.home.overview} ariaLabel={heroCopy.helpAriaLabel} />
                </>
              }
              description={heroCopy.description}
              badge={
                scopeLabel ? (
                  <CommercialStatusBadge label={scopeLabel} variant="info" />
                ) : (
                  <CommercialStatusBadge label={heroCopy.scopeOwn} variant="neutral" />
                )
              }
              highlights={heroHighlights}
              actions={
                contextualCta ? (
                  <CommercialActionButton
                    variant="primary"
                    onClick={() =>
                      navigatePluginView(contextualCta.viewId, {
                        basePath,
                        search: contextualCta.search,
                      })
                    }
                  >
                    {contextualCta.label}
                  </CommercialActionButton>
                ) : undefined
              }
            />
          </CommercialViewTransition>
        ) : null}

        <CommercialViewTransition transitionKey={view} tone="page">
          {children}
        </CommercialViewTransition>
      </div>

      <CommercialCommandPalette
        open={paletteOpen}
        onClose={() => {
          setPaletteOpen(false);
          setPaletteQuery("");
        }}
        title={HUB_CONTENT.palette.title}
        value={paletteQuery}
        onChange={setPaletteQuery}
        hits={paletteHits.map((hit) => ({
          id: hit.id,
          label: hit.label,
          groupLabel: hit.groupLabel,
        }))}
        onSelectHit={onSelectPaletteHit}
        placeholder={HUB_CONTENT.palette.placeholder}
        emptyHitsLabel={HUB_CONTENT.palette.empty}
        closeAriaLabel={HUB_CONTENT.palette.closeAriaLabel}
        aria-label={CM_HELP.home.palette}
      />
    </div>
  );
}
