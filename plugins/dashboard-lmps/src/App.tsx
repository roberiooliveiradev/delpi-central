import { useEffect, useState } from "react";
import { configureHttpClient } from "./api/httpClient";
import { useLmpsRouterPath } from "./hooks/useLmpsRouterPath";
import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";
import { LmpDetailPage } from "./pages/LmpDetailPage";
import { NonconformitiesPage } from "./pages/NonconformitiesPage";
import { normalizeLmpsPath, parseLmpsPath, readOvBranchFromUrl } from "./utils/routeParser";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  hasPermission?: (code: string) => boolean;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  hasPermission,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useLmpsRouterPath(pathnameFromHost);
  const path = normalizeLmpsPath(pathname);
  const route = parseLmpsPath(path);
  const showDashboard = route.view === "dashboard";
  const showNonconformities = route.view === "nonconformities";
  const showDetail = route.view === "ov-detail" && Boolean(route.saleNumber);
  const canWriteNc =
    typeof hasPermission === "function"
      ? hasPermission("dashboard-lmps.nc.write")
      : true;

  const [dashboardMounted, setDashboardMounted] = useState(showDashboard);

  useEffect(() => {
    if (showDashboard) {
      setDashboardMounted(true);
    }
  }, [showDashboard]);

  return (
    <>
      {dashboardMounted ? (
        <div hidden={!showDashboard} aria-hidden={!showDashboard}>
          <DashboardLmpsPage pathname={path} isActive={showDashboard} />
        </div>
      ) : null}

      {showNonconformities ? (
        <NonconformitiesPage pathname={path} canWrite={canWriteNc} />
      ) : null}

      {showDetail && route.saleNumber ? (
        <LmpDetailPage
          saleNumber={route.saleNumber}
          branch={readOvBranchFromUrl()}
        />
      ) : null}
    </>
  );
}
