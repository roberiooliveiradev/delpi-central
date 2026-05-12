import { Bot, Settings } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { ChatSidebarWorkspaceItem } from "./ChatSidebarWorkspaceItem";

type ChatSidebarAgentsSectionProps = {
  agents: ChatAgent[];
  selectedAgentKey?: string | null;
  isLoading?: boolean;
  onSelectAgent?: (agentKey: string | null) => void;
  onManageAgents: () => void;
};

export function ChatSidebarAgentsSection({
  agents,
  selectedAgentKey,
  isLoading,
  onSelectAgent,
  onManageAgents,
}: ChatSidebarAgentsSectionProps) {
  return (
    <>
      <div className="mdc-chat-sidebar__section-title">
        <span>Apps e agentes</span>
        <small>{agents.length}</small>
      </div>

      <div className="mdc-chat-sidebar__link-list">
        {isLoading ? (
          <p className="mdc-chat-muted">Carregando agentes...</p>
        ) : agents.length === 0 ? (
          <p className="mdc-chat-muted">Nenhum agente disponível.</p>
        ) : (
          agents.map((agent) => (
            <ChatSidebarWorkspaceItem
              key={agent.id}
              icon={Bot}
              title={agent.name}
              subtitle={agent.category || agent.description || agent.visibility}
              active={agent.key === selectedAgentKey}
              badge={
                agent.access_role === "owner"
                  ? "Seu"
                  : agent.access_role === "system"
                    ? "Oficial"
                    : null
              }
              onClick={() =>
                onSelectAgent?.(
                  agent.key === selectedAgentKey ? null : agent.key,
                )
              }
            />
          ))
        )}
      </div>

      <div className="mdc-chat-sidebar__project-manage">
        <button type="button" onClick={onManageAgents}>
          <Settings size={15} aria-hidden="true" />
          <span>Gerenciar agentes</span>
        </button>
      </div>
    </>
  );
}
