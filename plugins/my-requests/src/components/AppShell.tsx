import type { ReactNode } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { MyRequestsFormActions, MyRequestsPageHeader } from "../ui/mrUi";

type AppShellProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  canCreate?: boolean;
};

export function AppShell({ title, subtitle, children, canCreate = false }: AppShellProps) {
  const access = useRequestsPermissions();
  const canManage = access.canManage;

  return (
    <div className="dashboard-my-requests dashboard-page">
      <MyRequestsPageHeader title={title} subtitle={subtitle} />
      <nav aria-label="Navegação do módulo" data-help="shell-nav">
        <MyRequestsFormActions>
          <ActionButton
            href="/apps/my-requests/mine"
            title={MY_REQUESTS_HELP_TOOLTIPS.shell.nav}
            variant="ghost"
          >
            Minhas
          </ActionButton>
          <ActionButton
            href="/apps/my-requests/work-queue"
            title={MY_REQUESTS_HELP_TOOLTIPS.workQueue.section}
            variant="ghost"
          >
            Fila
          </ActionButton>
          {canCreate ? (
            <ActionButton
              href="/apps/my-requests/new"
              title={MY_REQUESTS_HELP_TOOLTIPS.new.section}
              variant="primary"
            >
              Nova
            </ActionButton>
          ) : null}
          {canManage ? (
            <ActionButton
              href="/apps/my-requests/admin"
              title={MY_REQUESTS_HELP_TOOLTIPS.admin.section}
              variant="ghost"
            >
              Admin
            </ActionButton>
          ) : null}
        </MyRequestsFormActions>
      </nav>
      <div className="my-requests-page-stack">{children}</div>
    </div>
  );
}
