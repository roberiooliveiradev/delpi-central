import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarCheck,
  ClipboardList,
  FileText,
  Settings,
  Target,
  Timer,
  Users,
} from "lucide-react";
import { ActionButton, EmptyState, SectionCard } from "@delpi/plugin-ui/index";

import { CM_HELP } from "../../content/helpTooltips";
import {
  HOME_LAUNCHER_CONTENT,
  resolveHomeLauncherCards,
  type HomeLauncherCardId,
} from "../../content/homeLauncher";
import { getOpenOrders } from "../../api/openOrdersApi";
import { useHomeHeroMetrics } from "../../app/HomeHeroMetricsContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialAlertQueue,
  CommercialLoadingCard,
  CommercialNavigationCard,
  CommercialScopeChipBar,
  CommercialWorklistItem,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { useWorklistPreview } from "../../hooks/useWorklistPreview";
import { formatDisplayDate } from "../../utils/dates";
import type { OpenOrdersData } from "../../types/openOrders";

type HomePageProps = {
  basePath: string;
  showAdmin: boolean;
  showWorklist: boolean;
  showProposals?: boolean;
  showAnalytics?: boolean;
  showCustomers?: boolean;
  canUseTeamScope?: boolean;
};

type HomeOrdersSummary = {
  totalLinhas: number;
  valorAberto: number;
  atrasos: number;
};

const emptySummary: HomeOrdersSummary = { totalLinhas: 0, valorAberto: 0, atrasos: 0 };

const EVENTS = HOME_LAUNCHER_CONTENT.events;
const FEATURES = HOME_LAUNCHER_CONTENT.features;

const LAUNCHER_ICONS: Record<HomeLauncherCardId, ReactNode> = {
  overview: <BarChart3 size={22} strokeWidth={1.75} aria-hidden="true" />,
  my_tasks: <CalendarCheck size={22} strokeWidth={1.75} aria-hidden="true" />,
  open_orders: <ClipboardList size={22} strokeWidth={1.75} aria-hidden="true" />,
  customers: <Users size={22} strokeWidth={1.75} aria-hidden="true" />,
  proposals: <FileText size={22} strokeWidth={1.75} aria-hidden="true" />,
  analytics_otd: <Timer size={22} strokeWidth={1.75} aria-hidden="true" />,
  analytics_opportunities: <Target size={22} strokeWidth={1.75} aria-hidden="true" />,
  analytics_team: <BriefcaseBusiness size={22} strokeWidth={1.75} aria-hidden="true" />,
  administration: <Settings size={22} strokeWidth={1.75} aria-hidden="true" />,
};

