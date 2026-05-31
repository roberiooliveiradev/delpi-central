import { ArrowRight, Sparkles, X } from "lucide-react";
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

  const interactive = Boolean(onChipAction);

  return (
    <div className="mdc-chat-context-bar" aria-label="Contexto ativo da conversa">
      <div className="mdc-chat-context-bar__header">
        <div className="mdc-chat-context-bar__heading">
          <Sparkles size={14} aria-hidden="true" className="mdc-chat-context-bar__icon" />
          <span className="mdc-chat-context-bar__title">Contexto ativo</span>
          {interactive ? (
            <span className="mdc-chat-context-bar__hint">Toque para consultar</span>
          ) : null}
        </div>

        {onClearContext ? (
          <button
            type="button"
            className="mdc-chat-context-bar__clear"
            onClick={onClearContext}
            title="Limpar preferências de contexto"
            aria-label="Limpar contexto ativo"
          >
            <X size={14} aria-hidden="true" />
            <span className="mdc-chat-context-bar__clear-label">Limpar</span>
          </button>
        ) : null}
      </div>

      <div className="mdc-chat-context-bar__chips" role="list">
        {chips.map((chip) => {
          const chipKey = `${chip.kind}-${chip.value}`;
          const query = interactive ? buildContextChipQuery(chip) : null;
          const isActionable = interactive && Boolean(query);

          if (isActionable) {
            return (
              <button
                key={chipKey}
                type="button"
                role="listitem"
                className="mdc-chat-context-bar__chip mdc-chat-context-bar__chip--action"
                title={`Consultar: ${chip.label}`}
                onClick={() => onChipAction?.(query!)}
              >
                <span className="mdc-chat-context-bar__chip-text">{chip.label}</span>
                <ArrowRight size={13} aria-hidden="true" className="mdc-chat-context-bar__chip-arrow" />
              </button>
            );
          }

          return (
            <span key={chipKey} role="listitem" className="mdc-chat-context-bar__chip">
              {chip.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
