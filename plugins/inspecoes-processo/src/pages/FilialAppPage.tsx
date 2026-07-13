import { useCallback, useEffect, useState } from "react";

import { AppHeader } from "../components/AppHeader";
import { branchFromPathname } from "../constants/branch";
import { syncTabInUrl, tabFromSearch, type InspecoesProcessoTab } from "../utils/tabs";
import { AuditoriaPage } from "./AuditoriaPage";
import { DashboardPage } from "./DashboardPage";
import { HistoricoPage } from "./HistoricoPage";

type FilialAppPageProps = {
  pathname?: string;
  search?: string;
};

export function FilialAppPage({ pathname, search }: FilialAppPageProps) {
  const routeBranch = branchFromPathname(pathname);
  const branch = routeBranch ?? "01";
  const routeTab = tabFromSearch(search);
  const [userTab, setUserTab] = useState<InspecoesProcessoTab | null>(null);
  const [trackedSearch, setTrackedSearch] = useState(search);
  const [refreshToken, setRefreshToken] = useState(0);
  const [loading, setLoading] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const [visitedTabs, setVisitedTabs] = useState<Set<InspecoesProcessoTab>>(
    () => new Set([routeTab]),
  );

  if (search !== trackedSearch) {
    setTrackedSearch(search);
    setUserTab(null);
  }

  const activeTab = userTab ?? routeTab;

  useEffect(() => {
    setVisitedTabs((current) => {
      if (current.has(activeTab)) return current;
      const next = new Set(current);
      next.add(activeTab);
      return next;
    });
  }, [activeTab]);

  const handleTabChange = useCallback((tab: InspecoesProcessoTab) => {
    setUserTab(tab);
    syncTabInUrl(tab);
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  if (pathname && !routeBranch) {
    return (
      <div className="dashboard-inspecoes-processo dashboard-page inspecoes-processo-app">
        <div className="ip-app-shell">
          <div className="ip-alert ip-alert--error" role="alert">
            <p>
              Rota inválida. Use /apps/inspecoes-processo/filial-01 ou
              /apps/inspecoes-processo/filial-02.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-inspecoes-processo dashboard-page inspecoes-processo-app">
      <div className="ip-app-shell">
        <AppHeader
          branch={branch}
          activeTab={activeTab}
          loading={loading}
          lastUpdatedAt={activeTab === "overview" ? lastUpdatedAt : null}
          onTabChange={handleTabChange}
          onRefresh={handleRefresh}
        />

        {/* Lazy keep-alive: monta na 1ª visita e mantém estado/cache ao trocar de aba. */}
        {visitedTabs.has("overview") ? (
          <div
            className="ip-tab-panel"
            hidden={activeTab !== "overview"}
            aria-hidden={activeTab !== "overview"}
          >
            <DashboardPage
              branch={branch}
              active={activeTab === "overview"}
              refreshToken={refreshToken}
              onLoadingChange={setLoading}
              onLastUpdated={setLastUpdatedAt}
            />
          </div>
        ) : null}
        {visitedTabs.has("historico") ? (
          <div
            className="ip-tab-panel"
            hidden={activeTab !== "historico"}
            aria-hidden={activeTab !== "historico"}
          >
            <HistoricoPage
              branch={branch}
              active={activeTab === "historico"}
              refreshToken={refreshToken}
              onLoadingChange={setLoading}
            />
          </div>
        ) : null}
        {visitedTabs.has("auditoria") ? (
          <div
            className="ip-tab-panel"
            hidden={activeTab !== "auditoria"}
            aria-hidden={activeTab !== "auditoria"}
          >
            <AuditoriaPage
              branch={branch}
              active={activeTab === "auditoria"}
              refreshToken={refreshToken}
              onLoadingChange={setLoading}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
