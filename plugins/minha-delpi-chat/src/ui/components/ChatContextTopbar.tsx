import {
  Bot,
  Folder,
  MessageSquare,
  MoreHorizontal,
  Pencil,
  Settings,
  Trash2,
  X,
} from "lucide-react";
import { useState } from "react";

import "./ChatContextTopbar.css";

type ChatContextTopbarMode = "general" | "project" | "agent";

type ChatContextTopbarProps = {
  mode: ChatContextTopbarMode;
  title: string;
  subtitle?: string;
  badge?: string;
  onOpenAdmin?: () => void;
  onRenameProject?: () => void;
  onOpenProjectSettings?: () => void;
  onDeleteProject?: () => void;
  onManageAgents?: () => void;
  onClearAgent?: () => void;
};

export function ChatContextTopbar({
  mode,
  title,
  subtitle,
  badge,
  onOpenAdmin,
  onRenameProject,
  onOpenProjectSettings,
  onDeleteProject,
  onManageAgents,
  onClearAgent,
}: ChatContextTopbarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const Icon =
    mode === "project" ? Folder : mode === "agent" ? Bot : MessageSquare;

  return (
    <header className="mdc-chat-context-topbar">
      <div className="mdc-chat-context-topbar__identity">
        <span className="mdc-chat-context-topbar__icon">
          <Icon size={18} aria-hidden="true" />
        </span>

        <div>
          <strong>{title}</strong>
          {subtitle ? <small>{subtitle}</small> : null}
        </div>

        {badge ? <em>{badge}</em> : null}
      </div>

      <div className="mdc-chat-context-topbar__actions">
        {mode === "general" ? (
          <>
            <button type="button" onClick={onOpenAdmin}>
              Admin
            </button>
            <span>MVP</span>
          </>
        ) : null}

        {mode !== "general" ? (
          <div className="mdc-chat-context-topbar__menu-wrap">
            <button
              type="button"
              className="mdc-chat-context-topbar__menu-trigger"
              aria-label="Opções do contexto"
              aria-expanded={isMenuOpen}
              onClick={() => setIsMenuOpen((current) => !current)}
            >
              <MoreHorizontal size={20} aria-hidden="true" />
            </button>

            {isMenuOpen && mode === "project" ? (
              <div className="mdc-chat-context-topbar__menu">
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onRenameProject?.();
                  }}
                >
                  <Pencil size={17} aria-hidden="true" />
                  <span>Renomear projeto</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onOpenProjectSettings?.();
                  }}
                >
                  <Settings size={17} aria-hidden="true" />
                  <span>Configurações do projeto</span>
                </button>

                <button
                  type="button"
                  className="mdc-chat-context-topbar__danger"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onDeleteProject?.();
                  }}
                >
                  <Trash2 size={17} aria-hidden="true" />
                  <span>Excluir projeto</span>
                </button>
              </div>
            ) : null}

            {isMenuOpen && mode === "agent" ? (
              <div className="mdc-chat-context-topbar__menu">
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onManageAgents?.();
                  }}
                >
                  <Settings size={17} aria-hidden="true" />
                  <span>Gerenciar agentes</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    onClearAgent?.();
                  }}
                >
                  <X size={17} aria-hidden="true" />
                  <span>Sair do agente</span>
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </header>
  );
}
