import { X } from "lucide-react";
import { buildContextChipQuery } from "./chatContextChipActions";
import "./ChatContextBar.css";

export type ChatContextChip = {
  label: string;
  kind: string;
  value: string;
};

type ChatContextBarProps = {
  chips: ChatContextChip[];
  onClearContext?: () => void;
  onChipAction?: (query: string) => void;
};

export function ChatContextBar({ chips, onClearContext, onChipAction }: ChatContextBarProps) {
  if (!chips.length) {
    return null;
  }

  return (
    <div className="mdc-chat-context-bar" aria-label="Contexto ativo da conversa">
      <span className="mdc-chat-context-bar__title">Contexto ativo</span>
      <div className="mdc-chat-context-bar__chips">
        {chips.map((chip) => {
          const chipKey = `${chip.kind}-${chip.value}`;

          if (onChipAction) {
            return (
              <button
                key={chipKey}
                type="button"
                className="mdc-chat-context-bar__chip mdc-chat-context-bar__chip--action"
                title={`Usar contexto: ${chip.label}`}
                onClick={() => {
                  const query = buildContextChipQuery(chip);

                  if (query) {
                    onChipAction(query);
                  }
                }}
              >
                {chip.label}
              </button>
            );
          }

          return (
            <span key={chipKey} className="mdc-chat-context-bar__chip">
              {chip.label}
            </span>
          );
        })}
      </div>
      {onClearContext ? (
        <button
          type="button"
          className="mdc-chat-context-bar__clear"
          onClick={onClearContext}
          title="Limpar preferências de contexto"
        >
          <X size={14} aria-hidden="true" />
          Limpar
        </button>
      ) : null}
    </div>
  );
}
