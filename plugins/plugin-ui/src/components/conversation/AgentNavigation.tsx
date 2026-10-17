import { Bot } from "lucide-react";

/** Display fields must come from an owner-approved, live-authorized catalog projection. */
export type AgentNavigationItem = {
  id: string;
  name: string;
  description?: string;
  selected?: boolean;
};

export type AgentNavigationProps = {
  status?: "catalog_unavailable" | "ready" | "loading" | "authorized_empty" | "error";
  agents?: readonly AgentNavigationItem[];
  /** UI navigation intent only; never launches an agent or executes a capability. */
  onSelectAgent?: (id: string) => void;
  /** Only for a contracted retry on a real catalog error. */
  onRetry?: () => void;
  className?: string;
};

/** Pure presentation; neither MCP discovery nor tool metadata grants availability. */
export function AgentNavigation({
  status = "catalog_unavailable",
  agents = [],
  onSelectAgent,
  onRetry,
  className,
}: AgentNavigationProps) {
  return (
    <div className={["delpi-ui-agent-navigation", className].filter(Boolean).join(" ")} data-state={status}>
      {status === "catalog_unavailable" ? (
        <p className="delpi-ui-agent-navigation__message">Agentes estarão disponíveis após a integração autorizada.</p>
      ) : status === "loading" ? (
        <p className="delpi-ui-agent-navigation__message" role="status">Carregando agentes…</p>
      ) : status === "authorized_empty" ? (
        <p className="delpi-ui-agent-navigation__message">Nenhum agente disponível.</p>
      ) : status === "error" ? (
        <div className="delpi-ui-agent-navigation__feedback">
          <p className="delpi-ui-agent-navigation__message" role="alert">Não foi possível carregar agentes.</p>
          {onRetry ? <button type="button" className="delpi-ui-agent-navigation__retry" onClick={onRetry}>Tentar novamente</button> : null}
        </div>
      ) : status === "ready" && onSelectAgent && agents.length > 0 ? (
        <section aria-label="Especialistas disponíveis">
          <h2 className="delpi-ui-conversation-sidebar__section-heading">Especialistas disponíveis</h2>
          <ul className="delpi-ui-agent-navigation__list">
            {agents.map(agent => (
              <li key={agent.id}>
                <button type="button" className="delpi-ui-agent-navigation__item"
                  aria-label={agent.name} aria-current={agent.selected ? "page" : undefined}
                  onClick={() => onSelectAgent(agent.id)}>
                  <Bot size={19} strokeWidth={1.8} aria-hidden="true" />
                  <span className="delpi-ui-agent-navigation__details">
                    <span className="delpi-ui-agent-navigation__name">{agent.name}</span>
                    {agent.description ? <span className="delpi-ui-agent-navigation__description">{agent.description}</span> : null}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
