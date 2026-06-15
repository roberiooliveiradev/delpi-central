import { useEffect, useState } from "react";
import { configureHttpClient } from "./api/httpClient";
import { useLmpsRouterPath } from "./hooks/useLmpsRouterPath";
import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";
import { LmpDetailPage } from "./pages/LmpDetailPage";
import { normalizeLmpsPath, parseLmpsPath, readOvBranchFromUrl } from "./utils/routeParser";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useLmpsRouterPath(pathnameFromHost);
  const path = normalizeLmpsPath(pathname);
  const route = parseLmpsPath(path);
  const showDashboard = route.view === "dashboard";
  const showDetail = route.view === "ov-detail" && Boolean(route.saleNumber);

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

      {showDetail && route.saleNumber ? (
        <LmpDetailPage
          saleNumber={route.saleNumber}
          branch={readOvBranchFromUrl()}
        />
      ) : null}
    </>
  );
}
