import type { ReactNode } from "react";
import { ArrowLeft } from "lucide-react";

import { routeHref, type AppRoute } from "../utils/routing";

type PageShellProps = {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  backRoute?: AppRoute;
  /** Href absoluto/relativo quando a rota de volta precisa de query (ex.: listagem por CC). */
  backHref?: string;
  children: ReactNode;
};

export function PageShell({
  title,
  subtitle,
  icon,
  actions,
  backRoute,
  backHref,
  children,
}: PageShellProps) {
  const href = backHref ?? (backRoute ? routeHref(backRoute) : null);
  return (
    <div className="dashboard-planejamento-orcamentario dashboard-page po-app">
      <div className="po-page-stack">
        <header className="po-page-header">
          <div className="po-page-header__main">
            {href ? (
              <a className="po-back-link" href={href}>
                <ArrowLeft size={16} aria-hidden="true" />
                Voltar
              </a>
            ) : null}
            <div className="po-page-header__title-row">
              {icon ? <span className="po-page-header__icon">{icon}</span> : null}
              <div>
                <h1 className="po-page-header__title">{title}</h1>
                {subtitle ? <p className="po-page-header__subtitle">{subtitle}</p> : null}
              </div>
            </div>
          </div>
          {actions ? <div className="po-page-header__actions">{actions}</div> : null}
        </header>
        {children}
      </div>
    </div>
  );
}
