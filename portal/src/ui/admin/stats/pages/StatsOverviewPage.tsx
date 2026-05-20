// src/ui/admin/stats/pages/StatsOverviewPage.tsx

import { LayoutGrid, Shield, Users, UsersRound } from "lucide-react";

import { DonutChart } from "../StatsCharts";
import { StatsPageIntro, type StatsPageProps } from "../StatsShared";

import type { StatsChartsData } from "../useAdminStats";

type StatsOverviewPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

export function StatsOverviewPage({ stats, charts }: StatsOverviewPageProps) {
  const usage = stats.apps.usage;

  return (
    <div className="admin-stats-page">
      <StatsPageIntro
        title="Visão geral"
        description="Indicadores principais e distribuição resumida de usuários, aplicações e notificações."
      />

      <div className="admin-stats__kpis" aria-label="Indicadores principais">
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <Users size={18} />
          </span>
          <div>
            <strong>{stats.users.total}</strong>
            <span>Usuários</span>
            <small>
              {stats.users.online} online · {stats.users.loggedInLast7Days} logins (7d)
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <LayoutGrid size={18} />
          </span>
          <div>
            <strong>{stats.apps.total}</strong>
            <span>Aplicações</span>
            <small>
              {usage?.inUseNow ?? 0} em uso · {usage?.ghostApps?.length ?? 0} fantasmas
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <Shield size={18} />
          </span>
          <div>
            <strong>{stats.roles.total}</strong>
            <span>Papéis</span>
            <small>
              {stats.roles.system} sistema · {stats.roles.custom} customizados
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <UsersRound size={18} />
          </span>
          <div>
            <strong>{stats.groups.total}</strong>
            <span>Grupos</span>
            <small>
              {stats.groups.active} ativos · {stats.permissions.total} permissões
            </small>
          </div>
        </article>
      </div>

      <div className="admin-stats__charts-row">
        <article className="admin-stats__chart-card">
          <h5>Usuários</h5>
          <DonutChart
            segments={charts.userSegments}
            centerValue={String(stats.users.total)}
            centerLabel="Cadastrados"
          />
        </article>
        <article className="admin-stats__chart-card">
          <h5>Adoção de apps</h5>
          <DonutChart
            segments={charts.appSegments}
            centerValue={String(stats.apps.active)}
            centerLabel="Ativas"
          />
        </article>
        <article className="admin-stats__chart-card">
          <h5>Notificações</h5>
          <DonutChart
            segments={charts.notificationSegments}
            centerValue={String(stats.notifications?.dispatchesTotal ?? 0)}
            centerLabel="Envios"
          />
        </article>
      </div>
    </div>
  );
}
