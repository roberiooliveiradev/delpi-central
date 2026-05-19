import { MessageSquarePlus, Search, X } from "lucide-react";
import type { RefObject } from "react";

import { buildChatHref } from "../../navigation/chatRoutes";

type ChatSidebarNavProps = {
  isSearchOpen: boolean;
  searchTerm: string;
  searchInputRef: RefObject<HTMLInputElement | null>;
  onNewSession: () => void;
  onToggleSearch: () => void;
  onClearSearch: () => void;
  onSearchChange: (value: string) => void;
};

export function ChatSidebarNav({
  isSearchOpen,
  searchTerm,
  searchInputRef,
  onNewSession,
  onToggleSearch,
  onClearSearch,
  onSearchChange,
}: ChatSidebarNavProps) {
  return (
    <>
      <nav className="mdc-chat-sidebar__nav" aria-label="Ações do chat">
        <a href={buildChatHref({ kind: "home" })} onClick={onNewSession}>
          <MessageSquarePlus size={17} aria-hidden="true" />
          <span>Nova conversa</span>
        </a>

        <button type="button" onClick={onToggleSearch}>
          <Search size={17} aria-hidden="true" />
          <span>Buscar conversas</span>
          <kbd>Ctrl K</kbd>
        </button>
      </nav>

      {isSearchOpen ? (
        <label className="mdc-chat-sidebar__search">
          <Search size={15} aria-hidden="true" />
          <input
            ref={searchInputRef}
            value={searchTerm}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar no histórico..."
          />
          {searchTerm ? (
            <button
              type="button"
              onClick={onClearSearch}
              aria-label="Limpar busca"
            >
              <X size={14} aria-hidden="true" />
            </button>
          ) : null}
        </label>
      ) : null}
    </>
  );
}
