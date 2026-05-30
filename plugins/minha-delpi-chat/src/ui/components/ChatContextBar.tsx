import { X } from "lucide-react";
import "./ChatContextBar.css";

export type ChatContextChip = {
  label: string;
  kind: string;
  value: string;
};

type ChatContextBarProps = {
  chips: ChatContextChip[];
  onClearContext?: () => void;
};

export function ChatContextBar({ chips, onClearContext }: ChatContextBarProps) {
  if (!chips.length) {
    return null;
  }

  return (
    <div className="mdc-chat-context-bar" aria-label="Contexto ativo da conversa">
      <span className="mdc-chat-context-bar__title">Contexto ativo</span>
      <div className="mdc-chat-context-bar__chips">
        {chips.map((chip) => (
          <span key={`${chip.kind}-${chip.value}`} className="mdc-chat-context-bar__chip">
            {chip.label}
          </span>
        ))}
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
