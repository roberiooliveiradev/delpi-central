import { useEffect, useState, type ReactNode } from "react";
import {
  BriefcaseBusiness,
  CalendarCheck,
  ClipboardList,
  Settings,
  Users,
} from "lucide-react";
import { HelpTooltip, PageHeader } from "@delpi/plugin-ui/index";

import { getMyWorklist } from "../api/worklistApi";
import { CM_HELP } from "../content/helpTooltips";
import { type PluginView } from "./pluginRoutes";
import { navigatePluginView } from "./pluginNavigation";
import {
  cmPageHeaderClassNames,
  CommercialScopeChipBar,
  CommercialTitleWithHelp,
  CommercialUnderlineNav,
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

function resolveActiveNavId(view: PluginView): NavId {
  if (view === "customer_detail") return "customers";
  if (view === "not_found") return "home";
  return view;
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

  return (
    <div className="dashboard-commercial dashboard-pedidos-venda-abertos dashboard-page">
      <div className="cm-page-stack">
        <div className="cm-shell-chrome">
          <PageHeader
            layout="brand"
            classNames={cmPageHeaderClassNames}
            labels={{ refresh: "Atualizar", refreshing: "Atualizando…" }}
            title={
              <CommercialTitleWithHelp title="Portal Comercial" hint={CM_HELP.shell.portal} />
            }
            subtitle="Carteira, pedidos, Meu dia e gestão."
            icon={<BriefcaseBusiness size={26} strokeWidth={1.75} aria-hidden="true" />}
            actions={
              scopeLabel ? (
                <div className="cm-shell-scope">
                  <CommercialScopeChipBar
                    label="Escopo"
                    chips={[{ id: "scope", label: scopeLabel, active: true }]}
                  />
                  <HelpTooltip content={CM_HELP.shell.scope} ariaLabel="Ajuda: Escopo" />
                </div>
              ) : null
            }
          />

          <CommercialUnderlineNav
            aria-label="Áreas do Portal Comercial"
            activeId={activeId}
            items={items.map((item) => ({
              id: item.id,
              label: item.label,
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
          />
        </div>

        {children}
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
