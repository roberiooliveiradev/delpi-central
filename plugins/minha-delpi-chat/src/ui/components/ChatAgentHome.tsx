import { Bot, Settings, Share2, Sparkles, Zap } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (value: string) => void;
  onUseAgent?: () => void;
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

function canManageAgent(agent: ChatAgent): boolean {
  return ["owner", "editor", "system"].includes(agent.access_role);
}

export function ChatAgentHome({
  agent,
  onUseSuggestion,
  onUseAgent,
  onManageAgent,
}: ChatAgentHomeProps) {
  const icebreakers = getAgentIcebreakers(agent);

  return (
    <section className="mdc-chat-agent-home" aria-label={`Agente ${agent.name}`}>
      <div className="mdc-chat-agent-home__avatar">
        <Bot size={26} aria-hidden="true" />
      </div>

      <p className="mdc-chat-eyebrow">Agente</p>

      <h2>{agent.name}</h2>

      {agent.description ? <p>{agent.description}</p> : null}

      <div className="mdc-chat-agent-home__meta">
        <span>{agent.visibility === "public" ? "Público interno" : "Privado"}</span>
        {agent.category ? <span>{agent.category}</span> : null}
        {agent.response_style ? <span>{agent.response_style}</span> : null}
        <span>{icebreakers.length} quebra-gelos</span>
      </div>

      <div className="mdc-chat-agent-home__actions">
        <button type="button" onClick={onUseAgent}>
          <Zap size={16} aria-hidden="true" />
          <span>Usar este agente</span>
        </button>

        {canManageAgent(agent) ? (
          <button type="button" onClick={onManageAgent}>
            <Settings size={16} aria-hidden="true" />
            <span>Gerenciar agente</span>
          </button>
        ) : null}

        <button type="button" disabled title="Em breve">
          <Share2 size={16} aria-hidden="true" />
          <span>Compartilhar</span>
        </button>
      </div>

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
