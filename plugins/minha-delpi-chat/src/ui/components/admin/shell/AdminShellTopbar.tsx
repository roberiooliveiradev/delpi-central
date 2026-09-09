import { HintAction } from "@delpi/plugin-ui/index";
import { ArrowLeft, RefreshCw } from "lucide-react";

import { getAdminNavBreadcrumb } from "../../../../navigation/adminNavTree";
import type { AdminNavState } from "../../../../navigation/adminNavigation";
import { ADMIN_SHELL_REVISION } from "./adminShellRevision";
import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import "./AdminShellTopbar.css";

type AdminShellTopbarProps = {
  nav: AdminNavState;
  isLoading: boolean;
  onRefresh: () => void;
  onBack: () => void;
};

export function AdminShellTopbar({ nav, isLoading, onRefresh, onBack }: AdminShellTopbarProps) {
  const breadcrumb = getAdminNavBreadcrumb(nav);

  return (
    <header className="mdc-chat-ws-topbar mdc-admin-topbar" aria-label="Administração do chat">
      <div className="mdc-chat-ws-topbar__start">
        <HintAction
          hint={ADMIN_HELP.shell.backToChat}
          ariaLabel="Ajuda: Voltar ao chat"
        >
          <button type="button" className="mdc-chat-ws-topbar__back" onClick={onBack}>
            <ArrowLeft size={18} aria-hidden="true" />
            <span>Voltar ao chat</span>
          </button>
        </HintAction>
      </div>

      <div className="mdc-chat-ws-topbar__title">
        <span>Administração</span>
        <small>
          {breadcrumb} — Minha DELPI Chat ·{" "}
          <span className="mdc-admin-shell-revision" title="Versão do painel admin">
            {ADMIN_SHELL_REVISION}
          </span>
        </small>
      </div>

      <div className="mdc-chat-ws-topbar__actions">
        <HintAction hint={ADMIN_HELP.shell.refresh} ariaLabel="Ajuda: Atualizar dados do admin">
          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
            onClick={onRefresh}
            disabled={isLoading}
            aria-label={isLoading ? "Atualizando dados do admin" : "Atualizar dados do admin"}
          >
            <RefreshCw
              size={16}
              aria-hidden="true"
              className={isLoading ? "mdc-admin-topbar__refresh-icon--spinning" : undefined}
            />
            <span>{isLoading ? "Atualizando..." : "Atualizar"}</span>
          </button>
        </HintAction>
      </div>
    </header>
  );
}
