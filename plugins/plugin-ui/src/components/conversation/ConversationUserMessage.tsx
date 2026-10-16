import type { ReactNode } from "react";

export type ConversationUserMessageDensity = "comfortable" | "compact";

export type ConversationUserMessageProps = {
  /** Already-resolved message content. React text is escaped; no parsing. */
  children: ReactNode;
  /** Presentation-only avatar supplied by the consumer (no identity lookup). */
  avatar?: ReactNode;
  /** Visible author supplied by the consumer, never inferred by the kit. */
  authorLabel?: ReactNode;
  density?: ConversationUserMessageDensity;
  className?: string;
  contentClassName?: string;
};

/**
 * Right-aligned user turn chrome for conversation surfaces.
 * This is not a timeline, identity resolver, authorization boundary or
 * live region. The consumer owns turn data, speaker and ordering.
 */
export function ConversationUserMessage({
  children,
  avatar,
  authorLabel,
  density = "comfortable",
  className,
  contentClassName,
}: ConversationUserMessageProps) {
  const rootClass = [
    "delpi-ui-conversation-user-message",
    density === "compact" ? "delpi-ui-conversation-user-message--compact" : null,
    className,
  ].filter(Boolean).join(" ");
  const textClass = [
    "delpi-ui-conversation-user-message__content",
    contentClassName,
  ].filter(Boolean).join(" ");

  return (
    <div className={rootClass}>
      {avatar != null ? (
        <span
          className="delpi-ui-conversation-user-message__avatar"
          aria-hidden={authorLabel != null ? true : undefined}
        >
          {avatar}
        </span>
      ) : null}
      <div className="delpi-ui-conversation-user-message__bubble">
        {authorLabel != null ? (
          <span className="delpi-ui-conversation-user-message__author">
            {authorLabel}
          </span>
        ) : null}
        <div className={textClass}>{children}</div>
      </div>
    </div>
  );
}
