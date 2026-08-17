import type { ReactNode } from "react";
import { ArrowLeft } from "lucide-react";

import { routeHref, type AppRoute } from "../utils/routing";

type PageShellProps = {
  /** Mantido para acessibilidade (sr-only); não é exibido no header. */
  title: string;
  /** @deprecated Não exibido — conteúdo da página deve trazer o contexto. */
  subtitle?: string;
  /** @deprecated Não exibido no header. */
  icon?: ReactNode;
  actions?: ReactNode;
  backRoute?: AppRoute;
  /** Href absoluto/relativo quando a rota de volta precisa de query (ex.: listagem por CC). */
  backHref?: string;
  children: ReactNode;
};

const DELPI_LOGO_URL =
  typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : "/logoDelpi.svg";

export function PageShell({
  title,
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
            ) : (
              <span className="po-page-header__spacer" aria-hidden="true" />
            )}
            <h1 className="po-sr-only">{title}</h1>
          </div>
          <div className="po-page-header__end">
            {actions ? <div className="po-page-header__actions">{actions}</div> : null}
            <img
              className="po-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
