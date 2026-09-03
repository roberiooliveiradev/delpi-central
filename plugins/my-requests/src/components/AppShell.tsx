import type { ReactNode } from "react";

type AppShellProps = {
  title: string;
  children: ReactNode;
  canCreate?: boolean;
};

export function AppShell({ title, children, canCreate = false }: AppShellProps) {
  return (
    <div className="dashboard-my-requests dashboard-page">
      <header className="dashboard-my-requests__header" data-help="shell-nav">
        <div>
          <h1>{title}</h1>
        </div>
        <nav className="dashboard-my-requests__nav" aria-label="Navegação do módulo">
          <a href="/apps/my-requests/mine">Minhas</a>
          <a href="/apps/my-requests/work-queue">Fila</a>
          {canCreate ? <a href="/apps/my-requests/new">Nova</a> : null}
        </nav>
      </header>
      {children}
    </div>
  );
}
