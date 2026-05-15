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
    <header className="mdc-admin-topbar">
      <div className="mdc-admin-topbar__content">
        <div>
          <p className="mdc-chat-eyebrow">Administração</p>
          <h1>Minha DELPI Chat</h1>
          <p>
            Curadoria da base global, diretrizes, ferramentas e auditoria operacional.
          </p>
        </div>

        <div className="mdc-admin-topbar__actions">
          <button type="button" onClick={onRefresh} disabled={isLoading}>
            Atualizar
          </button>
          <button type="button" onClick={onBack}>
            Voltar ao chat
          </button>
        </div>
      </div>

      <nav className="mdc-admin-tabs" aria-label="Administração do chat">
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
