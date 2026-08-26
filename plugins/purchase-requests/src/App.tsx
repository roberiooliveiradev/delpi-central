import { configureHttpClient } from "./api/httpClient";
import { usePurchaseRequestsRouterPath } from "./hooks/usePurchaseRequestsRouterPath";
import { PurchaseRequestsPage } from "./pages/PurchaseRequestsPage";
import { buildAccessFromPermissions } from "./security/purchaseRequestsAccess";
import { PurchaseRequestsStateBanner } from "./ui/purchaseRequestsUi";

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
  const { pathname, search } = usePurchaseRequestsRouterPath(
    pathnameFromHost,
    searchFromHost,
  );
  const access = buildAccessFromPermissions(permissions, isSuperadmin);

  if (!access.canView) {
    return (
      <div className="dashboard-purchase-requests dashboard-page">
        <PurchaseRequestsStateBanner variant="error">
          Você não possui permissão para abrir Solicitações de Compras.
        </PurchaseRequestsStateBanner>
      </div>
    );
  }

  if (access.branches.length === 0) {
    return (
      <div className="dashboard-purchase-requests dashboard-page">
        <PurchaseRequestsStateBanner variant="error">
          Você não possui acesso a nenhuma filial neste módulo.
        </PurchaseRequestsStateBanner>
      </div>
    );
  }

  return <PurchaseRequestsPage access={access} pathname={pathname} search={search} />;
}
