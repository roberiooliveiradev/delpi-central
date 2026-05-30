import "./ChatFollowUpChips.css";

export type ChatFollowUpSuggestion = {
  label: string;
  query: string;
};

type ChatFollowUpChipsProps = {
  suggestions: ChatFollowUpSuggestion[];
  onUseSuggestion?: (query: string) => void;
};

export function ChatFollowUpChips({
  suggestions,
  onUseSuggestion,
}: ChatFollowUpChipsProps) {
  if (!onUseSuggestion || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-follow-up" role="group" aria-label="Próximos passos sugeridos">
      <p className="mdc-chat-follow-up__label">Próximos passos</p>
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
