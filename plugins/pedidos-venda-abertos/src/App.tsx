import { configureHttpClient } from "./api/httpClient";
import { NotFoundPage } from "./app/NotFoundPage";
import { PluginShell } from "./app/PluginShell";
import { PortfolioScopeProvider } from "./app/PortfolioScopeContext";
import { usePortfolioScope } from "./app/usePortfolioScope";
import {
  normalizeBasePath,
  PVA_BASE_PATH,
  resolvePluginRoute,
} from "./app/pluginRoutes";
import { usePluginRouterPath } from "./app/usePluginRouterPath";
import { CustomerDetailPage } from "./features/customers/pages/CustomerDetailPage";
import { CustomersPage } from "./features/customers/pages/CustomersPage";
import { SellerConfigPage } from "./features/customers/pages/SellerConfigPage";
import { PedidosVendaAbertosPage } from "./pages/PedidosVendaAbertosPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  basePath?: string;
  search?: string;
};

function AppRoutes({
  basePath,
  search,
  pathnameFromHost,
}: {
  basePath: string;
  search?: string;
  pathnameFromHost?: string;
}) {
  const pathname = usePluginRouterPath(pathnameFromHost, basePath);
  const route = resolvePluginRoute(pathname, basePath);
  const { view } = route;
  const { isAdmin } = usePortfolioScope();

  return (
    <PluginShell view={view} basePath={basePath} search={search} showConfig={isAdmin}>
      {view === "orders" ? <PedidosVendaAbertosPage /> : null}
      {view === "customers" ? <CustomersPage basePath={basePath} /> : null}
      {view === "config" ? <SellerConfigPage basePath={basePath} /> : null}
      {view === "customer_detail" && route.codigo && route.loja ? (
        <CustomerDetailPage
          codigo={route.codigo}
          loja={route.loja}
          basePath={basePath}
          search={search}
        />
      ) : null}
      {view === "not_found" ? <NotFoundPage basePath={basePath} /> : null}
    </PluginShell>
  );
}

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  basePath: basePathFromHost,
  search,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const basePath = normalizeBasePath(basePathFromHost ?? PVA_BASE_PATH);

  return (
    <PortfolioScopeProvider>
      <AppRoutes
        basePath={basePath}
        search={search}
        pathnameFromHost={pathnameFromHost}
      />
    </PortfolioScopeProvider>
  );
}
