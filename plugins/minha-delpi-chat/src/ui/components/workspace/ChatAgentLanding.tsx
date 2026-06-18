import { Settings } from "lucide-react";
import type { ReactNode } from "react";

import {
  AGENT_ICEBREAKER_HOME_DISPLAY_COUNT,
  resolveIcebreakerCardPresentation,
} from "../../agentIcebreakers";
import { ChatAgentIcon } from "./ChatAgentIcon";

import "./ChatAgentLanding.css";

export type ChatAgentLandingProps = {
  name: string;
  icon?: string | null;
  description?: string | null;
  icebreakers?: string[];
  onIcebreakerClick?: (template: string) => void;
  icebreakersDisabled?: boolean;
  defaultIcebreakersHint?: string | null;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
  className?: string;
  footer?: ReactNode;
};

export function ChatAgentLanding({
  name,
  icon,
  description,
  icebreakers = [],
  onIcebreakerClick,
  icebreakersDisabled = false,
  defaultIcebreakersHint,
  canManageAgent = false,
  onManageAgent,
  className,
  footer,
}: ChatAgentLandingProps) {
  const displayIcebreakers = icebreakers.slice(0, AGENT_ICEBREAKER_HOME_DISPLAY_COUNT);

  return (
    <section
      className={["mdc-chat-landing", "mdc-chat-agent-landing", className].filter(Boolean).join(" ")}
      aria-label={`Agente ${name}`}
    >
      <div className="mdc-chat-landing__avatar" aria-hidden="true">
        <ChatAgentIcon icon={icon} size={26} />
      </div>

      <h2 className="mdc-chat-landing__title">{name}</h2>

      {description ? <p className="mdc-chat-landing__description">{description}</p> : null}

      {canManageAgent && onManageAgent ? (
        <button type="button" className="mdc-chat-landing__manage" onClick={onManageAgent}>
          <Settings size={15} aria-hidden="true" />
          <span>Gerenciar agente</span>
        </button>
      ) : null}

      {displayIcebreakers.length > 0 ? (
        <div
          className="mdc-chat-landing__prompts mdc-chat-agent-landing__prompts"
          role="region"
          aria-label="Sugestões para começar"
        >
          {defaultIcebreakersHint ? (
            <p className="mdc-chat-agent-landing__prompts-hint">{defaultIcebreakersHint}</p>
          ) : null}

          {displayIcebreakers.map((icebreaker) => {
            const presentation = resolveIcebreakerCardPresentation(icebreaker);

            return (
              <button
                key={icebreaker}
                type="button"
                className="mdc-chat-landing__prompt"
                disabled={icebreakersDisabled}
                title={icebreaker}
                onClick={() => onIcebreakerClick?.(icebreaker)}
              >
                <strong>{presentation.title}</strong>
                {presentation.subtitle ? (
                  <>
                    {" "}
                    <span className="mdc-chat-landing__prompt-detail">{presentation.subtitle}</span>
                  </>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}

      {footer ? <div className="mdc-chat-agent-landing__footer">{footer}</div> : null}
    </section>
  );
}
