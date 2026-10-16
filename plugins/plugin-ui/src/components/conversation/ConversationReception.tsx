import { useId } from "react";
import type { ReactNode } from "react";

/**
 * ConversationReception — empty-conversation welcome surface: assistant
 * avatar, optional greeting, title, description and a subordinate note.
 *
 * Render-only chrome: every value arrives already user-facing from the
 * consumer. It never fetches identity, never computes greetings, and
 * carries no Core/Keycloak/AuthZ/memory/capability knowledge.
 *
 * CSS: `styles/conversation-reception.css`
 * (`.delpi-ui-conversation-reception*`).
 */

export type ConversationReceptionDensity = "default" | "compact";

export type ConversationReceptionProps = {
  /** Assistant mark — decorative: the adjacent copy already identifies
   *  the assistant, so the slot is hidden from assistive tech. */
  avatar?: ReactNode;
  /** Optional personalized greeting rendered subordinate to the title. */
  greeting?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  /** Most-muted line, e.g. a persistence/privacy note. */
  note?: ReactNode;
  density?: ConversationReceptionDensity;
  className?: string;
};

export function ConversationReception({
  avatar,
  greeting,
  title,
  description,
  note,
  density = "default",
  className,
}: ConversationReceptionProps) {
  const titleId = useId();
  const densityClass =
    density === "compact"
      ? " delpi-ui-conversation-reception--compact"
      : "";

  return (
    <section
      className={`delpi-ui-conversation-reception${densityClass}${
        className ? ` ${className}` : ""
      }`}
      aria-labelledby={titleId}
    >
      {avatar ? (
        <div
          className="delpi-ui-conversation-reception__avatar"
          aria-hidden="true"
        >
          {avatar}
        </div>
      ) : null}
      {greeting ? (
        <p className="delpi-ui-conversation-reception__greeting">
          {greeting}
        </p>
      ) : null}
      <h2
        id={titleId}
        className="delpi-ui-conversation-reception__title"
      >
        {title}
      </h2>
      {description ? (
        <p className="delpi-ui-conversation-reception__description">
          {description}
        </p>
      ) : null}
      {note ? (
        <p className="delpi-ui-conversation-reception__note">{note}</p>
      ) : null}
    </section>
  );
}
