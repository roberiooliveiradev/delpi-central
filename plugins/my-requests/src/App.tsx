import type { ReactNode } from "react";

import { configureHttpClient } from "./api/httpClient";
import {
  resolveInternalRoute,
  useMyRequestsRouterPath,
} from "./hooks/useMyRequestsRouterPath";
import { AdminTypesPage } from "./pages/AdminTypesPage";
import { MinePage } from "./pages/MinePage";
import { NewRequestPage } from "./pages/NewRequestPage";
import { RequestDetailPage } from "./pages/RequestDetailPage";
import { WorkQueuePage } from "./pages/WorkQueuePage";
import { RequestsPermissionsProvider } from "./security/RequestsPermissionsContext";
import { buildAccessFromPermissions } from "./security/requestsAccess";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

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
        <p className="dashboard-my-requests__error">
          Você não possui permissão para abrir Minhas Solicitações.
        </p>
      </div>
    );
  }

  let page: ReactNode;
  switch (route.name) {
    case "work-queue":
      page = <WorkQueuePage />;
      break;
    case "new":
      page = <NewRequestPage />;
      break;
    case "detail":
      page = <RequestDetailPage requestId={route.requestId!} />;
      break;
    case "admin":
      page = <AdminTypesPage />;
      break;
    case "mine":
    case "home":
    default:
      page = <MinePage />;
      break;
  }

  return (
    <RequestsPermissionsProvider permissions={permissions} isSuperadmin={isSuperadmin}>
      {page}
    </RequestsPermissionsProvider>
  );
}