const cmEmptyQuietClassNames = {
  ...cmEmptyStateClassNames,
  root: `${cmEmptyStateClassNames.root} delpi-ui-state-box--compact cm-empty-quiet`,
  withTitle: true,
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

export function HomePage({
  basePath,
  showAdmin,
  showWorklist,
  showProposals = false,
  showAnalytics = false,
  showCustomers = false,
  canUseTeamScope = false,
}: HomePageProps) {
  const { sellerIdFilter } = usePortfolioScope();
  const { setMetrics, resetMetrics } = useHomeHeroMetrics();
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [summary, setSummary] = useState<HomeOrdersSummary>(emptySummary);
  const worklist = useWorklistPreview({ enabled: showWorklist });

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

  const eventsReady = !ordersLoading && (!showWorklist || !worklist.loading);

  useEffect(() => {
    if (!eventsReady) {
      setMetrics({ valorAberto: null, atrasos: null, followUps: null, ready: false });
      return;
    }
    setMetrics({
      valorAberto: ordersError ? null : summary.valorAberto,
      atrasos: ordersError ? null : summary.atrasos,
      followUps: showWorklist ? (worklist.error ? null : worklist.counts.open) : null,
      ready: true,
    });
  }, [
    eventsReady,
    ordersError,
    setMetrics,
    showWorklist,
    summary.atrasos,
    summary.valorAberto,
    worklist.counts.open,
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

  const alerts = useMemo(() => {
    if (!eventsReady) return [];
    const items = [];
    if (summary.atrasos > 0) {
      items.push({
        id: "late-orders",
        title: `${summary.atrasos} linha(s) em atraso`,
        description: "Revise pedidos em aberto e priorize entregas vencidas.",
        tone: "warning" as const,
        actionLabel: "Ver atrasos",
        onAction: () =>
          navigatePluginView("open_orders", { basePath, search: "?focus=late" }),
      });
    }
    if (showWorklist && worklist.counts.overdue > 0) {
      items.push({
        id: "overdue-tasks",
        title: `${worklist.counts.overdue} follow-up(s) atrasado(s)`,
        description: "Conclua ou reagende na fila de Minhas tarefas.",
        tone: "danger" as const,
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
        actionLabel: "Ver carteira",
        onAction: () => navigatePluginView("customers", { basePath }),
      });
    }
    return items;
  }, [
    basePath,
    eventsReady,
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
    return [
      {
        id: "overdue",
        label: `${EVENTS.buckets.overdue} ${overdue.toLocaleString("pt-BR")}`,
        active: overdue > 0,
        onSelect: () => openMyTasks("overdue"),
      },
      {
        id: "today",
        label: `${EVENTS.buckets.today} ${today.toLocaleString("pt-BR")}`,
        onSelect: () => openMyTasks("today"),
      },
      {
        id: "later",
        label: `${EVENTS.buckets.later} ${later.toLocaleString("pt-BR")}`,
        onSelect: () => openMyTasks(),
      },
    ];
  }, [openMyTasks, worklist.counts]);

  const launcherCards = useMemo(
    () =>
      resolveHomeLauncherCards({
        analytics: showAnalytics,
        worklist: showWorklist,
        proposals: showProposals,
        customers: showCustomers,
        team: showAnalytics && canUseTeamScope,
        admin: showAdmin,
      }),
    [canUseTeamScope, showAdmin, showAnalytics, showCustomers, showProposals, showWorklist],
  );

  const hasEvents = alerts.length > 0 || worklist.items.length > 0;

  return (
    <section className="cm-page-stack cm-home-layout" aria-label="Início">
      <div className="cm-home-columns">
        <div className="cm-home-columns__main">
          <SectionCard
            title={FEATURES.title}
            subtitle={FEATURES.subtitle}
            hint={CM_HELP.home.shortcuts}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            {launcherCards.length === 0 ? (
              <EmptyState
                classNames={cmEmptyStateClassNames}
                defaultMessage={FEATURES.empty}
              />
            ) : (
              <div className="cm-home-grid" aria-label={FEATURES.gridAriaLabel}>
                {launcherCards.map((card) => (
                  <div key={card.id} className="cm-launcher-cell">
                    <CommercialNavigationCard
                      title={card.title}
                      description={card.description}
                      icon={LAUNCHER_ICONS[card.id]}
                      onClick={() => navigatePluginView(card.viewId, { basePath })}
                    />
                    {card.quickLinks?.length ? (
                      <div className="cm-nav-row">
                        {card.quickLinks.map((link) => (
                          <ActionButton
                            key={link.id}
                            variant="ghost"
                            onClick={() =>
                              navigatePluginView(link.viewId, {
                                basePath,
                                search: link.search,
                              })
                            }
                          >
                            {link.label}
                          </ActionButton>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        <aside className="cm-home-columns__side">
          <SectionCard
            title={EVENTS.title}
            subtitle={EVENTS.subtitle}
            hint={CM_HELP.home.alerts}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
            actions={
              <>
                <ActionButton
                  variant="ghost"
                  onClick={() => {
                    reloadOrders();
                    worklist.reload();
                  }}
                >
                  {EVENTS.refresh}
                </ActionButton>
                {showWorklist ? (
                  <ActionButton variant="primary" onClick={() => openMyTasks()}>
                    {EVENTS.cta}
                  </ActionButton>
                ) : null}
              </>
            }
          >
            {!eventsReady ? (
              <CommercialLoadingCard title={EVENTS.loading} variant="panel" />
            ) : (
              <div className="cm-home-events-panel">
                {ordersError ? (
                  <EmptyState
                    classNames={cmEmptyStateClassNames}
                    defaultMessage={`Pedidos: ${ordersError}`}
                    role="alert"
                  />
                ) : null}
                {worklist.error ? (
                  <EmptyState
                    classNames={cmEmptyStateClassNames}
                    defaultMessage={`Minhas tarefas: ${worklist.error}`}
                    role="alert"
                  />
                ) : null}
                {showWorklist && !worklist.error && queueChips.length > 0 ? (
                  <CommercialScopeChipBar
                    label={EVENTS.queueLabel}
                    aria-label={EVENTS.queueLabel}
                    chips={queueChips}
                  />
                ) : null}
                {alerts.length > 0 ? <CommercialAlertQueue items={alerts} /> : null}
                {worklist.items.length > 0 ? (
                  <div className="cm-home-events-list" aria-label={EVENTS.listAriaLabel}>
                    {worklist.items.map(({ task, bucket }) => (
                      <CommercialWorklistItem
                        key={task.id}
                        title={task.title}
                        tone={
                          bucket === "overdue"
                            ? "danger"
                            : bucket === "today"
                              ? "warning"
                              : "neutral"
                        }
                        meta={[
                          EVENTS.buckets[bucket],
                          task.due_at ? formatDisplayDate(task.due_at) : EVENTS.noDueDate,
                          task.customer_code ? `Cliente ${task.customer_code}` : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                        detail={task.description ?? undefined}
                        primaryActionLabel={EVENTS.openTask}
                        onPrimaryAction={() =>
                          openMyTasks(bucket === "later" ? undefined : bucket)
                        }
                      />
                    ))}
                  </div>
                ) : null}
                {!hasEvents ? (
                  <EmptyState
                    classNames={cmEmptyQuietClassNames}
                    defaultTitle={EVENTS.emptyTitle}
                    defaultMessage={EVENTS.emptyMessage}
                  />
                ) : null}
              </div>
            )}
          </SectionCard>
        </aside>
      </div>
    </section>
  );
}
