import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { totvsBranchFromRoute } from "./constants/branches";
import { parseAppointmentsPath } from "./constants/routes";
import { useProductionAppointmentsRouterPath } from "./hooks/useProductionAppointmentsRouterPath";
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
  const showDetail = route.view === "op-detail" && Boolean(route.productionOrder);
  const totvsBranch = totvsBranchFromRoute(route.branchRoute);

  const [dashboardMounted, setDashboardMounted] = useState(showDashboard);

  useEffect(() => {
    if (showDashboard) setDashboardMounted(true);
  }, [showDashboard]);

  return (
    <div className="pa-app-shell">
      {dashboardMounted ? (
        <ProductionAppointmentsPage
          branchRoute={route.branchRoute}
          totvsBranch={totvsBranch}
          isActive={showDashboard}
        />
      ) : null}

      {showDetail && route.productionOrder ? (
        <OpDetailPage
          branchRoute={route.branchRoute}
          productionOrder={route.productionOrder}
        />
      ) : null}
    </div>
  );
}
