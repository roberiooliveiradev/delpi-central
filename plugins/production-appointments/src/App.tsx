import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { totvsBranchFromRoute } from "./constants/branches";
import { parseAppointmentsPath } from "./constants/routes";
import { useProductionAppointmentsRouterPath } from "./hooks/useProductionAppointmentsRouterPath";
import { CtDetailPage } from "./pages/CtDetailPage";
import { OpDetailPage } from "./pages/OpDetailPage";
import { ProductionAppointmentsPage } from "./pages/ProductionAppointmentsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useProductionAppointmentsRouterPath(pathnameFromHost);
  const route = parseAppointmentsPath(pathname);
  const showDashboard = route.view === "dashboard";
  const showOpDetail = route.view === "op-detail" && Boolean(route.productionOrder);
  const showCtDetail = route.view === "ct-detail" && Boolean(route.workCenter);
  const totvsBranch = totvsBranchFromRoute(route.branchRoute);

  const [dashboardMounted, setDashboardMounted] = useState(showDashboard);

  useEffect(() => {
    if (showDashboard) setDashboardMounted(true);
  }, [showDashboard]);

  return (
    <div className="pa-app-shell">
      {dashboardMounted ? (
        <div hidden={!showDashboard} aria-hidden={!showDashboard} className="pa-app-shell__dashboard">
          <ProductionAppointmentsPage
            branchRoute={route.branchRoute}
            totvsBranch={totvsBranch}
            isActive={showDashboard}
          />
        </div>
      ) : null}

      {showOpDetail && route.productionOrder ? (
        <OpDetailPage
          branchRoute={route.branchRoute}
          productionOrder={route.productionOrder}
        />
      ) : null}

      {showCtDetail && route.workCenter ? (
        <CtDetailPage branchRoute={route.branchRoute} workCenter={route.workCenter} />
      ) : null}
    </div>
  );
}
