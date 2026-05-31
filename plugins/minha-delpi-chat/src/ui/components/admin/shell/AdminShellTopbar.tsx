import { ArrowLeft } from "lucide-react";

import {
  getAdminSectionItem,
  type AdminNavState,
  type AdminSection,
} from "../../../../navigation/adminNavigation";
import { AdminSectionNav } from "./AdminSectionNav";

import "./AdminShellTopbar.css";

type AdminShellTopbarProps = {
  nav: AdminNavState;
  isLoading: boolean;
  onRefresh: () => void;
  onBack: () => void;
  onSectionChange: (section: AdminSection) => void;
};

export function AdminShellTopbar({
  nav,
  isLoading,
  onRefresh,
  onBack,
  onSectionChange,
}: AdminShellTopbarProps) {
  const sectionMeta = getAdminSectionItem(nav.section);

  return (
    <header className="mdc-chat-ws-topbar mdc-admin-topbar" aria-label="Administração do chat">
      <div className="mdc-chat-ws-topbar__start">
        <button type="button" className="mdc-chat-ws-topbar__back" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar ao chat</span>
        </button>
      </div>

      <div className="mdc-chat-ws-topbar__title">
        <span>Administração</span>
        <small>{sectionMeta.label} — Minha DELPI Chat</small>
      </div>

      <div className="mdc-chat-ws-topbar__actions">
        <button
          type="button"
          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
          onClick={onRefresh}
          disabled={isLoading}
        >
          Atualizar
        </button>
      </div>

      <AdminSectionNav nav={nav} onNavigate={onSectionChange} />
    </header>
  );
}
