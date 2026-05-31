import "./ChatFollowUpChips.css";

export type ChatFollowUpSuggestion = {
  label: string;
  query: string;
};

type ChatFollowUpChipsProps = {
  suggestions: ChatFollowUpSuggestion[];
  onUseSuggestion?: (query: string) => void;
  groupLabel?: string;
  ariaLabel?: string;
};

export function ChatFollowUpChips({
  suggestions,
  onUseSuggestion,
  groupLabel = "Próximos passos",
  ariaLabel,
}: ChatFollowUpChipsProps) {
  if (!onUseSuggestion || suggestions.length === 0) {
    return null;
  }

  return (
    <div
      className="mdc-chat-follow-up"
      role="group"
      aria-label={ariaLabel ?? `${groupLabel} sugeridos`}
    >
      <p className="mdc-chat-follow-up__label">{groupLabel}</p>
      <div className="mdc-chat-follow-up__chips">
        {suggestions.map((suggestion) => (
          <button
            key={`${suggestion.label}-${suggestion.query}`}
            type="button"
            className="mdc-chat-follow-up__chip"
            onClick={() => onUseSuggestion(suggestion.query)}
          >
            {suggestion.label}
          </button>
        ))}
      </div>
    </div>
  );
}
