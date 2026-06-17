import type { ChatAgentStats } from "../../../../data/api/chatTypes";
import { ChatRichDashboard } from "../../presentation/ChatRichDashboard";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import {
  agentDashboardKpisFromPresentation,
  agentUsageKpisFromStats,
  dashboardWithoutKpiPanels,
} from "./agentMiniDashboardHelpers";

import "./AgentMiniDashboard.css";

type AgentMiniDashboardProps = {
  stats: ChatAgentStats;
  /** Layout empilhado e controles reduzidos — builder do agente e colunas estreitas. */
  compact?: boolean;
};

export function AgentMiniDashboard({ stats, compact = false }: AgentMiniDashboardProps) {
  const dashboard = stats.miniDashboard;
  const recommendations = stats.recommendations ?? [];
  const usageKpis = agentUsageKpisFromStats(stats);
  const dashboardKpis = agentDashboardKpisFromPresentation(dashboard);
  const chartDashboard = dashboard
    ? compact
      ? dashboard
      : dashboardWithoutKpiPanels(dashboard)
    : null;

  const kpiItems = compact
    ? []
    : [...usageKpis, ...dashboardKpis].filter(
        (item, index, list) => list.findIndex((entry) => entry.key === item.key) === index,
      );

  return (
    <div
      className={[
        "mdc-agent-mini-dashboard",
        compact ? "mdc-agent-mini-dashboard--compact" : "mdc-agent-mini-dashboard--admin",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!compact && kpiItems.length > 0 ? (
        <AdminKpiGrid>
          {kpiItems.map((item) => (
            <AdminKpiCard key={item.key} title={item.title} value={item.value} hint={item.hint} />
          ))}
        </AdminKpiGrid>
      ) : null}

      {chartDashboard ? (
        <ChatRichDashboard presentation={chartDashboard} variant={compact ? "default" : "admin"} />
      ) : null}

      {recommendations.length > 0 ? (
        <aside className="mdc-agent-mini-dashboard__recommendations" aria-label="Recomendações">
          <h4>Recomendações</h4>
          <ul>
            {recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </aside>
      ) : null}
    </div>
  );
}
