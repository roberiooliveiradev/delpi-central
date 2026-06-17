import { Bot, Settings } from "lucide-react";

import type { ChatAgent } from "../../../data/api/chatTypes";
import {
  formatIcebreakerForDisplay,
  resolveAgentIcebreakersForDisplay,
} from "../../agentIcebreakers";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (value: string) => void;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
};

export function ChatAgentHome({
  agent,
  onUseSuggestion,
  canManageAgent = false,
  onManageAgent,
}: ChatAgentHomeProps) {
  const icebreakers = resolveAgentIcebreakersForDisplay(agent.metadata).slice(0, 6);

  return (
    <section className="mdc-chat-landing mdc-chat-agent-home" aria-label={`Agente ${agent.name}`}>
      <div className="mdc-chat-landing__avatar" aria-hidden="true">
        <Bot size={26} />
      </div>

      <h2 className="mdc-chat-landing__title">{agent.name}</h2>

      {agent.description ? (
        <p className="mdc-chat-landing__description">{agent.description}</p>
      ) : null}

      {canManageAgent ? (
        <button type="button" className="mdc-chat-landing__manage" onClick={onManageAgent}>
          <Settings size={15} aria-hidden="true" />
          <span>Gerenciar agente</span>
        </button>
      ) : null}

      {icebreakers.length > 0 ? (
        <div
          className="mdc-chat-landing__prompts"
          role="region"
          aria-label="Sugestões para começar"
        >
          {icebreakers.map((icebreaker) => (
            <button
              key={icebreaker}
              type="button"
              className="mdc-chat-landing__prompt"
              title={icebreaker}
              onClick={() => onUseSuggestion(icebreaker)}
            >
              {formatIcebreakerForDisplay(icebreaker)}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
