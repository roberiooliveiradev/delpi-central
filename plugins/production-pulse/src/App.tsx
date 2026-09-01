import { configureHttpClient } from "./api/httpClient";
import { resolveProductionPulsePermissions } from "./constants/permissions";
import { parseProductionPulseRoute } from "./constants/routes";
import { useProductionPulseRouterPath } from "./hooks/useProductionPulseRouterPath";
import { ScaffoldPage } from "./pages/ScaffoldPage";
import { PanelPage } from "./pages/PanelPage";
import { PpPageHero, PpStateBox, ppShellIcon } from "./app/productionPulseUi";

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
  const { pathname, search } = useProductionPulseRouterPath(pathnameFromHost);
  const route = parseProductionPulseRoute(pathname);
  const permissionFlags = resolveProductionPulsePermissions(permissions, isSuperadmin);

  if (route.kind === "unknown") {
    return (
      <div className="dashboard-production-pulse dashboard-page">
        <div className="pp-page-stack">
          <PpPageHero title="Pulso de Produção" badge={ppShellIcon} />
          <PpStateBox
            variant="error"
            title="Rota não encontrada"
            message="Este caminho ainda não está disponível neste plugin."
          />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-production-pulse dashboard-page">
      {route.kind === "panel" ? (
        <PanelPage search={search} permissions={permissionFlags} />
      ) : (
        <ScaffoldPage mode="operator" />
      )}
    </div>
  );
}
