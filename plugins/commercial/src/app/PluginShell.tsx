import type { ReactNode } from "react";
import { BriefcaseBusiness, ClipboardList, Settings, Users } from "lucide-react";
import { ActionButton, PageHeader } from "@delpi/plugin-ui/index";

import {
  isPluginNavActive,
  type PluginView,
} from "./pluginRoutes";
import { navigatePluginView } from "./pluginNavigation";
import { cmPageHeaderClassNames } from "./commercialUi";

type PluginShellProps = {
  view: PluginView;
  basePath: string;
  search?: string;
  showAdmin?: boolean;
  children: ReactNode;
};

const NAV_ITEMS: Array<{
  id: Exclude<PluginView, "customer_detail" | "not_found">;
  label: string;
}> = [
  { id: "home", label: "Início" },
  { id: "open_orders", label: "Pedidos em aberto" },
  { id: "customers", label: "Minha carteira" },
];

export function PluginShell({
  view,
  basePath,
  search,
  showAdmin = false,
  children,
}: PluginShellProps) {
  const items = showAdmin
    ? [...NAV_ITEMS, { id: "seller_portfolios" as const, label: "Carteiras" }]
    : NAV_ITEMS;

  return (
    <div className="dashboard-commercial dashboard-pedidos-venda-abertos dashboard-page">
      <div className="cm-page-stack">
        <PageHeader
          layout="brand"
          classNames={cmPageHeaderClassNames}
          labels={{ refresh: "Atualizar", refreshing: "Atualizando…" }}
          title="Portal Comercial"
          subtitle="Carteira de clientes, pedidos em aberto e gestão comercial."
          icon={<BriefcaseBusiness size={28} strokeWidth={1.75} aria-hidden="true" />}
        />

        <nav className="cm-nav-row" aria-label="Áreas do Portal Comercial">
          {items.map((item) => {
            const active = isPluginNavActive(view, item.id);
            return (
              <ActionButton
                key={item.id}
                variant={active ? "primary" : "ghost"}
                aria-label={item.label}
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
  target: "orders" | "customers" | "admin";
}) {
  if (target === "orders") {
    return <ClipboardList size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  if (target === "customers") {
    return <Users size={22} strokeWidth={1.75} aria-hidden="true" />;
  }
  return <Settings size={22} strokeWidth={1.75} aria-hidden="true" />;
}
