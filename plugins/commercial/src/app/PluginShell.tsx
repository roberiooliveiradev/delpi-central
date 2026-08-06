import type { ReactNode } from "react";
import { BriefcaseBusiness, CalendarCheck, ClipboardList, Settings, Users } from "lucide-react";
import { ActionButton, HelpTooltip, PageHeader } from "@delpi/plugin-ui/index";

import { CM_HELP } from "../content/helpTooltips";
import {
  isPluginNavActive,
  type PluginView,
} from "./pluginRoutes";
import { navigatePluginView } from "./pluginNavigation";
import {
  cmPageHeaderClassNames,
  CommercialScopeChipBar,
  CommercialTitleWithHelp,
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

export function PluginShell({
  view,
  basePath,
  search,
  showAdmin = false,
  showWorklist = false,
  scopeLabel,
  children,
}: PluginShellProps) {
  const items: Array<{ id: NavId; label: string }> = [
    { id: "home", label: "Início" },
    ...(showWorklist ? [{ id: "my_day" as const, label: "Meu dia" }] : []),
    { id: "open_orders", label: "Pedidos em aberto" },
    { id: "customers", label: "Minha carteira" },
    ...(showAdmin ? [{ id: "seller_portfolios" as const, label: "Carteiras" }] : []),
  ];

  return (
    <div className="dashboard-commercial dashboard-pedidos-venda-abertos dashboard-page">
      <div className="cm-page-stack">
        <PageHeader
          layout="brand"
          classNames={cmPageHeaderClassNames}
          labels={{ refresh: "Atualizar", refreshing: "Atualizando…" }}
          title={
            <CommercialTitleWithHelp title="Portal Comercial" hint={CM_HELP.shell.portal} />
          }
          subtitle="Carteira, pedidos, Meu dia e gestão comercial."
          icon={<BriefcaseBusiness size={28} strokeWidth={1.75} aria-hidden="true" />}
        />

        {scopeLabel ? (
          <div className="cm-nav-row" style={{ alignItems: "center", gap: 8 }}>
            <CommercialScopeChipBar
              label="Escopo"
              chips={[{ id: "scope", label: scopeLabel, active: true }]}
            />
            <HelpTooltip content={CM_HELP.shell.scope} ariaLabel="Ajuda: Escopo" />
          </div>
        ) : null}

        <nav className="cm-nav-row" aria-label="Áreas do Portal Comercial">
          {items.map((item) => {
            const active = isPluginNavActive(view, item.id);
            return (
              <ActionButton
                key={item.id}
                variant={active ? "primary" : "ghost"}
                aria-label={
                  NAV_HELP[item.id] ? `${item.label}. ${NAV_HELP[item.id]}` : item.label
                }
                onClick={() =>
                  navigatePluginView(item.id, {
                    basePath,
                    search: search || undefined,
                  })
                }
              >
                {item.label}
              </ActionButton>
            );
          })}
        </nav>

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
