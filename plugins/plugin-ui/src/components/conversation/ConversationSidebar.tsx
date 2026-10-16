import { MessageSquareText, Settings2, SquarePen } from "lucide-react";
import { ConversationSidebarSearch } from "./ConversationSidebarSearch";

export type ConversationSidebarProps = {
  /** Only enable after a real, authorized session creation flow exists. */
  onNewConversation?: () => void;
  /** Only enable after persisted backend history search is contracted. */
  onSearch?: () => void;
  /** Only enable for implemented application-level conversation options. */
  onOptions?: () => void;
  /** Real authorized conversation items, if supplied by the host. */
  history?: readonly { id: string; title: string; active?: boolean }[];
  onSelectConversation?: (id: string) => void;
};

/** Render-only conversation navigation: never creates local history or an API. */
export function ConversationSidebar({
  onNewConversation,
  onSearch,
  onOptions,
  history = [],
  onSelectConversation,
}: ConversationSidebarProps) {
  return (
    <div className="delpi-ui-conversation-sidebar">
      <button type="button" className="delpi-ui-conversation-sidebar__action delpi-ui-conversation-sidebar__action--primary"
        disabled={!onNewConversation} onClick={onNewConversation} title={!onNewConversation ? "Disponível após integração das sessões" : undefined}>
        <SquarePen size={17} aria-hidden="true" /><span>Nova conversa</span>
      </button>
      <ConversationSidebarSearch onOpenSearch={onSearch} />
      <div className="delpi-ui-conversation-sidebar__section" aria-label="Conversas recentes">
        <h2 className="delpi-ui-conversation-sidebar__section-heading">Recentes</h2>
        {history.length > 0 && onSelectConversation ? (
          <ul className="delpi-ui-conversation-sidebar__history">
            {history.map((item) => (
              <li key={item.id}>
                <button type="button" aria-current={item.active ? "page" : undefined}
                  className="delpi-ui-conversation-sidebar__history-item"
                  onClick={() => onSelectConversation(item.id)}>
                  <MessageSquareText size={16} aria-hidden="true" />
                  <span title={item.title}>{item.title}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="delpi-ui-conversation-sidebar__empty">
            O histórico estará disponível quando as conversas forem persistidas.
          </p>
        )}
      </div>
      <div className="delpi-ui-conversation-sidebar__bottom">
        <button type="button" className="delpi-ui-conversation-sidebar__action"
          disabled={!onOptions} onClick={onOptions} title={!onOptions ? "Opções de conversa ainda indisponíveis" : undefined}>
          <Settings2 size={17} aria-hidden="true" /><span>Opções</span>
        </button>
      </div>
    </div>
  );
}
