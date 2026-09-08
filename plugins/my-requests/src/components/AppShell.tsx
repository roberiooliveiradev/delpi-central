import type { ReactNode } from "react";
import { ClipboardList, ListChecks, PlusCircle, Settings } from "lucide-react";

import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { resolveTopBarActiveId } from "../hooks/resolveTopBarActiveId";
import { useMyRequestsRouterPath } from "../hooks/useMyRequestsRouterPath";
import { canCreateAnyRequest } from "../security/requestsAccess";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { MR_PORTAL_SCOPE, MyRequestsPageHeader, MyRequestsTopBar } from "../ui/mrUi";

type AppShellProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  canCreate?: boolean;
};

function navigate(href: string) {
  window.location.assign(href);
}

export function AppShell({ title, subtitle, children, canCreate = false }: AppShellProps) {
  const access = useRequestsPermissions();
  const { pathname } = useMyRequestsRouterPath();
  const activeId = resolveTopBarActiveId(pathname);
  const showCreate = canCreate || canCreateAnyRequest(access);
  const canManage = access.canManage;

  const items = [
    {
      id: "mine",
      label: "Minhas solicitações",
      icon: <ClipboardList size={18} aria-hidden />,
      title: `Minhas solicitações. ${MY_REQUESTS_HELP_TOOLTIPS.mine.section}`,
      onSelect: () => navigate("/apps/my-requests/mine"),
    },
    {
      id: "work_queue",
      label: "Fila de trabalho",
      icon: <ListChecks size={18} aria-hidden />,
      title: `Fila de trabalho. ${MY_REQUESTS_HELP_TOOLTIPS.workQueue.section}`,
      onSelect: () => navigate("/apps/my-requests/work-queue"),
    },
    ...(showCreate
      ? [
          {
            id: "new",
            label: "Nova solicitação",
            icon: <PlusCircle size={18} aria-hidden />,
            title: `Nova solicitação. ${MY_REQUESTS_HELP_TOOLTIPS.new.section}`,
            onSelect: () => navigate("/apps/my-requests/new"),
          },
        ]
      : []),
    ...(canManage
      ? [
          {
            id: "admin",
            label: "Administração",
            icon: <Settings size={18} aria-hidden />,
            title: `Administração. ${MY_REQUESTS_HELP_TOOLTIPS.admin.section}`,
            onSelect: () => navigate("/apps/my-requests/admin"),
          },
        ]
      : []),
  ];

  return (
    <div className="dashboard-my-requests dashboard-page">
      <MyRequestsTopBar
        aria-label="Navegação do módulo Minhas Solicitações"
        activeId={activeId}
        collapsible
        collapseMode="hamburger"
        collapseTrigger="overflow"
        menuLabel="Menu Minhas Solicitações"
        portalScopeClassName={MR_PORTAL_SCOPE}
        items={items}
      />
      <MyRequestsPageHeader title={title} subtitle={subtitle} />
      <div className="my-requests-page-stack">{children}</div>
    </div>
  );
}
