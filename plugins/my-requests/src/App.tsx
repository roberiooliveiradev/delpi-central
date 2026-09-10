import type { ReactNode } from "react";

import { MyRequestsFloatingNoticeProvider } from "./app/MyRequestsFloatingNoticeProvider";
import { MyRequestsRealtimeProvider } from "./app/MyRequestsRealtimeProvider";
import { configureHttpClient } from "./api/httpClient";
import { AppShell } from "./components/AppShell";
import {
  resolveInternalRoute,
  useMyRequestsRouterPath,
} from "./hooks/useMyRequestsRouterPath";
import { AdminTypesPage } from "./pages/AdminTypesPage";
import { MinePage } from "./pages/MinePage";
import { NewRequestPage } from "./pages/NewRequestPage";
import { RequestDetailPage } from "./pages/RequestDetailPage";
import { RequestEditPage } from "./pages/RequestEditPage";
import { WorkQueuePage } from "./pages/WorkQueuePage";
import { RequestsPermissionsProvider } from "./security/RequestsPermissionsContext";
import {
  buildAccessFromPermissions,
  canAccessWorkQueue,
  canCreateAnyRequest,
} from "./security/requestsAccess";
import { MyRequestsStateBanner } from "./ui/mrUi";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

function ForbiddenRoute({ title, message }: { title: string; message: string }) {
  return (
    <AppShell title={title}>
      <MyRequestsStateBanner variant="error">{message}</MyRequestsStateBanner>
    </AppShell>
  );
}

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  search: searchFromHost,
  permissions,
  isSuperadmin = false,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const { pathname } = useMyRequestsRouterPath(pathnameFromHost, searchFromHost);
  const access = buildAccessFromPermissions(permissions, isSuperadmin);
  const route = resolveInternalRoute(pathname);

  if (!access.canAccess) {
    return (
      <div className="dashboard-my-requests dashboard-page">
        <MyRequestsStateBanner variant="error">
          Você não tem permissão para abrir Minhas Solicitações. Peça acesso ao
          administrador do portal.
        </MyRequestsStateBanner>
      </div>
    );
  }

  let page: ReactNode;
  switch (route.name) {
    case "work-queue":
      page = canAccessWorkQueue(access) ? (
        <WorkQueuePage />
      ) : (
        <ForbiddenRoute
          title="Fila de trabalho"
          message="Você não tem permissão para atender a fila de trabalho. É necessário processar ao menos um tipo de solicitação (ou visão ampla / administração)."
        />
      );
      break;
    case "new":
      page = canCreateAnyRequest(access) ? (
        <NewRequestPage />
      ) : (
        <ForbiddenRoute
          title="Nova solicitação"
          message="Você não tem permissão para criar solicitações. Peça ao administrador a permissão de criação do tipo desejado."
        />
      );
      break;
    case "detail":
      page = <RequestDetailPage requestId={route.requestId!} />;
      break;
    case "edit":
      page = <RequestEditPage requestId={route.requestId!} />;
      break;
    case "admin":
      page = access.canManage ? (
        <AdminTypesPage />
      ) : (
        <ForbiddenRoute
          title="Administração"
          message="Você não tem permissão para administrar tipos de solicitação."
        />
      );
      break;
    case "mine":
    case "home":
    default:
      page = <MinePage />;
      break;
  }

  return (
    <RequestsPermissionsProvider permissions={permissions} isSuperadmin={isSuperadmin}>
      <MyRequestsFloatingNoticeProvider>
        <MyRequestsRealtimeProvider getAccessToken={getAccessToken} enabled>
          {page}
        </MyRequestsRealtimeProvider>
      </MyRequestsFloatingNoticeProvider>
    </RequestsPermissionsProvider>
  );
}
