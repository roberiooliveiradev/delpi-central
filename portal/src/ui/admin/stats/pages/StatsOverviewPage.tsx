// src/ui/admin/stats/pages/StatsOverviewPage.tsx

import { LayoutGrid, Shield, Users, Users2 } from "lucide-react";

import { DonutChart } from "../StatsCharts";
import {
  StatsChartCard,
  StatsInsight,
  StatsInsightRow,
  StatsMiniKpi,
  StatsMiniKpiRow,
  formatPercent,
  statPercent,
} from "../StatsEnrichment";
import { StatsPageIntro, type StatsPageProps, getTrackableActiveApps } from "../StatsShared";

import type { StatsChartsData } from "../useAdminStats";

type StatsOverviewPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

const KPI_ICON = { size: 20, strokeWidth: 2, "aria-hidden": true as const };

export function StatsOverviewPage({ stats, charts }: StatsOverviewPageProps) {
  const usage = stats.apps.usage;
  const trackableActive = getTrackableActiveApps(stats);
  const notifyTotal = stats.notifications?.dispatchesTotal ?? 0;
  const notifyOk = stats.notifications?.dispatchesCompleted ?? 0;
  const onlinePct = statPercent(stats.users.online, stats.users.total);
  const activeUserPct = statPercent(stats.users.active, stats.users.total);

  return (
    <div className="admin-stats-page">
      <StatsPageIntro
        title="Visão geral"
        description="Indicadores principais e distribuição resumida de usuários, aplicações e notificações."
      />

      <div className="admin-stats__kpis" aria-label="Indicadores principais">
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <Users {...KPI_ICON} />
          </span>
          <div>
            <strong>{stats.users.total}</strong>
            <span>Usuários</span>
            <small>
              {stats.users.online} online ({formatPercent(onlinePct)}) ·{" "}
              {stats.users.loggedInLast7Days} logins (7d)
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <LayoutGrid {...KPI_ICON} />
          </span>
          <div>
            <strong>{stats.apps.total}</strong>
            <span>Aplicações</span>
            <small>
              {usage?.inUseNow ?? 0} em uso · {usage?.ghostApps?.length ?? 0} fantasmas ·{" "}
              {usage?.usedInPeriod ?? 0} com uso (30d)
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <Shield {...KPI_ICON} />
          </span>
          <div>
            <strong>{stats.roles.total}</strong>
            <span>Papéis</span>
            <small>
              {stats.roles.system} sistema · {stats.roles.custom} customizados ·{" "}
              {stats.roles.withoutUsers} órfãos
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon">
            <Users2 {...KPI_ICON} />
          </span>
          <div>
            <strong>{stats.groups.total}</strong>
            <span>Grupos</span>
            <small>
              {stats.groups.active} ativos · {stats.permissions.total} permissões ·{" "}
              {stats.assignments.userRoles} vínculos usuário→papel
            </small>
          </div>
        </article>
      </div>

      <StatsInsightRow>
        <StatsInsight
          label="Base ativa"
          value={formatPercent(activeUserPct)}
          detail={`${stats.users.active} de ${stats.users.total} usuários`}
        />
        <StatsInsight
          label="Adoção de apps (30d)"
          value={formatPercent(statPercent(usage?.usedInPeriod ?? 0, trackableActive))}
          detail={`${usage?.usedInPeriod ?? 0} apps com UI usadas`}
        />
        <StatsInsight
          label="Envios de notificação"
          value={String(notifyTotal)}
          detail={
            notifyTotal > 0
              ? `${formatPercent(statPercent(notifyOk, notifyTotal))} concluídos`
              : "Nenhum envio registrado"
          }
        />
        <StatsInsight
          label="RBAC"
          value={String(
            stats.assignments.userRoles +
              stats.assignments.userGroups +
              stats.assignments.groupRoles,
          )}
          detail="Vínculos usuário/grupo/papel (sem permissões)"
        />
      </StatsInsightRow>

      <div className="admin-stats__charts-row">
        <StatsChartCard
          title="Usuários"
          foot={`${stats.users.superadmins} superadmins · ${stats.users.withoutGroups} sem grupo`}
        >
          <DonutChart
            segments={charts.userSegments}
            centerValue={String(stats.users.total)}
            centerLabel="Cadastrados"
          />
        </StatsChartCard>
        <StatsChartCard
          title="Adoção de apps"
          foot={`${usage?.inUseNow ?? 0} em uso neste instante`}
        >
          <DonutChart
            segments={charts.appSegments}
            centerValue={String(trackableActive)}
            centerLabel="Com UI"
          />
        </StatsChartCard>
        <StatsChartCard
          title="Notificações"
          foot={`${stats.notifications?.dispatchesPending ?? 0} pendentes · ${stats.notifications?.dispatchesFailed ?? 0} falhas`}
        >
          <DonutChart
            segments={charts.notificationSegments}
            centerValue={String(notifyTotal)}
            centerLabel="Envios"
          />
        </StatsChartCard>
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi
          tone="primary"
          label="Online"
          value={stats.users.online}
          hint="Presença Socket.IO"
        />
        <StatsMiniKpi
          label="Logins 30d"
          value={stats.users.loggedInLast30Days}
          hint={formatPercent(statPercent(stats.users.loggedInLast30Days, stats.users.total))}
        />
        <StatsMiniKpi
          tone="warning"
          label="Fantasmas"
          value={usage?.ghostApps?.length ?? 0}
          hint="Com UI, sem abertura no portal"
        />
        <StatsMiniKpi
          label="Grupos inativos"
          value={stats.groups.inactive}
          hint={`${stats.groups.withoutUsers} grupos sem usuários`}
        />
      </StatsMiniKpiRow>
    </div>
  );
}
