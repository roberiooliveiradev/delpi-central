import type { UserTurnContextChip } from "../../../state/chatComposerContext";
import { ChatAgentIcon } from "../workspace/ChatAgentIcon";
import { ChatProjectIcon } from "../workspace/ChatProjectIcon";

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
            <ChatAgentIcon icon={chip.icon} size={13} />
          ) : (
            <ChatProjectIcon icon={chip.icon} size={13} />
          )}
          <span>{chip.name}</span>
        </span>
      ))}
    </div>
  );
}
