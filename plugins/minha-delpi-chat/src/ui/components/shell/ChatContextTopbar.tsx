import {
  Bot,
  CircleHelp,
  Folder,
  MessageSquare,
  PanelLeft,
  Pencil,
  Settings,
  Trash2,
  X,
  Box,
} from "lucide-react";
import { useMemo } from "react";

import { DropdownMenuTrigger } from "../shared/menus/DropdownMenuTrigger";
import type { ActionMenuItem } from "../shared/menus/ActionMenuPanel";

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
  onOpenSidebar?: () => void;
  onOpenHelp?: () => void;
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
  onOpenSidebar,
  onOpenHelp,
}: ChatContextTopbarProps) {
  const Icon =
    mode === "project" ? Folder : mode === "agent" ? Bot : MessageSquare;

  const contextMenuItems = useMemo((): ActionMenuItem[] => {
    if (mode === "project") {
      return [
        ...(onOpenAdmin
          ? [
              {
                id: "admin",
                label: "Administração",
                icon: <Settings size={17} aria-hidden="true" />,
                onSelect: () => onOpenAdmin(),
              },
            ]
          : []),
        ...(onManageAgents
          ? [
              {
                id: "agents",
                label: "Apps e agentes",
                icon: <Box size={17} aria-hidden="true" />,
                onSelect: () => onManageAgents(),
              },
            ]
          : []),
        {
          id: "rename",
          label: "Renomear projeto",
          icon: <Pencil size={17} aria-hidden="true" />,
          onSelect: () => onRenameProject?.(),
        },
        {
          id: "settings",
          label: "Configurações do projeto",
          icon: <Settings size={17} aria-hidden="true" />,
          onSelect: () => onOpenProjectSettings?.(),
        },
        {
          id: "delete",
          label: "Excluir projeto",
          icon: <Trash2 size={17} aria-hidden="true" />,
          variant: "danger" as const,
          onSelect: () => onDeleteProject?.(),
        },
      ];
    }

    if (mode === "agent") {
      return [
        ...(onOpenAdmin
          ? [
              {
                id: "admin",
                label: "Administração",
                icon: <Settings size={17} aria-hidden="true" />,
                onSelect: () => onOpenAdmin(),
              },
            ]
          : []),
        ...(onManageAgents
          ? [
              {
                id: "agents",
                label: "Apps e agentes",
                icon: <Settings size={17} aria-hidden="true" />,
                onSelect: () => onManageAgents(),
              },
            ]
          : []),
        {
          id: "clear-agent",
          label: "Sair do agente",
          icon: <X size={17} aria-hidden="true" />,
          onSelect: () => onClearAgent?.(),
        },
      ];
    }

    return [];
  }, [
    mode,
    onClearAgent,
    onDeleteProject,
    onManageAgents,
    onOpenAdmin,
    onOpenProjectSettings,
    onRenameProject,
  ]);

  return (
    <header className="mdc-chat-context-topbar">
      <div className="mdc-chat-context-topbar__start">
        {onOpenSidebar ? (
          <button
            type="button"
            className="mdc-chat-context-topbar__menu-trigger mdc-chat-context-topbar__menu-trigger--sidebar"
            onClick={onOpenSidebar}
            aria-label="Abrir menu de conversas"
          >
            <PanelLeft size={18} aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className="mdc-chat-context-topbar__center">
        <span className="mdc-chat-context-topbar__icon">
          <Icon size={18} aria-hidden="true" />
        </span>

        <div className="mdc-chat-context-topbar__titles">
          <strong>{title}</strong>
          {subtitle ? <small>{subtitle}</small> : null}
        </div>

        {badge ? <em className="mdc-chat-context-topbar__badge">{badge}</em> : null}
      </div>

      <div className="mdc-chat-context-topbar__end">
        {onOpenHelp ? (
          <button
            type="button"
            className="mdc-chat-context-topbar__help-trigger"
            aria-label="Ajuda do chat"
            title="Ajuda do chat"
            onClick={onOpenHelp}
          >
            <CircleHelp size={18} aria-hidden="true" />
          </button>
        ) : null}

        {onOpenAdmin && mode === "general" ? (
          <button
            type="button"
            className="mdc-chat-context-topbar__admin-btn"
            onClick={() => onOpenAdmin()}
          >
            <span className="mdc-chat-context-topbar__admin-label--long">Administração</span>
            <span className="mdc-chat-context-topbar__admin-label--short">Admin</span>
          </button>
        ) : null}

        {mode !== "general" && contextMenuItems.length > 0 ? (
          <DropdownMenuTrigger
            items={contextMenuItems}
            menuLabel="Opções do contexto"
            ariaLabel="Opções do contexto"
            iconSize={20}
            wrapClassName="mdc-chat-context-topbar__menu-wrap"
            triggerClassName="mdc-chat-context-topbar__menu-trigger"
          />
        ) : null}
      </div>
    </header>
  );
}
