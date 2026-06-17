import type {
  ChatFollowUpSuggestion,
  ChatGuidedFlow,
  ChatGuidedFlowCard,
} from "../../../data/api/chatTypes";
import { ChatFollowUpChips } from "./ChatFollowUpChips";
import { ChatMarkdown } from "./ChatMarkdown";

import "./ChatGuidedFlowBlock.css";

type ChatGuidedFlowBlockProps = {
  flow?: ChatGuidedFlow | null;
  cards?: ChatGuidedFlowCard[];
  suggestions?: ChatFollowUpSuggestion[];
  onUseQuery?: (query: string) => void;
};

export function ChatGuidedFlowBlock({
  flow,
  cards,
  suggestions = [],
  onUseQuery,
}: ChatGuidedFlowBlockProps) {
  if (!flow && (!cards || cards.length === 0) && suggestions.length === 0) {
    return null;
  }

  return (
    <div className="mdc-guided-flow-block">
      {flow ? (
        <section className="mdc-guided-flow-block__flow" aria-label={flow.title}>
          <h4 className="mdc-guided-flow-block__title">{flow.title}</h4>
          {flow.intro ? (
            <div className="mdc-guided-flow-block__intro">
              <ChatMarkdown content={flow.intro} compact />
            </div>
          ) : null}
          <ol className="mdc-guided-flow-block__steps">
            {(flow.steps ?? []).map((step) => (
              <li key={step.order}>
                <span className="mdc-guided-flow-block__step-text">
                  <ChatMarkdown content={step.text} compact />
                </span>
                {step.suggestion && onUseQuery ? (
                  <button
                    type="button"
                    className="mdc-guided-flow-block__step-action"
                    onClick={() => onUseQuery(step.suggestion!.query)}
                  >
                    {step.suggestion.label}
                  </button>
                ) : null}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {cards && cards.length > 0 ? (
        <div className="mdc-guided-flow-block__cards" role="list">
          {cards.map((card) => (
            <article key={card.title} className="mdc-guided-flow-block__card" role="listitem">
              <h4>{card.title}</h4>
              {card.description ? (
                <div className="mdc-guided-flow-block__card-description">
                  <ChatMarkdown content={card.description} compact />
                </div>
              ) : null}
              {card.suggestions?.length && onUseQuery ? (
                <div className="mdc-guided-flow-block__card-actions">
                  {card.suggestions.map((item) => (
                    <button
                      key={`${item.label}-${item.query}`}
                      type="button"
                      className="mdc-chat-follow-up__chip"
                      onClick={() => onUseQuery(item.query)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}

      <ChatFollowUpChips
        suggestions={suggestions}
        onUseSuggestion={onUseQuery}
        groupLabel="Fluxo guiado"
        ariaLabel="Ações do fluxo guiado"
      />
    </div>
  );
}
