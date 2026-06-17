import { Bot } from "lucide-react";
import { useMemo } from "react";

import type { AssistantContextualHighlight } from "../../../data/api/chatTypes";
import { formatIcebreakerForDisplay } from "../../agentIcebreakers";
import { CHAT_OPERATIONAL_HOME_STARTERS } from "../../chatHomeStarters";
import {
  resolveStarterQueryForFeature,
  type StarterInvokeContext,
} from "../../chatShortcutPrompt";
import {
  pickEmptyStateGreeting,
  pickEmptyStateHint,
} from "../../chatEmptyStateGreeting";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
  contextualHighlights?: AssistantContextualHighlight[];
  onUseStarter?: (query: string, context?: StarterInvokeContext) => void;
  onStartTour?: () => void;
};

const DEFAULT_HOME_STARTERS = CHAT_OPERATIONAL_HOME_STARTERS.slice(0, 3);

export function ChatEmptyState({
  displayName,
  contextualHighlights = [],
  onUseStarter,
  onStartTour,
}: ChatEmptyStateProps) {
  const greeting = useMemo(() => pickEmptyStateGreeting(displayName), [displayName]);
  const hint = useMemo(() => pickEmptyStateHint(displayName), [displayName]);
  const showHighlights = contextualHighlights.length > 0;

  return (
    <section className="mdc-chat-landing mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-landing__avatar" aria-hidden="true" data-tour="home-greeting">
        <Bot size={26} />
      </div>

      <h2 className="mdc-chat-landing__title">{greeting}</h2>
      <p className="mdc-chat-landing__description">{hint}</p>

      {onStartTour ? (
        <button type="button" className="mdc-chat-landing__secondary-link" onClick={onStartTour}>
          Ver tour rápido do chat
        </button>
      ) : null}

      {showHighlights ? (
        <div
          className="mdc-chat-landing__prompts"
          role="region"
          aria-label="Novidades do chat"
          data-tour="home-highlights"
        >
          {contextualHighlights.slice(0, 3).map((highlight) => (
            <button
              key={highlight.featureId ?? highlight.title}
              type="button"
              className="mdc-chat-landing__prompt"
              title={highlight.description ?? highlight.title}
              onClick={() => {
                const query = resolveStarterQueryForFeature(highlight.exampleQuery, {
                  featureId: highlight.featureId,
                });

                if (query) {
                  onUseStarter?.(query, { featureId: highlight.featureId });
                }
              }}
            >
              <strong>{highlight.title}</strong>
              {highlight.description ? (
                <>
                  {" "}
                  <span className="mdc-chat-landing__prompt-detail">{highlight.description}</span>
                </>
              ) : null}
            </button>
          ))}
        </div>
      ) : (
        <div className="mdc-chat-landing__prompts" role="region" aria-label="Sugestões para começar">
          {DEFAULT_HOME_STARTERS.map((starter) => (
            <button
              key={starter.query}
              type="button"
              className="mdc-chat-landing__prompt"
              title={starter.query}
              onClick={() => onUseStarter?.(starter.query, { starterId: starter.label })}
            >
              {formatIcebreakerForDisplay(starter.query)}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
