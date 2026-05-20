// src/ui/admin/stats/pages/StatsUsersPage.tsx

import { BarChart, DonutChart } from "../StatsCharts";
import {
  StatsChartCard,
  StatsInsight,
  StatsInsightRow,
  StatsMiniKpi,
  StatsMiniKpiRow,
  formatPercent,
  statPercent,
} from "../StatsEnrichment";
import { PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

import type { StatsChartsData } from "../useAdminStats";

type StatsUsersPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

export function StatsUsersPage({ stats, charts, onNavigateTab }: StatsUsersPageProps) {
  const login7Pct = statPercent(stats.users.loggedInLast7Days, stats.users.total);
  const login30Pct = statPercent(stats.users.loggedInLast30Days, stats.users.total);
  const onlinePct = statPercent(stats.users.online, stats.users.active);

  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Usuários"
          description="Presença no portal, status da base, engajamento de login e lacunas de RBAC."
        />
        <PanelNav tab="users" label="Gerenciar usuários" onNavigateTab={onNavigateTab} />
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi
          tone="primary"
          label="Online agora"
          value={stats.users.online}
          hint={formatPercent(onlinePct) + " da base ativa"}
        />
        <StatsMiniKpi
          label="Ativos"
          value={stats.users.active}
          hint={`${stats.users.inactive} inativos`}
        />
        <StatsMiniKpi
          label="Login 7 dias"
          value={stats.users.loggedInLast7Days}
          hint={formatPercent(login7Pct) + " do total"}
        />
        <StatsMiniKpi
          label="Login 30 dias"
          value={stats.users.loggedInLast30Days}
          hint={formatPercent(login30Pct) + " do total"}
        />
      </StatsMiniKpiRow>

      <StatsInsightRow>
        <StatsInsight
          label="Superadmins"
          value={String(stats.users.superadmins)}
          detail="Acesso total à plataforma"
        />
        <StatsInsight
          label="Sem papel direto"
          value={String(stats.users.withoutDirectRoles)}
          detail="Podem herdar via grupo"
        />
        <StatsInsight
          label="Sem grupo"
          value={String(stats.users.withoutGroups)}
          detail="Revisar onboarding"
        />
        <StatsInsight
          label="Com data de nascimento"
          value={String(stats.users.withBirthDate)}
          detail={formatPercent(statPercent(stats.users.withBirthDate, stats.users.total))}
        />
      </StatsInsightRow>

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <StatsChartCard title="Status da base">
          <DonutChart
            segments={charts.userSegments}
            centerValue={String(stats.users.active)}
            centerLabel="Ativos"
            size={128}
          />
        </StatsChartCard>
        <StatsChartCard
          title="Engajamento e governança"
          foot="Comparativo absoluto — útil para detectar contas dormentes ou sem RBAC"
        >
          <BarChart
            items={[
              { id: "online", label: "Online agora", value: stats.users.online },
              {
                id: "login7",
                label: "Login últimos 7 dias",
                value: stats.users.loggedInLast7Days,
              },
              {
                id: "login30",
                label: "Login últimos 30 dias",
                value: stats.users.loggedInLast30Days,
              },
              {
                id: "super",
                label: "Superadmins",
                value: stats.users.superadmins,
              },
              {
                id: "norole",
                label: "Sem papel direto",
                value: stats.users.withoutDirectRoles,
              },
              {
                id: "nogroup",
                label: "Sem grupo",
                value: stats.users.withoutGroups,
              },
            ]}
            accent={STATS_CHART_COLORS.primary}
            maxItems={8}
          />
        </StatsChartCard>
      </div>
    </div>
  );
}
