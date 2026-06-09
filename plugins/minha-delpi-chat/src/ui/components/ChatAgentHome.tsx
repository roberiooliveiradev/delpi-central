import {
  ArrowUpRight,
  BadgeCheck,
  Bot,
  Boxes,
  Globe,
  MessageSquare,
  Package,
  PenLine,
  Settings,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import {
  AGENT_ICEBREAKER_MAX_COUNT,
  agentIcebreakersUseDefaults,
  getIcebreakerGridDensityClass,
  resolveAgentIcebreakersForDisplay,
  resolveIcebreakerCardPresentation,
  resolveIcebreakerVisualKind,
  type IcebreakerVisualKind,
} from "../agentIcebreakers";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (value: string) => void;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
};

const ICEBREAKER_ICONS: Record<IcebreakerVisualKind, LucideIcon> = {
  product: Package,
  stock: Boxes,
  web: Globe,
  capabilities: Sparkles,
  text: PenLine,
  generic: MessageSquare,
};

function formatAgentMetaLabel(value: string): string {
  const trimmed = value.trim();

  if (!trimmed) {
    return trimmed;
  }

  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
}

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
  const isOfficial = agent.visibility === "system";

  return (
    <section className="mdc-chat-agent-home" aria-label={`Agente ${agent.name}`}>
      <div className="mdc-chat-agent-home__hero">
        <div
          className={[
            "mdc-chat-agent-home__avatar",
            isOfficial ? "mdc-chat-agent-home__avatar--official" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <Bot size={22} aria-hidden="true" />
        </div>

        <div className="mdc-chat-agent-home__identity">
          <p className="mdc-chat-eyebrow">Agente</p>
          <h2>{agent.name}</h2>

          {agent.description ? (
            <p className="mdc-chat-agent-home__description">{agent.description}</p>
          ) : null}

          <div className="mdc-chat-agent-home__meta">
            <span
              className={[
                "mdc-chat-agent-home__meta-badge",
                isOfficial ? "mdc-chat-agent-home__meta-badge--official" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {isOfficial ? <BadgeCheck size={13} aria-hidden="true" /> : null}
              {visibilityLabel}
            </span>
            {agent.visibility !== "private" && agent.category ? (
              <span className="mdc-chat-agent-home__meta-badge">
                {formatAgentMetaLabel(agent.category)}
              </span>
            ) : null}
            {agent.visibility !== "private" && agent.response_style ? (
              <span className="mdc-chat-agent-home__meta-badge">
                {formatAgentMetaLabel(agent.response_style)}
              </span>
            ) : null}
            {agent.visibility !== "private" && !usingDefaultIcebreakers ? (
              <span className="mdc-chat-agent-home__meta-badge">
                {Math.min(icebreakers.length, AGENT_ICEBREAKER_MAX_COUNT)} quebra-gelos
              </span>
            ) : null}
          </div>

          {canManageAgent ? (
            <div className="mdc-chat-agent-home__actions">
              <button type="button" className="mdc-chat-agent-home__manage" onClick={onManageAgent}>
                <Settings size={15} aria-hidden="true" />
                <span>Gerenciar agente</span>
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {icebreakers.length > 0 ? (
        <div className="mdc-chat-agent-home__suggestions">
          <header className="mdc-chat-agent-home__suggestions-header">
            <h3>Comece por aqui</h3>
            <p>
              {usingDefaultIcebreakers
                ? "Sugestões padrão — clique para enviar ao agente."
                : "Quebra-gelos configurados para este agente."}
            </p>
          </header>

          <div className="mdc-chat-agent-home__icebreakers-scroll">
            <div
              className={["mdc-chat-agent-home__icebreakers", icebreakerDensityClass]
                .filter(Boolean)
                .join(" ")}
            >
              {icebreakers.map((icebreaker) => {
                const card = resolveIcebreakerCardPresentation(icebreaker);
                const visualKind = resolveIcebreakerVisualKind(icebreaker);
                const Icon = ICEBREAKER_ICONS[visualKind];

                return (
                  <button
                    key={icebreaker}
                    type="button"
                    className={[
                      "mdc-chat-agent-home__icebreaker",
                      `mdc-chat-agent-home__icebreaker--${visualKind}`,
                    ].join(" ")}
                    onClick={() => onUseSuggestion(icebreaker)}
                    title={card.subtitle ? `${card.title} — ${card.subtitle}` : card.title}
                  >
                    <span className="mdc-chat-agent-home__icebreaker-top">
                      <span className="mdc-chat-agent-home__icebreaker-icon-wrap">
                        <Icon size={16} aria-hidden="true" />
                      </span>
                      <ArrowUpRight
                        size={15}
                        aria-hidden="true"
                        className="mdc-chat-agent-home__icebreaker-arrow"
                      />
                    </span>
                    <span className="mdc-chat-agent-home__icebreaker-copy">
                      <strong>{card.title}</strong>
                      {card.subtitle ? (
                        card.example ? (
                          <span className="mdc-chat-agent-home__icebreaker-example">
                            <span className="mdc-chat-agent-home__icebreaker-example-label">Ex.</span>
                            <span className="mdc-chat-agent-home__icebreaker-example-value">
                              {card.subtitle}
                            </span>
                          </span>
                        ) : (
                          <span className="mdc-chat-agent-home__icebreaker-hint">{card.subtitle}</span>
                        )
                      ) : null}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
