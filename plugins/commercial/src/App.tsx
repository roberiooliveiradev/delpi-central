import { useCallback, type ReactNode } from "react";
import { configureHttpClient } from "./api/httpClient";
import { CommercialConfirmDialogProvider } from "./app/CommercialConfirmDialogProvider";
import { CommercialFloatingNoticeProvider } from "./app/CommercialFloatingNoticeProvider";
import { CommercialRealtimeProvider, useCommercialPortfolioSync, useCommercialRealtimeNotices } from "./app/CommercialRealtimeProvider";
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
import { AnalyticsTeamRedirect } from "./features/analytics/AnalyticsTeamRedirect";
import { AnalyticsOpportunityDetailPage } from "./features/analytics/AnalyticsOpportunityDetailPage";
import { AnalyticsOpportunitiesPage } from "./features/analytics/AnalyticsOpportunitiesPage";
import { AnalyticsOtdLineDetailPage } from "./features/analytics/AnalyticsOtdLineDetailPage";
import { AnalyticsOtdPage } from "./features/analytics/AnalyticsOtdPage";
import { OverviewPage } from "./features/overview/OverviewPage";
import { HomePage } from "./features/home/HomePage";
import { MyDayPage } from "./features/my-day/MyDayPage";
import { OpenOrdersPage } from "./features/open-orders/OpenOrdersPage";
import { OpenOrderLineDetailPage } from "./features/open-orders/OpenOrderLineDetailPage";
import { OpenOrderOpDetailPage } from "./features/open-orders/OpenOrderOpDetailPage";
import { ProposalDetailPage } from "./features/proposals/ProposalDetailPage";
import { ProposalsPage } from "./features/proposals/ProposalsPage";
import { AdministrationHomePage } from "./features/administration/AdministrationHomePage";
import { AdministrationMembersPage } from "./features/administration/AdministrationMembersPage";
import { SellerPortfolioDetailPage } from "./features/seller-portfolios/SellerPortfolioDetailPage";
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
  const {
    isAdmin,
    canManagePortfolios,
    canViewWorklist,
    canViewAnalytics,
    canViewProposals,
    canAccessMyPortfolio,
    loading: scopeLoading,
    myPortfolios,
  } = usePortfolioScope();
  const showCustomers = scopeLoading || canAccessMyPortfolio;
  const scopeLabel =
    myPortfolios.length > 1
      ? `${myPortfolios.length} carteiras`
      : myPortfolios.length === 1
        ? `Carteira: ${myPortfolios[0]?.display_name ?? "—"}`
        : undefined;

  return (
    <PluginShell
      view={view}
      basePath={basePath}
      search={search}
      showAdmin={canManagePortfolios || isAdmin}
      showWorklist={canViewWorklist}
      showAnalytics={canViewAnalytics}
      showCustomers={showCustomers}
      scopeLabel={scopeLabel}
    >
      {view === "home" ? (
        <HomePage
          basePath={basePath}
          showAdmin={canManagePortfolios || isAdmin}
          showWorklist={canViewWorklist}
          showProposals={canViewProposals}
          showAnalytics={canViewAnalytics}
          showCustomers={canAccessMyPortfolio}
        />
      ) : null}
      {view === "overview" ? (
        canViewAnalytics ? (
          <OverviewPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "my_tasks" ? (
        canViewWorklist ? <MyDayPage basePath={basePath} /> : <NotFoundPage basePath={basePath} />
      ) : null}
      {view === "open_orders" ? <OpenOrdersPage basePath={basePath} /> : null}
      {view === "open_order_line_detail" &&
      route.orderBranch &&
      route.orderNumber &&
      route.lineItem ? (
        <OpenOrderLineDetailPage
          basePath={basePath}
          branch={route.orderBranch}
          orderNumber={route.orderNumber}
          lineItem={route.lineItem}
          search={search}
        />
      ) : null}
      {view === "open_order_op_detail" &&
      route.orderBranch &&
      route.orderNumber &&
      route.lineItem &&
      route.productionOrder ? (
        <OpenOrderOpDetailPage
          basePath={basePath}
          branch={route.orderBranch}
          orderNumber={route.orderNumber}
          lineItem={route.lineItem}
          productionOrder={route.productionOrder}
          search={search}
        />
      ) : null}
      {view === "customers" ? (
        scopeLoading || canAccessMyPortfolio ? (
          <CustomersPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "customer_detail" && route.codigo && route.loja ? (
        scopeLoading || canAccessMyPortfolio ? (
          <CustomerDetailPage
            codigo={route.codigo}
            loja={route.loja}
            basePath={basePath}
            search={search}
          />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "proposals" ? (
        canViewProposals ? (
          <ProposalsPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "proposal_detail" && route.propostaId ? (
        canViewProposals ? (
          <ProposalDetailPage basePath={basePath} propostaId={route.propostaId} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "analytics_otd" ? (
        canViewAnalytics ? (
          <AnalyticsOtdPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "analytics_otd_line" &&
      route.orderBranch &&
      route.orderNumber &&
      route.lineItem ? (
        canViewAnalytics ? (
          <AnalyticsOtdLineDetailPage
            basePath={basePath}
            branch={route.orderBranch}
            orderNumber={route.orderNumber}
            lineItem={route.lineItem}
          />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "analytics_team" ? <AnalyticsTeamRedirect basePath={basePath} /> : null}
      {view === "analytics_opportunities" ? (
        canViewAnalytics ? (
          <AnalyticsOpportunitiesPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "analytics_opportunity_detail" && route.proposalNumber ? (
        canViewAnalytics ? (
          <AnalyticsOpportunityDetailPage
            basePath={basePath}
            proposalNumber={route.proposalNumber}
            search={search}
          />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "administration" ? (
        canManagePortfolios || isAdmin ? (
          <AdministrationHomePage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "administration_portfolios" || view === "seller_portfolios" ? (
        canManagePortfolios || isAdmin ? (
          <SellerPortfoliosPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "administration_members" ? (
        canManagePortfolios || isAdmin ? (
          <AdministrationMembersPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "seller_portfolio_detail" && route.portfolioId ? (
        canManagePortfolios || isAdmin ? (
          <SellerPortfolioDetailPage
            basePath={basePath}
            portfolioId={route.portfolioId}
            search={search}
          />
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
  const { canViewWorklist, isAdmin, myPortfolios } = usePortfolioScope();
  // WS: worklist.view OU quem tem carteira (accounts.view) / manage — alinhado à API.
  const realtimeEnabled = canViewWorklist || isAdmin || myPortfolios.length > 0;
  return (
    <CommercialRealtimeProvider getAccessToken={getAccessToken} enabled={realtimeEnabled}>
      <CommercialRealtimeNoticesBridge enabled={realtimeEnabled} />
      <PortfolioScopeRealtimeSyncBridge />
      {children}
    </CommercialRealtimeProvider>
  );
}

function CommercialRealtimeNoticesBridge({ enabled }: { enabled: boolean }) {
  useCommercialRealtimeNotices(enabled);
  return null;
}

/** Mantém `sellers` / membership frescos após CRUD de carteiras (WS + escopo). */
function PortfolioScopeRealtimeSyncBridge() {
  const { reloadScope } = usePortfolioScope();
  useCommercialPortfolioSync(() => {
    reloadScope();
  });
  return null;
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
        <CommercialConfirmDialogProvider>
          <RealtimeShell getAccessToken={tokenGetter}>
            <HomeHeroMetricsProvider>
              <AppRoutes
                basePath={basePath}
                search={search}
                pathnameFromHost={pathnameFromHost}
              />
            </HomeHeroMetricsProvider>
          </RealtimeShell>
        </CommercialConfirmDialogProvider>
      </CommercialFloatingNoticeProvider>
    </PortfolioScopeProvider>
  );
}
