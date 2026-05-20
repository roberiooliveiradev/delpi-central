// src/ui/admin/stats/pages/StatsAppsPage.tsx

import { Ghost } from "lucide-react";

import { BarChart, DonutChart, LiveAppUsageCard } from "../StatsCharts";
import { formatAppType, PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

import type { StatsChartsData } from "../useAdminStats";

type StatsAppsPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

export function StatsAppsPage({ stats, charts, onNavigateTab }: StatsAppsPageProps) {
  const usage = stats.apps.usage;

  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Aplicações"
          description="Quem está em cada app agora, ranking de uso e plugins ativos sem acesso recente."
        />
        <PanelNav tab="apps" label="Gerenciar aplicações" onNavigateTab={onNavigateTab} />
      </div>

      {usage?.enabled ? (
        <div className="admin-stats__apps-layout">
          <div className="admin-stats__panel">
            <h5>Em uso agora</h5>
            {(usage.live ?? []).length === 0 ? (
              <p className="admin-stats__empty">Nenhum app em uso no momento.</p>
            ) : (
              <div className="admin-stats__live-grid">
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
          </div>
          <div className="admin-stats__panel admin-stats__panel--stack">
            <h5>Top 30 dias (usuários únicos)</h5>
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
            <h5 className="admin-stats__subsection">
              <Ghost size={14} aria-hidden="true" />
              Apps fantasmas ({usage.ghostApps?.length ?? 0})
            </h5>
            {(usage.ghostApps ?? []).length === 0 ? (
              <p className="admin-stats__empty admin-stats__empty--success">
                Nenhuma aplicação ativa sem uso no período.
              </p>
            ) : (
              <ul className="admin-stats__ghost-tags">
                {(usage.ghostApps ?? []).map((item) => (
                  <li key={item.id} title={item.id}>
                    {item.name}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : (
        <p className="admin-stats__empty">
          Rastreamento de uso desabilitado no servidor.
        </p>
      )}

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <article className="admin-stats__chart-card">
          <h5>Adoção (30 dias)</h5>
          <DonutChart
            segments={charts.appSegments}
            centerValue={String(usage?.usedInPeriod ?? 0)}
            centerLabel="Com uso"
            size={120}
          />
        </article>
        <article className="admin-stats__chart-card">
          <h5>Por tipo de renderização</h5>
          <BarChart
            items={stats.apps.byType.map((item) => ({
              id: item.type,
              label: formatAppType(item.type),
              value: item.count,
            }))}
            accent={STATS_CHART_COLORS.secondary}
            maxItems={6}
          />
          <p className="admin-stats__chart-foot">
            {stats.apps.routesActive} rotas ativas de {stats.apps.routesTotal} cadastradas
          </p>
        </article>
      </div>
    </div>
  );
}
