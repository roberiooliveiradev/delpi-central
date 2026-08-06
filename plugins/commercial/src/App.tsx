import { useCallback, type ReactNode } from "react";
import { configureHttpClient } from "./api/httpClient";
import { CommercialFloatingNoticeProvider } from "./app/CommercialFloatingNoticeProvider";
import { CommercialRealtimeProvider } from "./app/CommercialRealtimeProvider";
import { HomeHeroMetricsProvider } from "./app/HomeHeroMetricsContext";
import { NotFoundPage } from "./app/NotFoundPage";
import { PluginShell } from "./app/PluginShell";
import { PortfolioScopeProvider, usePortfolioScope } from "./app/PortfolioScopeContext";
import {
  COMMERCIAL_BASE_PATH,
  normalizeBasePath,
  resolvePluginRoute,
} from "./app/pluginRoutes";
import { usePluginRouterPath } from "./app/usePluginRouterPath";
import { CustomerDetailPage } from "./features/customers/CustomerDetailPage";
import { CustomersPage } from "./features/customers/CustomersPage";
import { HomePage } from "./features/home/HomePage";
import { MyDayPage } from "./features/my-day/MyDayPage";
import { OpenOrdersPage } from "./features/open-orders/OpenOrdersPage";
import { SellerPortfoliosPage } from "./features/seller-portfolios/SellerPortfoliosPage";

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
  const { isAdmin, canViewWorklist, myPortfolio } = usePortfolioScope();
  const scopeLabel = myPortfolio?.display_name
    ? `Carteira: ${myPortfolio.display_name}`
    : undefined;

  return (
    <PluginShell
      view={view}
      basePath={basePath}
      search={search}
      showAdmin={isAdmin}
      showWorklist={canViewWorklist}
      scopeLabel={scopeLabel}
    >
      {view === "home" ? (
        <HomePage basePath={basePath} showAdmin={isAdmin} showWorklist={canViewWorklist} />
      ) : null}
      {view === "my_day" ? (
        canViewWorklist ? <MyDayPage basePath={basePath} /> : <NotFoundPage basePath={basePath} />
      ) : null}
      {view === "open_orders" ? <OpenOrdersPage /> : null}
      {view === "customers" ? <CustomersPage basePath={basePath} /> : null}
      {view === "customer_detail" && route.codigo && route.loja ? (
        <CustomerDetailPage
          codigo={route.codigo}
          loja={route.loja}
          basePath={basePath}
          search={search}
        />
      ) : null}
      {view === "seller_portfolios" ? (
        isAdmin ? (
          <SellerPortfoliosPage />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "not_found" ? <NotFoundPage basePath={basePath} /> : null}
    </PluginShell>
  );
}

function RealtimeShell({
  getAccessToken,
  children,
}: {
  getAccessToken: () => string | undefined;
  children: ReactNode;
}) {
  const { canViewWorklist } = usePortfolioScope();
  return (
    <CommercialRealtimeProvider getAccessToken={getAccessToken} enabled={canViewWorklist}>
      {children}
    </CommercialRealtimeProvider>
  );
}

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  basePath: basePathFromHost,
  search,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const basePath = normalizeBasePath(basePathFromHost ?? COMMERCIAL_BASE_PATH);
  const tokenGetter = useCallback(() => getAccessToken?.(), [getAccessToken]);

  return (
    <PortfolioScopeProvider>
      <CommercialFloatingNoticeProvider>
        <RealtimeShell getAccessToken={tokenGetter}>
          <HomeHeroMetricsProvider>
            <AppRoutes
              basePath={basePath}
              search={search}
              pathnameFromHost={pathnameFromHost}
            />
          </HomeHeroMetricsProvider>
        </RealtimeShell>
      </CommercialFloatingNoticeProvider>
    </PortfolioScopeProvider>
  );
}
