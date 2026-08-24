// src/ui/admin/tabs/StatsTab.tsx

import { useState } from "react";
import {
  Activity,
  BarChart3,
  Bell,
  Compass,
  LayoutGrid,
  LayoutDashboard,
  LineChart,
  Shield,
  Users,
} from "lucide-react";

import type { AdminTab } from "../AdminPage";
import { useAdminStats } from "../stats/useAdminStats";
import { useAdminEngagementStats } from "../stats/useAdminEngagementStats";
import { StatsRefreshBar } from "../stats/StatsShared";
import { STATS_SUB_PAGES, type StatsSubPage } from "../stats/statsTheme";
import { StatsOverviewPage } from "../stats/pages/StatsOverviewPage";
import { StatsUsagePage } from "../stats/pages/StatsUsagePage";
import { StatsUsersPage } from "../stats/pages/StatsUsersPage";
import { StatsAppsPage } from "../stats/pages/StatsAppsPage";
import { StatsAccessPage } from "../stats/pages/StatsAccessPage";
import { StatsNotificationsPage } from "../stats/pages/StatsNotificationsPage";
import { StatsTourPage } from "../stats/pages/StatsTourPage";
import { Button } from "../../../ui-kit";

import "./StatsTab.css";

type StatsTabProps = {
  onNavigateTab?: (tab: AdminTab) => void;
};

const SUB_PAGE_ICONS: Record<StatsSubPage, typeof LayoutDashboard> = {
  overview: LayoutDashboard,
  usage: LineChart,
  users: Users,
  apps: LayoutGrid,
  access: Shield,
  notifications: Bell,
  tour: Compass,
};

export const StatsTab = ({ onNavigateTab }: StatsTabProps) => {
  const [page, setPage] = useState<StatsSubPage>("overview");
  const { stats, loading, error, load, charts, autoRefreshSeconds } = useAdminStats();
  const engagementResource = useAdminEngagementStats(30);

  const activeMeta = STATS_SUB_PAGES.find((item) => item.id === page)!;

  if (loading && !stats) {
    return (
      <div className="admin-stats admin-stats--loading">
        <div className="admin-stats__skeleton admin-stats__skeleton--hero" />
        <div className="admin-stats__skeleton admin-stats__skeleton--subnav" />
        <div className="admin-stats__skeleton admin-stats__skeleton--panel" />
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="admin-stats">
        <div className="admin-stats__state admin-stats__state--error">{error}</div>
        <Button variant="primary" onClick={() => void load()}>
          Tentar novamente
        </Button>
      </div>
    );
  }

  if (!stats || !charts) {
    return <div className="admin-stats__state">Nenhum dado disponível.</div>;
  }

  const pageProps = {
    stats,
    charts,
    engagement: engagementResource.engagement,
    onNavigateTab,
    onNavigateStatsSubPage: setPage,
  };

  return (
    <section className="admin-stats" aria-labelledby="admin-stats-title">
      <header className="admin-stats__hero">
        <div className="admin-stats__hero-copy">
          <span className="admin-stats__eyebrow">
            <BarChart3 size={14} aria-hidden="true" />
            Estatísticas Minha DELPI
          </span>
          <h3 id="admin-stats-title">Painel de governança</h3>
          <p>
            Métricas separadas por tema — usuários, apps, RBAC e notificações — com as cores
            e o visual do portal.
          </p>
        </div>
        <StatsRefreshBar
          generatedAt={stats.generatedAt}
          loading={loading}
          onRefresh={() => void load()}
          autoRefreshSeconds={autoRefreshSeconds}
        />
      </header>

      <nav className="admin-stats-subnav" aria-label="Seções de estatísticas">
        {STATS_SUB_PAGES.map((item) => {
          const Icon = SUB_PAGE_ICONS[item.id];
          const isActive = item.id === page;

          return (
            <button
              key={item.id}
              type="button"
              className={`admin-stats-subnav__item ${isActive ? "active" : ""}`}
              data-tour={item.id === "tour" ? "admin-stats-subnav-tour" : undefined}
              onClick={() => setPage(item.id)}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon size={16} aria-hidden="true" />
              <span className="admin-stats-subnav__label">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="admin-stats__page-shell">
        <div className="admin-stats__page-active" aria-live="polite">
          <Activity size={14} aria-hidden="true" />
          <span>{activeMeta.label}</span>
          <span className="admin-stats__page-active-desc">{activeMeta.description}</span>
        </div>

        {page === "overview" ? <StatsOverviewPage {...pageProps} /> : null}
        {page === "usage" ? (
          <StatsUsagePage
            stats={stats}
            engagement={engagementResource.engagement}
            loading={engagementResource.loading}
            error={engagementResource.error}
            periodDays={engagementResource.periodDays}
            onPeriodChange={engagementResource.changePeriod}
            onRefresh={() => void engagementResource.load()}
            onNavigateTab={onNavigateTab}
            onNavigateStatsSubPage={setPage}
          />
        ) : null}
        {page === "users" ? <StatsUsersPage {...pageProps} /> : null}
        {page === "apps" ? <StatsAppsPage {...pageProps} /> : null}
        {page === "access" ? <StatsAccessPage stats={stats} onNavigateTab={onNavigateTab} /> : null}
        {page === "notifications" ? (
          <StatsNotificationsPage {...pageProps} />
        ) : null}
        {page === "tour" ? <StatsTourPage /> : null}
      </div>
    </section>
  );
};
