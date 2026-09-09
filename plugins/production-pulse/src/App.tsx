import { useEffect } from "react";

import { configureHttpClient } from "./api/httpClient";
import { resolveProductionPulsePermissions } from "./constants/permissions";
import {
  parseProductionPulseRoute,
  productionPulseFirmwareLinksPath,
} from "./constants/routes";
import { useProductionPulseRouterPath } from "./hooks/useProductionPulseRouterPath";
import { useShortViewport } from "./hooks/useShortViewport";
import { useViewportBucket } from "./hooks/useViewportBucket";
import { ProductionPulseShell } from "./components/ProductionPulseShell";
import { FirmwaresPage } from "./pages/FirmwaresPage";
import { FirmwareLinksPage } from "./pages/FirmwareLinksPage";
import { OperatorPage } from "./pages/operator/OperatorPage";
import { PpPageHero, PpStateBox, ppShellIcon } from "./app/productionPulseUi";
import { navigateProductionPulse } from "./utils/navigation";
import { formatAdminEntity } from "./utils/adminHubUiState";

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
  const searchParams = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);

  const redirectTarget =
    route.kind === "firmwareJobs"
      ? productionPulseFirmwareLinksPath({
          branch: route.branch,
          panel: "jobs",
        })
      : route.kind === "panel"
        ? productionPulseFirmwareLinksPath({
            branch: searchParams.get("branch") ?? "01",
            panel: searchParams.get("panel") ?? undefined,
            entity: searchParams.get("entity") ?? undefined,
            modal:
              searchParams.get("modal") ??
              searchParams.get("drawer") ??
              undefined,
          })
        : route.kind === "deviceNew"
          ? productionPulseFirmwareLinksPath({
              branch: route.branch ?? "01",
              modal: "device-create",
            })
          : route.kind === "deviceEdit"
            ? productionPulseFirmwareLinksPath({
                branch: "01",
                entity: formatAdminEntity({ type: "device", id: route.deviceId }) ?? undefined,
                modal: "device-edit",
              })
            : route.kind === "deviceDetail"
              ? productionPulseFirmwareLinksPath({
                  branch: "01",
                  entity: formatAdminEntity({ type: "device", id: route.deviceId }) ?? undefined,
                  modal: "device-detail",
                })
              : route.kind === "firmwareNew"
                ? productionPulseFirmwareLinksPath({
                    branch: "01",
                    modal: "firmware-create",
                  })
                : route.kind === "firmwareDetail"
                  ? productionPulseFirmwareLinksPath({
                      branch: "01",
                      entity:
                        formatAdminEntity({ type: "firmware", id: route.firmwareId }) ?? undefined,
                      modal: "firmware-detail",
                    })
                  : null;

  useEffect(() => {
    if (!redirectTarget) return;
    navigateProductionPulse(redirectTarget);
  }, [redirectTarget]);

  if (
    route.kind === "firmwareJobs" ||
    route.kind === "panel" ||
    route.kind === "deviceNew" ||
    route.kind === "deviceEdit" ||
    route.kind === "deviceDetail" ||
    route.kind === "firmwareNew" ||
    route.kind === "firmwareDetail"
  ) {
    return (
      <div className="dashboard-production-pulse dashboard-page dashboard-page--fill">
        <div className="pp-page-stack">
          <PpPageHero title="Admin" badge={ppShellIcon} />
          <PpStateBox variant="loading" title="Abrindo o mapa Admin…" />
        </div>
      </div>
    );
  }

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
  const isOperatorFillRoute = route.kind === "operatorDevice";
  const isAdminHub = route.kind === "firmwareLinks" || route.kind === "firmwares";

  const adminContent =
    route.kind === "firmwares" ? (
      <FirmwaresPage />
    ) : route.kind === "firmwareLinks" ? (
      <FirmwareLinksPage
        branch={route.branch}
        highlightFirmwareKey={route.firmwareKey}
        focus={route.focus}
        entityParam={route.entity}
        panelParam={route.panel}
        drawerParam={route.drawer}
        modalParam={route.modal}
        permissions={permissionFlags}
      />
    ) : isOperatorRoute ? (
      <OperatorPage route={route} permissions={permissionFlags} />
    ) : null;

  return (
    <div
      className={[
        "dashboard-production-pulse",
        "dashboard-page",
        isOperatorRoute ? "dashboard-production-pulse--operator" : "",
        isOperatorFillRoute || isAdminHub ? "dashboard-page--fill" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-pp-viewport={viewport}
      data-pp-viewport-short={shortViewport && isOperatorRoute ? "true" : undefined}
    >
      {isOperatorRoute ? (
        adminContent
      ) : (
        <ProductionPulseShell
          route={route}
          permissions={permissionFlags}
          fillContent={isAdminHub}
        >
          {adminContent}
        </ProductionPulseShell>
      )}
    </div>
  );
}
