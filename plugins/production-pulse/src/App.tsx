import { configureHttpClient } from "./api/httpClient";
import { resolveProductionPulsePermissions } from "./constants/permissions";
import { parseProductionPulseRoute } from "./constants/routes";
import { useProductionPulseRouterPath } from "./hooks/useProductionPulseRouterPath";
import { useShortViewport } from "./hooks/useShortViewport";
import { useViewportBucket } from "./hooks/useViewportBucket";
import { PanelPage } from "./pages/PanelPage";
import { DeviceFormPage } from "./pages/DeviceFormPage";
import { DeviceDetailPage } from "./pages/DeviceDetailPage";
import { OperatorPage } from "./pages/operator/OperatorPage";
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
  const route = parseProductionPulseRoute(pathname, search);
  const permissionFlags = resolveProductionPulsePermissions(permissions, isSuperadmin);
  const viewport = useViewportBucket();
  const shortViewport = useShortViewport();

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

  const isOperatorRoute =
    route.kind === "operatorHub" ||
    route.kind === "operatorPicker" ||
    route.kind === "operatorDevice";
  /** Superfície imersiva (contador/gauge): preenche a área do .content do portal. */
  const isOperatorFillRoute = route.kind === "operatorDevice";

  return (
    <div
      className={[
        "dashboard-production-pulse",
        "dashboard-page",
        isOperatorRoute ? "dashboard-production-pulse--operator" : "",
        isOperatorFillRoute ? "dashboard-page--fill" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-pp-viewport={viewport}
      data-pp-viewport-short={shortViewport && isOperatorRoute ? "true" : undefined}
    >
      {route.kind === "panel" ? (
        <PanelPage search={search} permissions={permissionFlags} />
      ) : route.kind === "deviceNew" ? (
        <DeviceFormPage
          mode="create"
          initialBranch={route.branch}
          permissions={permissionFlags}
        />
      ) : route.kind === "deviceEdit" ? (
        <DeviceFormPage mode="edit" deviceId={route.deviceId} permissions={permissionFlags} />
      ) : route.kind === "deviceDetail" ? (
        <DeviceDetailPage
          deviceId={route.deviceId}
          tab={route.tab}
          search={search}
          permissions={permissionFlags}
        />
      ) : isOperatorRoute ? (
        <OperatorPage route={route} permissions={permissionFlags} />
      ) : null}
    </div>
  );
}
