import { Bot, Settings, Sparkles } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import {
  AGENT_ICEBREAKER_MAX_COUNT,
  agentIcebreakersUseDefaults,
  formatIcebreakerForDisplay,
  getIcebreakerGridDensityClass,
  resolveAgentIcebreakersForDisplay,
} from "../agentIcebreakers";

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
  const configuredIcebreakers = resolveAgentIcebreakersForDisplay(agent.metadata);
  const usingDefaultIcebreakers = agentIcebreakersUseDefaults(agent.metadata);
  const icebreakers = configuredIcebreakers;
  const icebreakerDensityClass = getIcebreakerGridDensityClass(icebreakers.length);
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
        {agent.visibility !== "private" && !usingDefaultIcebreakers ? (
          <span>
            {Math.min(icebreakers.length, AGENT_ICEBREAKER_MAX_COUNT)} quebra-gelos
          </span>
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
        <div
          className={[
            "mdc-chat-agent-home__icebreakers",
            icebreakerDensityClass,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {usingDefaultIcebreakers ? (
            <p className="mdc-chat-agent-home__icebreakers-hint">
              Sugestões padrão — clique para preencher campos ou digite do seu jeito.
            </p>
          ) : null}
          {icebreakers.map((icebreaker) => {
            const displayLabel = formatIcebreakerForDisplay(icebreaker);

            return (
              <button
                key={icebreaker}
                type="button"
                onClick={() => onUseSuggestion(icebreaker)}
                title={displayLabel}
              >
                <Sparkles size={15} aria-hidden="true" />
                <span>{displayLabel}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
