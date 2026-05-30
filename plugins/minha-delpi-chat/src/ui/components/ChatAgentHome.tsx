import { Bot, Settings, Sparkles } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { DEFAULT_AGENT_ICEBREAKERS } from "../chatHomeStarters";

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
  const configuredIcebreakers = getAgentIcebreakers(agent);
  const icebreakers =
    configuredIcebreakers.length > 0 ? configuredIcebreakers : DEFAULT_AGENT_ICEBREAKERS;
  const usingDefaultIcebreakers = configuredIcebreakers.length === 0;
  const visibilityLabel =
    agent.visibility === "system"
      ? "Oficial"
      : agent.visibility === "public"
        ? "Público interno"
        : "Privado";

  return (
    <section className="mdc-chat-agent-home" aria-label={`Agente ${agent.name}`}>
      <div className="mdc-chat-agent-home__avatar">
        <Bot size={26} aria-hidden="true" />
      </div>

      <p className="mdc-chat-eyebrow">Agente</p>

      <h2>{agent.name}</h2>

      {agent.description ? <p>{agent.description}</p> : null}

      <div className="mdc-chat-agent-home__meta">
        <span>{visibilityLabel}</span>
        {agent.visibility !== "private" && agent.category ? <span>{agent.category}</span> : null}
        {agent.visibility !== "private" && agent.response_style ? (
          <span>{agent.response_style}</span>
        ) : null}
        {agent.visibility !== "private" && configuredIcebreakers.length > 0 ? (
          <span>{configuredIcebreakers.length} quebra-gelos</span>
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
          {usingDefaultIcebreakers ? (
            <p className="mdc-chat-agent-home__icebreakers-hint">
              Sugestões para começar — clique ou digite do seu jeito.
            </p>
          ) : null}
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
