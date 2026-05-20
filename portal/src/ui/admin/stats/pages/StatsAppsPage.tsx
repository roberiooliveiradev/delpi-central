// src/ui/admin/stats/pages/StatsAppsPage.tsx

import { Activity } from "lucide-react";

import { BarChart, DonutChart, LiveAppUsageCard } from "../StatsCharts";
import {
  GhostAppsCompact,
  StatsChartCard,
  StatsMiniKpi,
  StatsMiniKpiRow,
  statPercent,
  formatPercent,
} from "../StatsEnrichment";
import { formatAppType, PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

import type { StatsChartsData } from "../useAdminStats";

type StatsAppsPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

export function StatsAppsPage({ stats, charts, onNavigateTab }: StatsAppsPageProps) {
  const usage = stats.apps.usage;
  const ghostCount = usage?.ghostApps?.length ?? 0;
  const usedInPeriod = usage?.usedInPeriod ?? 0;
  const adoptionPct = statPercent(usedInPeriod, stats.apps.active);

  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Aplicações"
          description="Uso em tempo real, ranking de adoção e apps ativos sem acesso recente."
        />
        <PanelNav tab="apps" label="Gerenciar aplicações" onNavigateTab={onNavigateTab} />
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi
          tone="primary"
          label="Em uso agora"
          value={usage?.inUseNow ?? 0}
          hint={`${(usage?.live ?? []).length} app(s) com sessão`}
        />
        <StatsMiniKpi
          label="Com uso (30d)"
          value={usedInPeriod}
          hint={`${formatPercent(adoptionPct)} das ${stats.apps.active} ativas`}
        />
        <StatsMiniKpi
          tone="warning"
          label="Fantasmas"
          value={ghostCount}
          hint="Ativas sem uso no período"
        />
        <StatsMiniKpi
          label="Cadastro"
          value={stats.apps.total}
          hint={`${stats.apps.active} ativas · ${stats.apps.inactive} inativas`}
        />
      </StatsMiniKpiRow>

      {usage?.enabled ? (
        <div className="admin-stats__apps-workspace">
          <section className="admin-stats__panel admin-stats__panel--live">
            <div className="admin-stats-panel__title-row">
              <h5>
                <Activity size={14} aria-hidden="true" />
                Em uso agora
              </h5>
              <span className="admin-stats-panel__badge">
                {(usage.live ?? []).length} app(s)
              </span>
            </div>
            {(usage.live ?? []).length === 0 ? (
              <p className="admin-stats__empty">Nenhum app em uso no momento.</p>
            ) : (
              <div className="admin-stats__live-grid admin-stats__live-grid--compact">
                {(usage.live ?? []).map((item) => (
                  <LiveAppUsageCard
                    key={item.appId}
                    appId={item.appId}
                    appName={item.appName || item.appId}
                    userCount={item.userCount}
                    sessionCount={item.sessionCount}
                    users={item.users ?? []}
                  />
                ))}
              </div>
            )}
          </section>

          <div className="admin-stats__apps-side">
            <article className="admin-stats__panel admin-stats__panel--stack">
              <h5>Top 30 dias</h5>
              <p className="admin-stats-panel__lede">Usuários únicos por aplicação</p>
              <BarChart
                items={(usage.topUsed ?? []).map((item) => ({
                  id: item.id,
                  label: item.name,
                  value: item.count,
                }))}
                valueLabel="usuários"
                accent={STATS_CHART_COLORS.primary}
                maxItems={8}
              />
            </article>
            <GhostAppsCompact apps={usage.ghostApps ?? []} />
          </div>
        </div>
      ) : (
        <p className="admin-stats__empty">
          Rastreamento de uso desabilitado no servidor.
        </p>
      )}

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <StatsChartCard
          title="Adoção (30 dias)"
          foot={`${usedInPeriod} de ${stats.apps.active} apps ativas com pelo menos um acesso`}
        >
          <DonutChart
            segments={charts.appSegments}
            centerValue={String(usedInPeriod)}
            centerLabel="Com uso"
            size={120}
          />
        </StatsChartCard>
        <StatsChartCard
          title="Infraestrutura"
          foot={`${stats.apps.routesActive} rotas ativas de ${stats.apps.routesTotal} cadastradas`}
        >
          <StatsMiniKpiRow>
            <StatsMiniKpi
              label="Por tipo"
              value={stats.apps.byType.length}
              hint="Renderizações distintas"
            />
            <StatsMiniKpi
              label="Rotas inativas"
              value={stats.apps.routesInactive}
              hint="Fora do ar ou desligadas"
            />
          </StatsMiniKpiRow>
          <BarChart
            items={stats.apps.byType.map((item) => ({
              id: item.type,
              label: formatAppType(item.type),
              value: item.count,
            }))}
            accent={STATS_CHART_COLORS.c2}
            maxItems={6}
          />
        </StatsChartCard>
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi
          label="Iframe"
          value={
            stats.apps.byType.find((t) => t.type === "iframe")?.count ?? 0
          }
          hint="Apps embutidos"
        />
        <StatsMiniKpi
          label="Microfrontend"
          value={
            stats.apps.byType.find((t) => t.type === "microfrontend")?.count ?? 0
          }
        />
        <StatsMiniKpi
          label="Backend-only"
          value={
            stats.apps.byType.find((t) => t.type === "backend-only")?.count ?? 0
          }
        />
        <StatsMiniKpi
          label="Rotas"
          value={stats.apps.routesTotal}
          hint={`${stats.apps.routesActive} rotas ativas`}
        />
      </StatsMiniKpiRow>
    </div>
  );
}
