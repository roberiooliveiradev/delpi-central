import { MessageSquareText } from "lucide-react";

/** Already-authorized, presentation-only projection from the conversation owner. */
export type ConversationHistoryItemData = {
  id: string;
  title: string;
  active?: boolean;
};

export type ConversationHistoryItemProps = {
  item: ConversationHistoryItemData;
  /** Intent only; the consumer must check live authorization and load the session. */
  onSelect?: (id: string) => void;
  /** A pending or stale entry cannot trigger duplicate/invalid selections. */
  pending?: boolean;
  stale?: boolean;
  className?: string;
};

/**
 * Single conversation row. No menu is shown without an authorized actions
 * contract, and there are no implicit pin/rename/archive/delete operations.
 */
export function ConversationHistoryItem({
  item,
  onSelect,
  pending = false,
  stale = false,
  className,
}: ConversationHistoryItemProps) {
  const disabled = !onSelect || pending || stale;
  return (
    <button
      type="button"
      className={["delpi-ui-conversation-sidebar__history-item", "delpi-ui-conversation-history-item", className].filter(Boolean).join(" ")}
      aria-current={item.active ? "page" : undefined}
      aria-busy={pending || undefined}
      aria-label={item.title}
      title={item.title}
      disabled={disabled}
      onClick={() => {
        if (!disabled) onSelect?.(item.id);
      }}
    >
      <MessageSquareText size={16} strokeWidth={1.8} aria-hidden="true" />
      <span className="delpi-ui-conversation-history-item__title">{item.title}</span>
    </button>
  );
}
