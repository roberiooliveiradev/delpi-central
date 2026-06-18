import type { ComposerMentionCandidate } from "../../../state/chatComposerMention";
import { ChatAgentIcon } from "../workspace/ChatAgentIcon";
import { ChatProjectIcon } from "../workspace/ChatProjectIcon";

import "./ChatComposerMentionMenu.css";

type ChatComposerMentionMenuProps = {
  items: ComposerMentionCandidate[];
  activeIndex: number;
  onSelect: (candidate: ComposerMentionCandidate) => void;
  onHover?: (index: number) => void;
  variant?: "inline" | "portal";
};

export function ChatComposerMentionMenu({
  items,
  activeIndex,
  onSelect,
  onHover,
  variant = "portal",
}: ChatComposerMentionMenuProps) {
  const menuClassName =
    variant === "portal"
      ? "mdc-chat-composer-mention-menu__list"
      : "mdc-chat-composer-mention-menu";

  if (items.length === 0) {
    return (
      <div className={menuClassName} role="listbox" aria-label="Menções">
        <p className="mdc-chat-composer-mention-menu__empty">Nenhum agente ou projeto encontrado</p>
      </div>
    );
  }

  return (
    <div className={menuClassName} role="listbox" aria-label="Menções">
      {items.map((item, index) => (
        <button
          key={`${item.kind}-${item.id}`}
          type="button"
          role="option"
          aria-selected={index === activeIndex}
          aria-label={`${item.name} (${item.kind === "agent" ? "Agente" : "Projeto"})`}
          className={[
            "mdc-chat-composer-mention-menu__item",
            item.kind === "agent"
              ? "mdc-chat-composer-mention-menu__item--agent"
              : "mdc-chat-composer-mention-menu__item--project",
            index === activeIndex ? "mdc-chat-composer-mention-menu__item--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          onMouseDown={(event) => {
            event.preventDefault();
          }}
          onMouseEnter={() => onHover?.(index)}
          onClick={() => onSelect(item)}
        >
          <span className="mdc-chat-composer-mention-menu__icon" aria-hidden="true">
            {item.kind === "agent" ? (
              <ChatAgentIcon icon={item.icon} size={13} />
            ) : (
              <ChatProjectIcon icon={item.icon} size={13} />
            )}
          </span>
          <span className="mdc-chat-composer-mention-menu__label">{item.name}</span>
        </button>
      ))}
    </div>
  );
}
