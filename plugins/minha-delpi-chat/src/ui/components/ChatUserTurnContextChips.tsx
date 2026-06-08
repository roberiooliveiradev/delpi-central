import { Bot, Folder } from "lucide-react";

import type { UserTurnContextChip } from "../../state/chatComposerContext";

import "./ChatUserTurnContextChips.css";

type ChatUserTurnContextChipsProps = {
  chips: UserTurnContextChip[];
};

export function ChatUserTurnContextChips({ chips }: ChatUserTurnContextChipsProps) {
  if (chips.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-user-turn-context" aria-label="Contexto do turno">
      {chips.map((chip) => (
        <span
          key={`${chip.kind}-${chip.id}`}
          className={`mdc-chat-user-turn-context__chip mdc-chat-user-turn-context__chip--${chip.kind}`}
        >
          {chip.kind === "agent" ? (
            <Bot size={13} aria-hidden="true" />
          ) : (
            <Folder size={13} aria-hidden="true" />
          )}
          <span>{chip.name}</span>
        </span>
      ))}
    </div>
  );
}
