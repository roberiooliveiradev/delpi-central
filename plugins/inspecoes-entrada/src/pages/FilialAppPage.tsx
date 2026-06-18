import { useCallback, useState } from "react";

import { branchFromPathname } from "../constants/branch";
import { AppHeader } from "../components/AppHeader";
import { DashboardPage } from "./DashboardPage";
import { HistoricoPage } from "./HistoricoPage";
import { syncTabInUrl, tabFromSearch, type InspecoesEntradaTab } from "../utils/tabs";

type FilialAppPageProps = {
  pathname?: string;
  search?: string;
};

export function FilialAppPage({ pathname, search }: FilialAppPageProps) {
  const routeBranch = branchFromPathname(pathname);
  const branch = routeBranch ?? "01";
  const routeTab = tabFromSearch(search);
  const [userTab, setUserTab] = useState<InspecoesEntradaTab | null>(null);
  const [trackedSearch, setTrackedSearch] = useState(search);
  const [refreshToken, setRefreshToken] = useState(0);
  const [loading, setLoading] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  if (search !== trackedSearch) {
    setTrackedSearch(search);
    setUserTab(null);
  }

  const activeTab = userTab ?? routeTab;

  const handleTabChange = useCallback((tab: InspecoesEntradaTab) => {
    setUserTab(tab);
    syncTabInUrl(tab);
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  if (pathname && !routeBranch) {
    return (
      <div className="dashboard-inspecoes-entrada dashboard-page">
        <div className="ie-app-shell">
          <div className="ie-alert ie-alert--error" role="alert">
            <p>
              Rota inválida. Use /apps/inspecoes-entrada/filial-01 ou
              /apps/inspecoes-entrada/filial-02.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-inspecoes-entrada dashboard-page">
      <div className="ie-app-shell">
        <AppHeader
          branch={branch}
          activeTab={activeTab}
          loading={loading}
          lastUpdatedAt={activeTab === "overview" ? lastUpdatedAt : null}
          onTabChange={handleTabChange}
          onRefresh={handleRefresh}
        />

        {activeTab === "overview" ? (
          <DashboardPage
            branch={branch}
            refreshToken={refreshToken}
            onLoadingChange={setLoading}
            onLastUpdated={setLastUpdatedAt}
          />
        ) : (
          <HistoricoPage
            embedded
            pathname={pathname}
            refreshToken={refreshToken}
            onLoadingChange={setLoading}
          />
        )}
      </div>
    </div>
  );
}
