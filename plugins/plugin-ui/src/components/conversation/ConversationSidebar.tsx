import { MessageSquareText, Search, Settings2, SquarePen } from "lucide-react";
import { ConversationSidebarSearch } from "./ConversationSidebarSearch";

export type ConversationSidebarProps = {
  collapsed?: boolean;
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
  collapsed = false,
  onSearch,
  onOptions,
  history = [],
  onSelectConversation,
}: ConversationSidebarProps) {
  return (
    <div className={`delpi-ui-conversation-sidebar${collapsed ? " delpi-ui-conversation-sidebar--collapsed" : ""}`}>
      <button type="button" className="delpi-ui-conversation-sidebar__action delpi-ui-conversation-sidebar__action--primary"
        disabled={!onNewConversation} onClick={onNewConversation} aria-label="Nova conversa" title={!onNewConversation ? "Disponível após integração das sessões" : undefined}>
        <SquarePen size={17} aria-hidden="true" />{!collapsed ? <span>Nova conversa</span> : null}
      </button>
      {collapsed ? (
        <button className="delpi-ui-conversation-sidebar__action" type="button" aria-label="Pesquisar conversas" title="Pesquisar conversas" disabled={!onSearch} onClick={onSearch}><Search size={18} aria-hidden="true" /></button>
      ) : <ConversationSidebarSearch onOpenSearch={onSearch} />}
      {!collapsed ? <div className="delpi-ui-conversation-sidebar__section" aria-label="Conversas recentes">
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
      </div> : <div className="delpi-ui-conversation-sidebar__rail-spacer" />}
      <div className="delpi-ui-conversation-sidebar__bottom">
        <button type="button" className="delpi-ui-conversation-sidebar__action"
          disabled={!onOptions} onClick={onOptions} aria-label="Opções" title={!onOptions ? "Opções de conversa ainda indisponíveis" : undefined}>
          <Settings2 size={17} aria-hidden="true" />{!collapsed ? <span>Opções</span> : null}
        </button>
      </div>
    </div>
  );
}
