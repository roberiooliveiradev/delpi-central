import { ChevronLeft, X } from "lucide-react";

type ChatSidebarBrandProps = {
  /**
   * Sidebar em modo gaveta (mobile ou chat embarcado): a única ação possível é
   * fechar. O rail colapsado não existe nesse layout.
   */
  isDrawer?: boolean;
  onToggleCollapsed?: () => void;
  onCloseMobile?: () => void;
};

export function ChatSidebarBrand({
  isDrawer = false,
  onToggleCollapsed,
  onCloseMobile,
}: ChatSidebarBrandProps) {
  const className = [
    "mdc-chat-sidebar__brand",
    isDrawer ? "mdc-chat-sidebar__brand--drawer" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
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
        {!isDrawer ? (
          <button
            type="button"
            className="mdc-chat-sidebar__collapse-button"
            onClick={onToggleCollapsed}
            aria-label="Recolher barra lateral"
            title="Recolher"
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
