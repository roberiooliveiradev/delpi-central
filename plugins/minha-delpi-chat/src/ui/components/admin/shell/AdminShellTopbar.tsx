import { ArrowLeft } from "lucide-react";

import type { AdminTab, AdminTabItem } from "./adminShellTypes";

import "./AdminShellTopbar.css";

type AdminShellTopbarProps = {
  activeTab: AdminTab;
  tabs: AdminTabItem[];
  isLoading: boolean;
  onRefresh: () => void;
  onBack: () => void;
  onTabChange: (tab: AdminTab) => void;
};

export function AdminShellTopbar({
  activeTab,
  tabs,
  isLoading,
  onRefresh,
  onBack,
  onTabChange,
}: AdminShellTopbarProps) {
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
        <small>Minha DELPI Chat</small>
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

      <nav
        className="mdc-admin-tabs mdc-chat-project-home__tabs"
        aria-label="Seções do admin"
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={activeTab === tab.key ? "is-active" : undefined}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
