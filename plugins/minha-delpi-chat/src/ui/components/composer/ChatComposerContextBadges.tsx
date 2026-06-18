import { Bot, Folder, X } from "lucide-react";

import type { ComposerContextBarItem } from "../../../state/chatAgentActivation";
import type { ChatAgent, ChatProject } from "../../../data/api/chatTypes";

import "./ChatComposerContextBadges.css";

type ChatComposerContextBadgesProps = {
  items: ComposerContextBarItem[];
  agents: ChatAgent[];
  projects: ChatProject[];
  onRemoveAgent?: (agentId: string) => void;
  onRemoveProject?: (projectId: string) => void;
};

export function ChatComposerContextBadges({
  items,
  agents,
  projects,
  onRemoveAgent,
  onRemoveProject,
}: ChatComposerContextBadgesProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-composer-context-badges" aria-label="Agentes e projetos ativos">
      {items.map((item) => {
        if (item.kind === "agent") {
          const agent = agents.find((entry) => entry.id === item.id);

          if (!agent) {
            return null;
          }

          return (
            <span
              key={`agent-${item.id}`}
              className="mdc-chat-composer-context-badges__badge mdc-chat-composer-context-badges__badge--agent"
            >
              <Bot size={13} aria-hidden="true" />
              <span className="mdc-chat-composer-context-badges__label">{agent.name}</span>
              <button
                type="button"
                className="mdc-chat-composer-context-badges__remove"
                onClick={() => onRemoveAgent?.(item.id)}
                aria-label={`Remover ${agent.name} do contexto`}
                title={`Remover ${agent.name}`}
              >
                <X size={12} aria-hidden="true" />
              </button>
            </span>
          );
        }

        const project = projects.find((entry) => entry.id === item.id);

        if (!project) {
          return null;
        }

        return (
          <span
            key={`project-${item.id}`}
            className="mdc-chat-composer-context-badges__badge mdc-chat-composer-context-badges__badge--project"
          >
            <Folder size={13} aria-hidden="true" />
            <span className="mdc-chat-composer-context-badges__label">{project.name}</span>
            <button
              type="button"
              className="mdc-chat-composer-context-badges__remove"
              onClick={() => onRemoveProject?.(item.id)}
              aria-label={`Remover ${project.name} do contexto`}
              title={`Remover ${project.name}`}
            >
              <X size={12} aria-hidden="true" />
            </button>
          </span>
        );
      })}
    </div>
  );
}
