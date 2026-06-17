import {
  Archive,
  Pencil,
  Pin,
  Trash2,
} from "lucide-react";

import { DropdownMenuTrigger } from "../shared/menus/DropdownMenuTrigger";

import "../../styles/chat-overlay-layer.css";
import "./ChatConversationMenu.css";

type ChatConversationMenuProps = {
  open: boolean;
  disabled?: boolean;
  onOpenChange: (open: boolean) => void;
  onRename: () => void;
  pinLabel?: string;
  archiveLabel?: string;
  onPin?: () => void;
  onArchive?: () => void;
  onDelete: () => void;
};

export function ChatConversationMenu({
  open,
  disabled,
  onOpenChange,
  onRename,
  pinLabel = "Fixar chat",
  archiveLabel = "Arquivar",
  onPin,
  onArchive,
  onDelete,
}: ChatConversationMenuProps) {
  const menuItems = [
    {
      id: "rename",
      label: "Renomear",
      icon: <Pencil size={18} aria-hidden="true" />,
      onSelect: () => onRename(),
    },
    {
      id: "pin",
      label: pinLabel,
      icon: <Pin size={18} aria-hidden="true" />,
      disabled: !onPin,
      leadingDivider: true,
      onSelect: () => onPin?.(),
    },
    {
      id: "archive",
      label: archiveLabel,
      icon: <Archive size={18} aria-hidden="true" />,
      disabled: !onArchive,
      onSelect: () => onArchive?.(),
    },
    {
      id: "delete",
      label: "Excluir",
      icon: <Trash2 size={18} aria-hidden="true" />,
      variant: "danger" as const,
      onSelect: () => onDelete(),
    },
  ];

  return (
    <DropdownMenuTrigger
      open={open}
      onOpenChange={onOpenChange}
      disabled={disabled}
      items={menuItems}
      menuLabel="Opções da conversa"
      ariaLabel="Abrir opções da conversa"
      iconSize={17}
      wrapClassName="mdc-chat-conversation-menu"
      triggerClassName="mdc-chat-conversation-menu__trigger"
      panelClassName="mdc-chat-conversation-menu__panel mdc-menu-popover--sidebar-action"
      scrim="transparent"
    />
  );
}
