import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import type { ChatSession } from "../../data/api/chatTypes";
import { formatSessionDate } from "./chatSidebarUtils";

import "./ChatConversationListItem.css";

type ChatConversationListItemVariant = "sidebar" | "project" | "home";

type ChatConversationListItemProps = {
  session: ChatSession;
  active?: boolean;
  variant?: ChatConversationListItemVariant;
  leading?: ReactNode;
  trailing?: ReactNode;
  isProcessing?: boolean;
  onClick: () => void;
};

export function ChatConversationListItem({
  session,
  active,
  variant = "sidebar",
  leading,
  trailing,
  isProcessing = false,
  onClick,
}: ChatConversationListItemProps) {
  const date = formatSessionDate(session.updated_at);

  return (
    <button
      type="button"
      className={[
        "mdc-chat-conversation-item",
        `mdc-chat-conversation-item--${variant}`,
        active ? "mdc-chat-conversation-item--active" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={onClick}
      aria-busy={isProcessing || undefined}
      title={isProcessing ? "Gerando resposta..." : undefined}
    >
      {leading ? (
        <span className="mdc-chat-conversation-item__leading">{leading}</span>
      ) : null}

      <span className="mdc-chat-conversation-item__content">
        <strong>{session.title || "Conversa sem título"}</strong>
        {date ? <small>{date}</small> : null}
      </span>

      {trailing || isProcessing ? (
        <span className="mdc-chat-conversation-item__trailing">
          {isProcessing ? (
            <Loader2
              size={14}
              className="mdc-chat-conversation-item__spinner"
              aria-hidden="true"
            />
          ) : null}
          {trailing}
        </span>
      ) : null}
    </button>
  );
}
