import { configureHttpClient } from "./api/httpClient";
import { useMyRequestsRouterPath } from "./hooks/useMyRequestsRouterPath";
import { ShellHomePage } from "./pages/ShellHomePage";
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
  useMyRequestsRouterPath(pathnameFromHost, searchFromHost);
  const access = buildAccessFromPermissions(permissions, isSuperadmin);

  if (!access.canAccess) {
    return (
      <div className="dashboard-my-requests dashboard-page">
        <p className="dashboard-my-requests__error">
          Você não possui permissão para abrir Minhas Solicitações.
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard-my-requests dashboard-page">
      <ShellHomePage canCreate={access.canCreateInvoiceIssuance || access.canManage} />
    </div>
  );
}
