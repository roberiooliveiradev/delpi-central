import type { ChatAgent } from "../../data/api/chatTypes";
import {
  agentIcebreakersUseDefaults,
  resolveAgentIcebreakersForDisplay,
  resolveIcebreakerCardPresentation,
} from "../agentIcebreakers";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (value: string) => void;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
};

const DEFAULT_AGENT_HINT =
  "Pergunte do seu jeito — dados, textos e ferramentas deste especialista.";

export function ChatAgentHome({
  agent,
  onUseSuggestion,
  canManageAgent = false,
  onManageAgent,
}: ChatAgentHomeProps) {
  const usingDefaultIcebreakers = agentIcebreakersUseDefaults(agent.metadata);
  const icebreakers = resolveAgentIcebreakersForDisplay(agent.metadata);
  const hint = agent.description?.trim() || DEFAULT_AGENT_HINT;

  return (
    <section
      className="mdc-chat-empty-state mdc-chat-agent-home"
      aria-label={`Agente ${agent.name}`}
    >
      <div className="mdc-chat-empty-state__hero">
        <h2 className="mdc-chat-empty-state__headline">
          <span className="mdc-chat-empty-state__headline-accent">{agent.name}</span>
        </h2>
        <p className="mdc-chat-empty-state__hint">{hint}</p>
        {canManageAgent ? (
          <button
            type="button"
            className="mdc-chat-empty-state__tour-link"
            onClick={onManageAgent}
          >
            Gerenciar agente
          </button>
        ) : null}
      </div>

      {icebreakers.length > 0 ? (
        <div
          className="mdc-chat-empty-state__highlights"
          role="region"
          aria-label="Sugestões para começar"
        >
          <p className="mdc-chat-empty-state__highlights-label">Comece por aqui</p>
          {icebreakers.map((icebreaker) => {
            const card = resolveIcebreakerCardPresentation(icebreaker);

            return (
              <button
                key={icebreaker}
                type="button"
                className="mdc-chat-empty-state__highlight-chip"
                title={card.subtitle ? `${card.title} — ${card.subtitle}` : card.title}
                onClick={() => onUseSuggestion(icebreaker)}
              >
                <strong>{card.title}</strong>
                {card.subtitle ? <span>{card.subtitle}</span> : null}
              </button>
            );
          })}
          {usingDefaultIcebreakers ? (
            <p className="mdc-chat-agent-home__suggestions-footnote">
              Sugestões padrão — clique para enviar ao agente.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
