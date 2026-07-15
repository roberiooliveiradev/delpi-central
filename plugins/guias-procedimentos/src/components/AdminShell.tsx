import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";

import { ModuleHeader } from "./ModuleHeader";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

type AdminShellProps = {
  title: string;
  standalone?: boolean;
  children: ReactNode;
  actions?: ReactNode;
  backTo?: string;
  backLabel?: string;
};

export function AdminShell({
  title,
  standalone = false,
  children,
  actions = null,
  backTo = GUIAS_PROCEDIMENTOS_ROUTES.home,
  backLabel = "Voltar ao módulo",
}: AdminShellProps) {
  return (
    <div className="dashboard-guias-procedimentos gp-page gp-page--admin">
      <div className="gp-shell gp-shell--admin">
        <ModuleHeader
          title={title}
          showThemeToggle={standalone}
          actions={actions}
        />
        <nav className="gp-back" aria-label="Navegação administrativa">
          <button
            type="button"
            className="gp-btn gp-btn--ghost"
            onClick={() => navigateGuiasProcedimentos(backTo)}
          >
            <ArrowLeft size={16} strokeWidth={2} aria-hidden="true" />
            {backLabel}
          </button>
        </nav>
        {children}
      </div>
    </div>
  );
}
