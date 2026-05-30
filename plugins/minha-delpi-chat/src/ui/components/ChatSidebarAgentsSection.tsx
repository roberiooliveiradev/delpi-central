import { Bot, Settings } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { buildChatAgentHref, buildChatHref } from "../../navigation/chatRoutes";
import { handleChatNavClick } from "../../navigation/chatNavigation";
import { ChatSidebarWorkspaceItem } from "./ChatSidebarWorkspaceItem";

type ChatSidebarAgentsSectionProps = {
  agents: ChatAgent[];
  selectedAgentId?: string | null;
  isLoading?: boolean;
  onSelectAgent?: (agentId: string | null) => void;
  onManageAgents: () => void;
  canManageAgents?: boolean;
  hideTitle?: boolean;
};

export function ChatSidebarAgentsSection({
  agents,
  selectedAgentId,
  isLoading,
  onSelectAgent: _onSelectAgent,
  onManageAgents,
  canManageAgents = false,
  hideTitle,
}: ChatSidebarAgentsSectionProps) {
  return (
    <>
      {!hideTitle ? (
        <div className="mdc-chat-sidebar__section-title">
          <span>Apps e agentes</span>
          <small>{agents.length}</small>
        </div>
      ) : null}

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
              active={agent.id === selectedAgentId}
              href={buildChatAgentHref(agent.id)}
              badge={
                agent.access_role === "owner"
                  ? "Seu"
                  : agent.access_role === "system"
                    ? "Oficial"
                    : null
              }
            />
          ))
        )}
      </div>

      {canManageAgents ? (
        <div className="mdc-chat-sidebar__project-manage">
          <a
            href={buildChatHref({ kind: "agents" })}
            onClick={(event) => {
              handleChatNavClick(event, buildChatHref({ kind: "agents" }), {
                onNavigate: onManageAgents,
              });
            }}
          >
            <Settings size={15} aria-hidden="true" />
            <span>Gerenciar agentes</span>
          </a>
        </div>
      ) : null}
    </>
  );
}
