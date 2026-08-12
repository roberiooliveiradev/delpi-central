import { useEffect, useState, type ReactNode } from "react";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarCheck,
  ClipboardList,
  FileText,
  Home,
  Settings,
  Users,
} from "lucide-react";
import { HelpTooltip, StatusBadge } from "@delpi/plugin-ui/index";

import { fetchMeProfile, firstNameFromDisplay } from "../api/meApi";
import { getMyWorklist } from "../api/worklistApi";
import { CM_HELP } from "../content/helpTooltips";
import { formatCurrency } from "../utils/format";
import { AnalyticsSubNav } from "../features/analytics/components/AnalyticsSubNav";
import { isAnalyticsView, resolveActiveNavId, type PluginNavId, type PluginView } from "./pluginRoutes";
import { navigatePluginView } from "./pluginNavigation";
import { useHomeHeroMetricsOptional } from "./HomeHeroMetricsContext";
import {
  CommercialPageHero,
  CommercialScopeChipBar,
  CommercialTopBar,
  CommercialViewTransition,
  cmStatusBadgeClassNames,
} from "./commercialUi";

type PluginShellProps = {
  view: PluginView;
  basePath: string;
  search?: string;
  showAdmin?: boolean;
  showWorklist?: boolean;
  showProposals?: boolean;
  showAnalytics?: boolean;
  showCustomers?: boolean;
  scopeLabel?: string;
  children: ReactNode;
};

const NAV_HELP: Partial<Record<PluginNavId, string>> = {
  home: CM_HELP.shell.navHome,
  my_day: CM_HELP.shell.navMyDay,
  open_orders: CM_HELP.shell.navOrders,
  customers: CM_HELP.shell.navCustomers,
  proposals: CM_HELP.shell.navProposals,
  analytics: CM_HELP.shell.navGestao,
  seller_portfolios: CM_HELP.shell.navAdmin,
};

const NAV_ICONS: Record<PluginNavId, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  my_day: <CalendarCheck size={16} strokeWidth={1.75} aria-hidden="true" />,
  open_orders: <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
  customers: <Users size={16} strokeWidth={1.75} aria-hidden="true" />,
  proposals: <FileText size={16} strokeWidth={1.75} aria-hidden="true" />,
  analytics: <BarChart3 size={16} strokeWidth={1.75} aria-hidden="true" />,
  seller_portfolios: <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />,
};

