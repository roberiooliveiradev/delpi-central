import { ChevronLeft, X } from "lucide-react";

type ChatSidebarBrandProps = {
  onToggleCollapsed?: () => void;
  onCloseMobile?: () => void;
};

export function ChatSidebarBrand({
  onToggleCollapsed,
  onCloseMobile,
}: ChatSidebarBrandProps) {
  return (
    <div className="mdc-chat-sidebar__brand">
      <div>
        <strong>Minha DELPI</strong>
        <small>Chat corporativo</small>
      </div>

      <div className="mdc-chat-sidebar__brand-actions">
        {onCloseMobile ? (
          <button
            type="button"
            className="mdc-chat-sidebar__close-mobile mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
            onClick={onCloseMobile}
            aria-label="Fechar menu"
            title="Fechar"
          >
            <X size={18} aria-hidden="true" />
          </button>
        ) : null}
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
