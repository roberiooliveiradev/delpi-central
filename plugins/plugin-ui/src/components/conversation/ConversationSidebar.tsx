import { Search } from "lucide-react";
import { NavigationActions } from "./NavigationActions";
import { ConversationHistoryItem } from "./ConversationHistoryItem";
import { PinnedConversations } from "./PinnedConversations";
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
  /** Authorized and explicitly grouped sessions from the backend owner. */
  pinnedHistory?: readonly { id: string; title: string; active?: boolean }[];
  olderHistory?: readonly { id: string; title: string; active?: boolean }[];
  /** Set only after the history owner confirmed an authorized empty response. */
  historyStatus?: "unavailable" | "ready" | "loading" | "authorized_empty" | "error";
  onSelectConversation?: (id: string) => void;
};

/** Render-only conversation navigation: never creates local history or an API. */
export function ConversationSidebar({
  onNewConversation,
  collapsed = false,
  onSearch,
  onOptions,
  history = [],
  pinnedHistory = [],
  olderHistory = [],
  historyStatus,
  onSelectConversation,
}: ConversationSidebarProps) {
  // Backward compatible with legitimate host-provided history arrays.
  const effectiveHistoryStatus = historyStatus ??
    (onSelectConversation && (history.length > 0 || pinnedHistory.length > 0 || olderHistory.length > 0)
      ? "ready" : "unavailable");
  return (
    <div className={`delpi-ui-conversation-sidebar${collapsed ? " delpi-ui-conversation-sidebar--collapsed" : ""}`}>
      <NavigationActions action="new" collapsed={collapsed} onAction={onNewConversation} />
      {collapsed ? (
        <button className="delpi-ui-conversation-sidebar__action" type="button" aria-label="Pesquisar conversas" title="Pesquisar conversas" disabled={!onSearch} onClick={onSearch}><Search size={18} aria-hidden="true" /></button>
      ) : <ConversationSidebarSearch onOpenSearch={onSearch} />}
      {!collapsed ? <div className="delpi-ui-conversation-sidebar__section" aria-label="Histórico de conversas">
        {effectiveHistoryStatus === "ready" && onSelectConversation ? (
          <>
            <PinnedConversations items={pinnedHistory} onSelectConversation={onSelectConversation} />
            {([
              ["Recentes", history],
              ["Anteriores", olderHistory],
            ] as const).map(([heading, items]) => items.length > 0 ? (
              <section className="delpi-ui-conversation-sidebar__group" aria-label={heading} key={heading}>
                <h2 className="delpi-ui-conversation-sidebar__section-heading">{heading}</h2>
                <ul className="delpi-ui-conversation-sidebar__history">
                  {items.map((item) => (
                    <li key={item.id}>
                      <ConversationHistoryItem item={item} onSelect={onSelectConversation} />
                    </li>
                  ))}
                </ul>
              </section>
            ) : null)}
          </>
        ) : null}
        {effectiveHistoryStatus === "unavailable" ? (
          <>
            <h2 className="delpi-ui-conversation-sidebar__section-heading">Recentes</h2>
            <p className="delpi-ui-conversation-sidebar__empty">O histórico estará disponível quando as conversas forem persistidas.</p>
          </>
        ) : effectiveHistoryStatus === "loading" ? (
          <p className="delpi-ui-conversation-sidebar__empty" role="status">Carregando conversas…</p>
        ) : effectiveHistoryStatus === "authorized_empty" ? (
          <p className="delpi-ui-conversation-sidebar__empty">Nenhuma conversa encontrada.</p>
        ) : effectiveHistoryStatus === "error" ? (
          <p className="delpi-ui-conversation-sidebar__empty" role="alert">Não foi possível carregar as conversas.</p>
        ) : null}
      </div> : <div className="delpi-ui-conversation-sidebar__rail-spacer" />}
      <div className="delpi-ui-conversation-sidebar__bottom">
        <NavigationActions action="options" collapsed={collapsed} onAction={onOptions} />
      </div>
    </div>
  );
}
