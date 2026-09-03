import type { ReactNode } from "react";

import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";

type AppShellProps = {
  title: string;
  children: ReactNode;
  canCreate?: boolean;
};

export function AppShell({ title, children, canCreate = false }: AppShellProps) {
  return (
    <div className="dashboard-my-requests dashboard-page">
      <header
        className="dashboard-my-requests__header"
        data-help="shell-nav"
        title={MY_REQUESTS_HELP_TOOLTIPS.shell.nav}
      >
        <div>
          <h1>{title}</h1>
        </div>
        <nav className="dashboard-my-requests__nav" aria-label="Navegação do módulo">
          <a href="/apps/my-requests/mine" title={MY_REQUESTS_HELP_TOOLTIPS.mine.section}>
            Minhas
          </a>
          <a
            href="/apps/my-requests/work-queue"
            title={MY_REQUESTS_HELP_TOOLTIPS.workQueue.section}
          >
            Fila
          </a>
          {canCreate ? (
            <a href="/apps/my-requests/new" title={MY_REQUESTS_HELP_TOOLTIPS.new.section}>
              Nova
            </a>
          ) : null}
        </nav>
      </header>
      {children}
    </div>
  );
}