function greetingForNow(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

export function PluginShell({
  view,
  basePath,
  showAdmin = false,
  showWorklist = false,
  showProposals = false,
  showAnalytics = false,
  showCustomers = false,
  scopeLabel,
  children,
}: PluginShellProps) {
  const [myDayBadge, setMyDayBadge] = useState(0);
  const [userFirstName, setUserFirstName] = useState<string | null>(null);
  const homeMetrics = useHomeHeroMetricsOptional()?.metrics;

  useEffect(() => {
    if (!showWorklist) {
      setMyDayBadge(0);
      return;
    }
    const controller = new AbortController();
    void getMyWorklist({ signal: controller.signal })
      .then((wl) => {
        setMyDayBadge((wl.counts.overdue ?? 0) + (wl.counts.today ?? 0));
      })
      .catch(() => {
        if (!controller.signal.aborted) setMyDayBadge(0);
      });
    return () => controller.abort();
  }, [showWorklist, view]);

  useEffect(() => {
    const controller = new AbortController();
    void fetchMeProfile(controller.signal)
      .then((profile) => {
        setUserFirstName(firstNameFromDisplay(profile.name));
      })
      .catch(() => {
        if (!controller.signal.aborted) setUserFirstName(null);
      });
    return () => controller.abort();
  }, []);

  const items: Array<{
    id: PluginNavId;
    label: string;
    count?: number;
  }> = [
    { id: "home", label: "Início" },
    ...(showWorklist
      ? [{ id: "my_day" as const, label: "Meu dia", count: myDayBadge || undefined }]
      : []),
    { id: "open_orders", label: "Meus pedidos" },
    ...(showCustomers ? [{ id: "customers" as const, label: "Minha Carteira" }] : []),
    ...(showProposals ? [{ id: "proposals" as const, label: "Propostas" }] : []),
    ...(showAnalytics ? [{ id: "analytics" as const, label: "Gestão" }] : []),
    ...(showAdmin ? [{ id: "seller_portfolios" as const, label: "Carteiras" }] : []),
  ];

  const activeId = resolveActiveNavId(view);
  const showGreeting = view === "home";
  const greeting = greetingForNow();
  const heroTitle = userFirstName ? `${greeting}, ${userFirstName}` : greeting;

  const followUpsValue =
    homeMetrics?.ready && homeMetrics.followUps != null
      ? homeMetrics.followUps > 0
        ? `${homeMetrics.followUps.toLocaleString("pt-BR")} na fila`
        : "Em dia"
      : myDayBadge > 0
        ? `${myDayBadge} na fila`
        : "—";
  const valorValue =
    homeMetrics?.ready && homeMetrics.valorAberto != null
      ? formatCurrency(homeMetrics.valorAberto)
      : "—";
  const atrasosValue =
    homeMetrics?.ready && homeMetrics.atrasos != null
      ? homeMetrics.atrasos.toLocaleString("pt-BR")
      : "—";

  const heroHighlights = [
    {
      id: "follow-ups",
      label: "Follow-ups",
      value: followUpsValue,
    },
    {
      id: "open-value",
      label: "Valor em aberto",
      value: valorValue,
    },
    {
      id: "late",
      label: "Atrasos",
      value: atrasosValue,
    },
  ];

  return (
    <div className="dashboard-commercial dashboard-page">
      <div className="cm-page-stack">
        {showGreeting ? (
          <CommercialViewTransition transitionKey="home-hero" tone="page">
            <CommercialPageHero
              aria-label="Saudação"
              eyebrow="Portal Comercial"
              title={
                <>
                  {heroTitle}
                  <HelpTooltip content={CM_HELP.home.overview} ariaLabel="Ajuda: Início" />
                </>
              }
              description="Bem vindo ao Portal Comercial! Alertas e números da carteira abaixo — use a navegação para operar."
              badge={
                scopeLabel ? (
                  <StatusBadge
                    classNames={cmStatusBadgeClassNames}
                    label={scopeLabel}
                    variant="info"
                  />
                ) : (
                  <StatusBadge
                    classNames={cmStatusBadgeClassNames}
                    label="Carteira própria"
                    variant="neutral"
                  />
                )
              }
              highlights={heroHighlights}
            />
          </CommercialViewTransition>
        ) : null}

        <CommercialTopBar
          aria-label="Áreas do Portal Comercial"
          activeId={activeId}
          items={items.map((item) => ({
            id: item.id,
            label: item.label,
            icon: NAV_ICONS[item.id],
            count: item.count,
            title: NAV_HELP[item.id]
              ? `${item.label}. ${NAV_HELP[item.id]}`
              : item.label,
            onSelect: () =>
              // Nav de topo: path limpo. Não reaproveitar query da view atual
              // (ex.: ?pedido=&linha= reabre modal; datas de Gestão vazam em Pedidos).
              navigatePluginView(item.id, { basePath }),
          }))}
          actions={
            scopeLabel ? (
              <>
                <CommercialScopeChipBar
                  label="Escopo"
                  chips={[{ id: "scope", label: scopeLabel, active: true }]}
                />
                <HelpTooltip content={CM_HELP.shell.scope} ariaLabel="Ajuda: Escopo" />
              </>
            ) : undefined
          }
        />

        {isAnalyticsView(view) && showAnalytics ? (
          <AnalyticsSubNav view={view} basePath={basePath} />
        ) : null}

        <CommercialViewTransition transitionKey={view} tone="page">
          {children}
        </CommercialViewTransition>
      </div>
    </div>
  );
}

export function HomeNavIcon({
  target,
}: {
  target: "orders" | "customers" | "admin" | "my_day" | "proposals" | "analytics";
}) {
  if (target === "orders") {
    return <ClipboardList size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  if (target === "customers") {
    return <Users size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  if (target === "my_day") {
    return <CalendarCheck size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  if (target === "proposals") {
    return <FileText size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  if (target === "analytics") {
    return <BarChart3 size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  return <Settings size={22} strokeWidth={1.75} aria-hidden="true" />;
}
