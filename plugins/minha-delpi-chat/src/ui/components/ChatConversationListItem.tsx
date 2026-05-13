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
  onClick: () => void;
};

export function ChatConversationListItem({
  session,
  active,
  variant = "sidebar",
  leading,
  trailing,
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
    >
      {leading ? (
        <span className="mdc-chat-conversation-item__leading">{leading}</span>
      ) : null}

      <span className="mdc-chat-conversation-item__content">
        <strong>{session.title || "Conversa sem título"}</strong>
        <small>
          {session.context || "geral"}
          {date ? <> · {date}</> : null}
        </small>
      </span>

      {trailing ? (
        <span className="mdc-chat-conversation-item__trailing">{trailing}</span>
      ) : null}
    </button>
  );
}
