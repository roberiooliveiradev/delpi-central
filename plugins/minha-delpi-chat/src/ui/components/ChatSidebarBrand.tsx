import { ChevronLeft } from "lucide-react";
import type { ReactNode } from "react";

type ChatSidebarBrandProps = {
  onToggleCollapsed?: () => void;
  actions?: ReactNode;
};

export function ChatSidebarBrand({ onToggleCollapsed, actions }: ChatSidebarBrandProps) {
  return (
    <div className="mdc-chat-sidebar__brand">
      <div>
        <strong>Minha DELPI</strong>
        <small>Chat corporativo</small>
      </div>

      <div className="mdc-chat-sidebar__brand-actions">
        {actions}
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
    </div>
  );
}
