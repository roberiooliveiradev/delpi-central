import { useEffect, useState } from "react";
import { configureHttpClient } from "./api/httpClient";
import { useCommercialRouterPath } from "./hooks/useCommercialRouterPath";
import { CommercialDetailPage } from "./pages/CommercialDetailPage";
import { DashboardCommercialPage } from "./pages/DashboardCommercialPage";
import {
  normalizeCommercialPath,
  parseCommercialPath,
  readProposalBranchFromUrl,
  readProposalRevisionFromUrl,
} from "./utils/routeParser";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useCommercialRouterPath(pathnameFromHost);
  const path = normalizeCommercialPath(pathname);
  const route = parseCommercialPath(path);
  const showDashboard = route.view === "dashboard";
  const showDetail =
    route.view === "ov-detail" && Boolean(route.proposalNumber);

  const [dashboardMounted, setDashboardMounted] = useState(showDashboard);

  useEffect(() => {
    if (showDashboard) {
      setDashboardMounted(true);
    }
  }, [showDashboard]);

  return (
    <div className="dc-app-shell">
      {dashboardMounted ? (
        <div hidden={!showDashboard} aria-hidden={!showDashboard}>
          <DashboardCommercialPage isActive={showDashboard} />
        </div>
      ) : null}

      {showDetail && route.proposalNumber ? (
        <CommercialDetailPage
          proposalNumber={route.proposalNumber}
          branch={readProposalBranchFromUrl()}
          revision={readProposalRevisionFromUrl()}
        />
      ) : null}
    </div>
  );
}
