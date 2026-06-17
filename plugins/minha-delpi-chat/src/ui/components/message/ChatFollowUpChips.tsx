import "./ChatFollowUpChips.css";

export type ChatFollowUpSuggestion = {
  id?: string;
  label: string;
  query: string;
  icon?: string;
  group?: string;
  kind?: "primary" | "secondary" | "ghost" | "danger";
  tooltip?: string;
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
  disabledReason?: string;
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
        {suggestions.map((suggestion) => {
          const disabled = Boolean(suggestion.disabledReason);
          const className = [
            "mdc-chat-follow-up__chip",
            suggestion.kind === "primary" ? "mdc-chat-follow-up__chip--primary" : "",
            disabled ? "mdc-chat-follow-up__chip--disabled" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <button
              key={suggestion.id ?? `${suggestion.label}-${suggestion.query}`}
              type="button"
              className={className}
              disabled={disabled}
              title={suggestion.disabledReason ?? suggestion.tooltip ?? suggestion.label}
              aria-label={suggestion.label}
              onClick={() => {
                if (!disabled) {
                  onUseSuggestion(suggestion.query);
                }
              }}
            >
              {suggestion.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
