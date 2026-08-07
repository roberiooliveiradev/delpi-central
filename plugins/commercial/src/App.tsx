import { useCallback, type ReactNode } from "react";
import { configureHttpClient } from "./api/httpClient";
import { CommercialConfirmDialogProvider } from "./app/CommercialConfirmDialogProvider";
import { CommercialFloatingNoticeProvider } from "./app/CommercialFloatingNoticeProvider";
import { CommercialRealtimeProvider, useCommercialRealtimeNotices } from "./app/CommercialRealtimeProvider";
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
import { GestaoEquipePage } from "./features/gestao/GestaoEquipePage";
import { GestaoOportunidadeDetailPage } from "./features/gestao/GestaoOportunidadeDetailPage";
import { GestaoOportunidadesPage } from "./features/gestao/GestaoOportunidadesPage";
import { GestaoOtdLineDetailPage } from "./features/gestao/GestaoOtdLineDetailPage";
import { GestaoOtdPage } from "./features/gestao/GestaoOtdPage";
import { GestaoPage } from "./features/gestao/GestaoPage";
import { HomePage } from "./features/home/HomePage";
import { MyDayPage } from "./features/my-day/MyDayPage";
import { OpenOrdersPage } from "./features/open-orders/OpenOrdersPage";
import { PropostaDetailPage } from "./features/propostas/PropostaDetailPage";
import { PropostasPage } from "./features/propostas/PropostasPage";
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
    canViewWorklist,
    canViewAnalytics,
    canViewPropostas,
    canUseTeamScope,
    myPortfolio,
  } = usePortfolioScope();
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
      showPropostas={canViewPropostas}
      showAnalytics={canViewAnalytics}
      scopeLabel={scopeLabel}
    >
      {view === "home" ? (
        <HomePage
          basePath={basePath}
          showAdmin={isAdmin}
          showWorklist={canViewWorklist}
          showPropostas={canViewPropostas}
          showAnalytics={canViewAnalytics}
        />
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
      {view === "propostas" ? (
        canViewPropostas ? (
          <PropostasPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "proposta_detail" && route.propostaId ? (
        canViewPropostas ? (
          <PropostaDetailPage basePath={basePath} propostaId={route.propostaId} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "gestao" ? (
        canViewAnalytics ? (
          <GestaoPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "gestao_otd" ? (
        canViewAnalytics ? (
          <GestaoOtdPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "gestao_otd_line" &&
      route.orderBranch &&
      route.orderNumber &&
      route.lineItem ? (
        canViewAnalytics ? (
          <GestaoOtdLineDetailPage
            basePath={basePath}
            branch={route.orderBranch}
            orderNumber={route.orderNumber}
            lineItem={route.lineItem}
          />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "gestao_equipe" ? (
        canViewAnalytics && canUseTeamScope ? (
          <GestaoEquipePage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "gestao_oportunidades" ? (
        canViewAnalytics ? (
          <GestaoOportunidadesPage basePath={basePath} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
      ) : null}
      {view === "gestao_oportunidade_detail" && route.proposalNumber ? (
        canViewAnalytics ? (
          <GestaoOportunidadeDetailPage
            basePath={basePath}
            proposalNumber={route.proposalNumber}
            search={search}
          />
        ) : (
          <NotFoundPage basePath={basePath} />
        )
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
      <CommercialRealtimeNoticesBridge enabled={canViewWorklist} />
      {children}
    </CommercialRealtimeProvider>
  );
}

function CommercialRealtimeNoticesBridge({ enabled }: { enabled: boolean }) {
  useCommercialRealtimeNotices(enabled);
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
