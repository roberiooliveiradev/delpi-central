import { configureHttpClient } from "./api/httpClient";
import { useTravelAccess } from "./hooks/useTravelAccess";
import { parseTravelRoute, useTravelRouterPath } from "./hooks/useTravelRouterPath";
import { HubPage } from "./pages/HubPage";
import { ListPage } from "./pages/ListPage";
import { NewReportPage } from "./pages/NewReportPage";
import { PackagePage } from "./pages/PackagePage";
import { WorkspacePage } from "./pages/WorkspacePage";
import { TravelStateBanner } from "./ui/travelUi";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  permissions,
  isSuperadmin,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const { pathname, search } = useTravelRouterPath(pathnameFromHost);
  const route = parseTravelRoute(pathname, search);
  const { access, loading, error } = useTravelAccess(getAccessToken, {
    permissions,
    isSuperadmin,
  });

  if (loading) {
    return (
      <div className="dashboard-travel-expenses dashboard-page">
        <TravelStateBanner>Carregando permissões…</TravelStateBanner>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-travel-expenses dashboard-page">
        <TravelStateBanner variant="error">{error}</TravelStateBanner>
      </div>
    );
  }

  if (!access?.canView) {
    return (
      <div className="dashboard-travel-expenses dashboard-page">
        <TravelStateBanner variant="error">
          Você não tem permissão para abrir Despesas de Viagem.
        </TravelStateBanner>
      </div>
    );
  }

  return (
    <div className="dashboard-travel-expenses dashboard-page">
      {route.kind === "hub" ? <HubPage access={access} /> : null}
      {route.kind === "list" ? <ListPage access={access} search={search} /> : null}
      {route.kind === "new" ? <NewReportPage access={access} /> : null}
      {route.kind === "detail" ? <WorkspacePage reportId={route.reportId} access={access} /> : null}
      {route.kind === "package" ? <PackagePage reportId={route.reportId} /> : null}
      {route.kind === "unknown" ? (
        <TravelStateBanner variant="error">Rota não encontrada neste plugin.</TravelStateBanner>
      ) : null}
    </div>
  );
}
