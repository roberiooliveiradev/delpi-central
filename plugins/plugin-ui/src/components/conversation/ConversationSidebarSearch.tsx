import { Search } from "lucide-react";

/** Entry point only; query/results require an authorized backend search contract. */
export type ConversationSidebarSearchProps = {
  onOpenSearch?: () => void;
};

export function ConversationSidebarSearch({ onOpenSearch }: ConversationSidebarSearchProps) {
  return (
    <div className="delpi-ui-conversation-sidebar__search">
      <Search size={16} aria-hidden="true" />
      <button
        type="button"
        disabled={!onOpenSearch}
        onClick={onOpenSearch}
        title={!onOpenSearch ? "Pesquisa disponível após integração do histórico" : undefined}
      >
        Pesquisar conversas
      </button>
    </div>
  );
}
