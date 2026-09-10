import type { ReactNode } from "react";
import { ClipboardList, ListChecks, PlusCircle, Settings } from "lucide-react";

import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { resolveTopBarActiveId } from "../hooks/resolveTopBarActiveId";
import { useMyRequestsRouterPath } from "../hooks/useMyRequestsRouterPath";
import {
  canAccessWorkQueue,
  canCreateAnyRequest,
} from "../security/requestsAccess";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { MR_PORTAL_SCOPE, MyRequestsPageHeader, MyRequestsTopBar } from "../ui/mrUi";

type AppShellProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function AppShell({ title, subtitle, children }: AppShellProps) {
  const access = useRequestsPermissions();
  const { pathname } = useMyRequestsRouterPath();
  const activeId = resolveTopBarActiveId(pathname);
  const showCreate = canCreateAnyRequest(access);
  const showWorkQueue = canAccessWorkQueue(access);
  const canManage = access.canManage;

  const items = [
    {
      id: "mine",
      label: "Minhas solicitações",
      icon: <ClipboardList size={18} aria-hidden />,
      onSelect: () => navigateMyRequestsPath(myRequestsPath("mine")),
    },
    ...(showWorkQueue
      ? [
          {
            id: "work_queue",
            label: "Fila de trabalho",
            icon: <ListChecks size={18} aria-hidden />,
            onSelect: () => navigateMyRequestsPath(myRequestsPath("work-queue")),
          },
        ]
      : []),
    ...(showCreate
      ? [
          {
            id: "new",
            label: "Nova solicitação",
            icon: <PlusCircle size={18} aria-hidden />,
            onSelect: () => navigateMyRequestsPath(myRequestsPath("new")),
          },
        ]
      : []),
    ...(canManage
      ? [
          {
            id: "admin",
            label: "Administração",
            icon: <Settings size={18} aria-hidden />,
            onSelect: () => navigateMyRequestsPath(myRequestsPath("admin")),
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
      <div className="my-requests-content-column">
        <MyRequestsPageHeader title={title} subtitle={subtitle} />
        <div className="my-requests-page-stack">{children}</div>
      </div>
    </div>
  );
}
