import { ChevronLeft } from "lucide-react";

type ChatSidebarBrandProps = {
  onToggleCollapsed?: () => void;
};

export function ChatSidebarBrand({ onToggleCollapsed }: ChatSidebarBrandProps) {
  return (
    <div className="mdc-chat-sidebar__brand">
      <div>
        <strong>Minha DELPI</strong>
        <small>Chat corporativo</small>
      </div>

      <button
        type="button"
        className="mdc-chat-sidebar__collapse-button"
        onClick={onToggleCollapsed}
        aria-label="Recolher barra lateral"
        title="Recolher"
      >
        <ChevronLeft size={18} aria-hidden="true" />
      </button>
    </div>
  );
}
