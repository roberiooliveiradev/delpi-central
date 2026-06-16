import {
  Folder,
  Pencil,
  Settings,
  Trash2,
} from "lucide-react";

import type { ChatProject } from "../../data/api/chatTypes";
import { shouldOpenChatLinkInNewTab } from "../../navigation/chatNavigation";
import { DropdownMenuTrigger } from "./shared/menus/DropdownMenuTrigger";

import "./ChatProjectCard.css";

type ChatProjectCardProps = {
  project: ChatProject;
  active?: boolean;
  href?: string;
  onSelect: () => void;
  onRename?: () => void;
  onOpenSettings?: () => void;
  onDelete?: () => void;
};

export function ChatProjectCard({
  project,
  active,
  href,
  onSelect,
  onRename,
  onOpenSettings,
  onDelete,
}: ChatProjectCardProps) {
  const menuItems = [
    {
      id: "rename",
      label: "Renomear",
      icon: <Pencil size={17} aria-hidden="true" />,
      onSelect: () => onRename?.(),
    },
    {
      id: "settings",
      label: "Configurações",
      icon: <Settings size={17} aria-hidden="true" />,
      onSelect: () => onOpenSettings?.(),
    },
    {
      id: "delete",
      label: "Excluir projeto",
      icon: <Trash2 size={17} aria-hidden="true" />,
      variant: "danger" as const,
      onSelect: () => onDelete?.(),
    },
  ];

  return (
    <div
      className={
        active
          ? "mdc-chat-project-card mdc-chat-project-card--active"
          : "mdc-chat-project-card"
      }
    >
      {href ? (
        <a
          href={href}
          className="mdc-chat-project-card__main"
          onClick={(event) => {
            if (shouldOpenChatLinkInNewTab(event)) {
              return;
            }

            event.preventDefault();
            onSelect();
          }}
          title={project.description || project.name}
        >
          <span className="mdc-chat-project-card__icon">
            <Folder size={15} aria-hidden="true" />
          </span>

          <span className="mdc-chat-project-card__content">
            <strong>{project.name}</strong>
          </span>
        </a>
      ) : (
        <button
          type="button"
          className="mdc-chat-project-card__main"
          onClick={onSelect}
          title={project.description || project.name}
        >
          <span className="mdc-chat-project-card__icon">
            <Folder size={15} aria-hidden="true" />
          </span>

          <span className="mdc-chat-project-card__content">
            <strong>{project.name}</strong>
          </span>
        </button>
      )}

      <DropdownMenuTrigger
        items={menuItems}
        menuLabel="Opções do projeto"
        ariaLabel="Opções do projeto"
        iconSize={16}
        triggerClassName="mdc-chat-project-card__options"
      />
    </div>
  );
}
