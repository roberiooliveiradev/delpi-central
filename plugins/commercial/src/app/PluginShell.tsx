import type { ReactNode } from "react";
import { BriefcaseBusiness, CalendarCheck, ClipboardList, Settings, Users } from "lucide-react";
import { ActionButton, PageHeader } from "@delpi/plugin-ui/index";

import {
  isPluginNavActive,
  type PluginView,
} from "./pluginRoutes";
import { navigatePluginView } from "./pluginNavigation";
import {
  cmPageHeaderClassNames,
  CommercialScopeChipBar,
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
          title="Portal Comercial"
          subtitle="Carteira, pedidos, Meu dia e gestão comercial."
          icon={<BriefcaseBusiness size={28} strokeWidth={1.75} aria-hidden="true" />}
        />

        {scopeLabel ? (
          <CommercialScopeChipBar
            label="Escopo"
            chips={[{ id: "scope", label: scopeLabel, active: true }]}
          />
        ) : null}

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
