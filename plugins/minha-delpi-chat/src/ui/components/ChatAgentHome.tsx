import { Bot, Settings, Sparkles } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (value: string) => void;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
};

function getAgentIcebreakers(agent: ChatAgent): string[] {
  const value = agent.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 8);
}

export function ChatAgentHome({
  agent,
  onUseSuggestion,
  canManageAgent = false,
  onManageAgent,
}: ChatAgentHomeProps) {
  const icebreakers = getAgentIcebreakers(agent);
  const isPrivate = agent.visibility !== "public";

  return (
    <section className="mdc-chat-agent-home" aria-label={`Agente ${agent.name}`}>
      <div className="mdc-chat-agent-home__avatar">
        <Bot size={26} aria-hidden="true" />
      </div>

      <p className="mdc-chat-eyebrow">Agente</p>

      <h2>{agent.name}</h2>

      {agent.description ? <p>{agent.description}</p> : null}

      <div className="mdc-chat-agent-home__meta">
        <span>{isPrivate ? "Privado" : "Público interno"}</span>
        {!isPrivate && agent.category ? <span>{agent.category}</span> : null}
        {!isPrivate && agent.response_style ? <span>{agent.response_style}</span> : null}
        {!isPrivate && icebreakers.length > 0 ? (
          <span>{icebreakers.length} quebra-gelos</span>
        ) : null}
      </div>

      {canManageAgent ? (
        <div className="mdc-chat-agent-home__actions">
          <button type="button" onClick={onManageAgent}>
            <Settings size={16} aria-hidden="true" />
            <span>Gerenciar agente</span>
          </button>
        </div>
      ) : null}

      {icebreakers.length > 0 ? (
        <div className="mdc-chat-agent-home__icebreakers">
          {icebreakers.map((icebreaker) => (
            <button
              key={icebreaker}
              type="button"
              onClick={() => onUseSuggestion(icebreaker)}
            >
              <Sparkles size={15} aria-hidden="true" />
              <span>{icebreaker}</span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
