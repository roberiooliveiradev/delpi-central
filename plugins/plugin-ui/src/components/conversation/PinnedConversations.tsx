import { ConversationHistoryItem } from "./ConversationHistoryItem";
import type { ConversationHistoryItemData } from "./ConversationHistoryItem";

export type PinnedConversationsProps = {
  /** Only entries explicitly confirmed as pinned by the authoritative owner. */
  items: readonly ConversationHistoryItemData[];
  /** Selection intent, not authorization. */
  onSelectConversation?: (id: string) => void;
  className?: string;
};

/**
 * Read-only pinned group; cannot pin/unpin or infer pin state locally.
 * No empty label when there is no confirmed pinned item or selection contract.
 */
export function PinnedConversations({ items, onSelectConversation, className }: PinnedConversationsProps) {
  if (!onSelectConversation || items.length === 0) return null;

  return (
    <section className={["delpi-ui-conversation-sidebar__group", "delpi-ui-pinned-conversations", className].filter(Boolean).join(" ")} aria-label="Fixadas">
      <h2 className="delpi-ui-conversation-sidebar__section-heading">Fixadas</h2>
      <ul className="delpi-ui-conversation-sidebar__history">
        {items.map(item => (
          <li key={item.id}>
            <ConversationHistoryItem item={item} onSelect={onSelectConversation} />
          </li>
        ))}
      </ul>
    </section>
  );
}
