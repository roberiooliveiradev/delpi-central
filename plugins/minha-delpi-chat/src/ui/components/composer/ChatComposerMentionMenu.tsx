import { Bot, Folder } from "lucide-react";

import type { ComposerMentionCandidate } from "../../../state/chatComposerMention";

import "./ChatComposerMentionMenu.css";

type ChatComposerMentionMenuProps = {
  items: ComposerMentionCandidate[];
  activeIndex: number;
  onSelect: (candidate: ComposerMentionCandidate) => void;
  onHover?: (index: number) => void;
};

export function ChatComposerMentionMenu({
  items,
  activeIndex,
  onSelect,
  onHover,
}: ChatComposerMentionMenuProps) {
  if (items.length === 0) {
    return (
      <div className="mdc-chat-composer-mention-menu" role="listbox" aria-label="Menções">
        <p className="mdc-chat-composer-mention-menu__empty">Nenhum agente ou projeto encontrado</p>
      </div>
    );
  }

  return (
    <div className="mdc-chat-composer-mention-menu" role="listbox" aria-label="Menções">
      <p className="mdc-chat-composer-mention-menu__hint">Use @ para citar agente ou projeto no turno</p>

      {items.map((item, index) => (
        <button
          key={`${item.kind}-${item.id}`}
          type="button"
          role="option"
          aria-selected={index === activeIndex}
          className={
            index === activeIndex
              ? "mdc-chat-composer-mention-menu__item mdc-chat-composer-mention-menu__item--active"
              : "mdc-chat-composer-mention-menu__item"
          }
          onMouseDown={(event) => {
            event.preventDefault();
          }}
          onMouseEnter={() => onHover?.(index)}
          onClick={() => onSelect(item)}
        >
          {item.kind === "agent" ? (
            <Bot size={15} aria-hidden="true" />
          ) : (
            <Folder size={15} aria-hidden="true" />
          )}
          <span>{item.name}</span>
          <small>{item.kind === "agent" ? "Agente" : "Projeto"}</small>
        </button>
      ))}
    </div>
  );
}
