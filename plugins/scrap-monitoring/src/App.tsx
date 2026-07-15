import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { useScrapMonitoringRouterPath } from "./hooks/useScrapMonitoringRouterPath";
import { ScrapMonitoringPage } from "./pages/ScrapMonitoringPage";
import { ScrapRegistroDetailPage } from "./pages/ScrapRegistroDetailPage";
import { parseScrapPath, readRegistroFromSearch } from "./utils/routes";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useScrapMonitoringRouterPath(pathnameFromHost);
  const route = parseScrapPath(pathname);
  const showDashboard = route.view === "dashboard";
  const showDetail = route.view === "registro-detail";

  const [dashboardMounted, setDashboardMounted] = useState(showDashboard);
  const [registro, setRegistro] = useState(() =>
    showDetail ? readRegistroFromSearch(window.location.search) : null,
  );

  useEffect(() => {
    if (showDashboard) {
      setDashboardMounted(true);
    }
  }, [showDashboard]);

  useEffect(() => {
    if (!showDetail) {
      setRegistro(null);
      return;
    }
    setRegistro(readRegistroFromSearch(window.location.search));
  }, [showDetail, pathname]);

  return (
    <div className="sm-app-root">
      {dashboardMounted ? (
        <div hidden={!showDashboard} aria-hidden={!showDashboard}>
          <ScrapMonitoringPage
            branchRoute={route.branchRoute}
            isActive={showDashboard}
          />
        </div>
      ) : null}

      {showDetail ? (
        <ScrapRegistroDetailPage
          branchRoute={route.branchRoute}
          registro={registro}
        />
      ) : null}
    </div>
  );
}
