import { useMemo } from "react";

import type { AssistantContextualHighlight } from "../../data/api/chatTypes";
import {
  resolveStarterQueryForFeature,
  type StarterInvokeContext,
} from "../chatShortcutPrompt";
import {
  pickEmptyStateGreeting,
  pickEmptyStateHint,
} from "../chatEmptyStateGreeting";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
  contextualHighlights?: AssistantContextualHighlight[];
  onUseStarter?: (query: string, context?: StarterInvokeContext) => void;
  onStartTour?: () => void;
};

export function ChatEmptyState({
  displayName,
  contextualHighlights = [],
  onUseStarter,
  onStartTour,
}: ChatEmptyStateProps) {
  const greeting = useMemo(() => pickEmptyStateGreeting(displayName), [displayName]);
  const hint = useMemo(() => pickEmptyStateHint(displayName), [displayName]);

  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero" data-tour="home-greeting">
        <h2 className="mdc-chat-empty-state__headline">
          <span className="mdc-chat-empty-state__headline-main">{greeting}</span>
        </h2>
        <p className="mdc-chat-empty-state__hint">{hint}</p>
        {onStartTour ? (
          <button
            type="button"
            className="mdc-chat-empty-state__tour-link"
            onClick={onStartTour}
          >
            Ver tour rápido do chat
          </button>
        ) : null}
      </div>

      {contextualHighlights.length > 0 ? (
        <div
          className="mdc-chat-empty-state__highlights"
          role="region"
          aria-label="Novidades do chat"
          data-tour="home-highlights"
        >
          <p className="mdc-chat-empty-state__highlights-label">Novidades</p>
          {contextualHighlights.slice(0, 2).map((highlight) => (
            <button
              key={highlight.featureId ?? highlight.title}
              type="button"
              className="mdc-chat-empty-state__highlight-chip"
              title={highlight.description}
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
                <span>{highlight.description}</span>
              ) : null}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
