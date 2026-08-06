import { useEffect, useState, type ReactNode } from "react";
import {
  BriefcaseBusiness,
  CalendarCheck,
  ClipboardList,
  Home,
  Settings,
  Users,
} from "lucide-react";
import { HelpTooltip, StatusBadge } from "@delpi/plugin-ui/index";

import { fetchMeProfile, firstNameFromDisplay } from "../api/meApi";
import { getMyWorklist } from "../api/worklistApi";
import { CM_HELP } from "../content/helpTooltips";
import { type PluginView } from "./pluginRoutes";
import { navigatePluginView } from "./pluginNavigation";
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
  scopeLabel?: string;
  children: ReactNode;
};

type NavId = Exclude<PluginView, "customer_detail" | "not_found">;

const NAV_HELP: Partial<Record<NavId, string>> = {
  home: CM_HELP.shell.navHome,
  my_day: CM_HELP.shell.navMyDay,
  open_orders: CM_HELP.shell.navOrders,
  customers: CM_HELP.shell.navCustomers,
  seller_portfolios: CM_HELP.shell.navAdmin,
};

const NAV_ICONS: Record<NavId, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  my_day: <CalendarCheck size={16} strokeWidth={1.75} aria-hidden="true" />,
  open_orders: <ClipboardList size={16} strokeWidth={1.75} aria-hidden="true" />,
  customers: <Users size={16} strokeWidth={1.75} aria-hidden="true" />,
  seller_portfolios: <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />,
};

function resolveActiveNavId(view: PluginView): NavId {
  if (view === "customer_detail") return "customers";
  if (view === "not_found") return "home";
  return view;
}

function greetingForNow(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

export function PluginShell({
  view,
  basePath,
  search,
  showAdmin = false,
  showWorklist = false,
  scopeLabel,
  children,
}: PluginShellProps) {
  const [myDayBadge, setMyDayBadge] = useState(0);
  const [userFirstName, setUserFirstName] = useState<string | null>(null);

  useEffect(() => {
    if (!showWorklist) {
      setMyDayBadge(0);
      return;
    }
    const controller = new AbortController();
    void getMyWorklist(controller.signal)
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
    id: NavId;
    label: string;
    count?: number;
  }> = [
    { id: "home", label: "Início" },
    ...(showWorklist
      ? [{ id: "my_day" as const, label: "Meu dia", count: myDayBadge || undefined }]
      : []),
    { id: "open_orders", label: "Pedidos em aberto" },
    { id: "customers", label: "Minha carteira" },
    ...(showAdmin ? [{ id: "seller_portfolios" as const, label: "Carteiras" }] : []),
  ];

  const activeId = resolveActiveNavId(view);
  const showGreeting = view === "home";
  const greeting = greetingForNow();
  const heroTitle = userFirstName ? `${greeting}, ${userFirstName}` : greeting;
  const heroHighlights =
    showWorklist || myDayBadge > 0
      ? [
          {
            id: "my-day",
            label: "Meu dia",
            value: myDayBadge > 0 ? `${myDayBadge} na fila` : "Em dia",
          },
          {
            id: "scope",
            label: "Escopo",
            value: scopeLabel ?? "Carteira própria",
          },
          {
            id: "focus",
            label: "Foco",
            value: "Carteira e follow-ups",
          },
        ]
      : [
          {
            id: "scope",
            label: "Escopo",
            value: scopeLabel ?? "Carteira própria",
          },
          {
            id: "focus",
            label: "Foco",
            value: "Pedidos e carteira",
          },
          {
            id: "next",
            label: "Próximo passo",
            value: "Abrir pedidos ou Conta",
          },
        ];

  return (
    <div className="dashboard-commercial dashboard-pedidos-venda-abertos dashboard-page">
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
              description="Bem vindo ao Portal Comercial! Use o Início para alertas e números da carteira; Meu dia para follow-ups priorizados."
              badge={
                scopeLabel ? (
                  <StatusBadge
                    classNames={cmStatusBadgeClassNames}
                    label={scopeLabel}
                    variant="info"
                  />
                ) : undefined
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
              navigatePluginView(item.id, {
                basePath,
                search: search || undefined,
              }),
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
  target: "orders" | "customers" | "admin" | "my_day";
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
  return <Settings size={22} strokeWidth={1.75} aria-hidden="true" />;
}
