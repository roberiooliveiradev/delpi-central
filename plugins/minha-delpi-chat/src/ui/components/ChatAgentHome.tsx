import { Bot, Settings, Sparkles } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import {
  AGENT_ICEBREAKER_MAX_COUNT,
  formatIcebreakerForDisplay,
  getIcebreakerGridDensityClass,
  normalizeAgentIcebreakers,
} from "../agentIcebreakers";
import { DEFAULT_AGENT_ICEBREAKERS } from "../chatHomeStarters";

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
  const configuredIcebreakers = normalizeAgentIcebreakers(agent.metadata?.icebreakers);
  const icebreakers =
    configuredIcebreakers.length > 0 ? configuredIcebreakers : DEFAULT_AGENT_ICEBREAKERS;
  const usingDefaultIcebreakers = configuredIcebreakers.length === 0;
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
        {agent.visibility !== "private" && configuredIcebreakers.length > 0 ? (
          <span>
            {Math.min(configuredIcebreakers.length, AGENT_ICEBREAKER_MAX_COUNT)} quebra-gelos
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
              Sugestões para começar — clique ou digite do seu jeito.
            </p>
          ) : null}
          {icebreakers.map((icebreaker) => {
            const displayLabel = formatIcebreakerForDisplay(icebreaker);

            return (
              <button
                key={icebreaker}
                type="button"
                onClick={() => onUseSuggestion(icebreaker)}
                title={icebreaker}
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
