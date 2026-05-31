import type { ChatAgentStats } from "../../../../data/api/chatTypes";
import { ChatRichDashboard } from "../../ChatRichDashboard";

import "./AgentMiniDashboard.css";

type AgentMiniDashboardProps = {
  stats: ChatAgentStats;
};

export function AgentMiniDashboard({ stats }: AgentMiniDashboardProps) {
  const dashboard = stats.miniDashboard;
  const recommendations = stats.recommendations ?? [];

  return (
    <div className="mdc-agent-mini-dashboard">
      {dashboard ? (
        <ChatRichDashboard presentation={dashboard} />
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
