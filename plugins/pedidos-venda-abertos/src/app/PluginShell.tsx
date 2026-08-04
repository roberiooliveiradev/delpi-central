import type { ReactNode } from "react";
import { BriefcaseBusiness } from "lucide-react";

import { PluginNav } from "./PluginNav.tsx";
import type { PluginView } from "./pluginRoutes.ts";

type PluginShellProps = {
  view: PluginView;
  basePath: string;
  search?: string;
  children: ReactNode;
  updatedLabel?: string;
  onRefresh?: () => void;
  refreshing?: boolean;
  showConfig?: boolean;
};

export function PluginShell({
  view,
  basePath,
  search,
  children,
  updatedLabel,
  onRefresh,
  refreshing = false,
  showConfig = false,
}: PluginShellProps) {
  return (
    <div className="dashboard-pedidos-venda-abertos dashboard-page">
      <div className="pva-app-shell">
        <header className="pva-module-chrome">
          <div className="pva-module-chrome__top">
            <div className="pva-module-chrome__brand">
              <span className="pva-module-chrome__icon" aria-hidden="true">
                <BriefcaseBusiness size={26} strokeWidth={1.75} />
              </span>
              <div>
                <p className="pva-module-chrome__eyebrow">DELPI · Comercial</p>
                <h1 className="pva-module-chrome__title">Portal do Vendedor</h1>
                <p className="pva-module-chrome__subtitle">
                  Acompanhe sua carteira de clientes e pedidos em aberto.
                </p>
                {updatedLabel ? (
                  <p className="pva-module-chrome__meta" aria-live="polite">
                    {updatedLabel}
                    {refreshing ? " · Atualizando…" : ""}
                  </p>
                ) : null}
              </div>
            </div>
            {onRefresh ? (
              <button
                type="button"
                className="pva-btn pva-btn--on-dark"
                onClick={onRefresh}
                disabled={refreshing}
                aria-busy={refreshing}
              >
                {refreshing ? "Atualizando…" : "Atualizar"}
              </button>
            ) : null}
          </div>
          <PluginNav
            view={view}
            basePath={basePath}
            search={search}
            showConfig={showConfig}
          />
        </header>
        {children}
      </div>
    </div>
  );
}
