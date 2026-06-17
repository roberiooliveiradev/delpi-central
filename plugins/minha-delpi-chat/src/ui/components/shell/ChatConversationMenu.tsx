import {
  Archive,
  Pencil,
  Pin,
  Share2,
  Trash2,
} from "lucide-react";

import { DropdownMenuTrigger } from "../shared/menus/DropdownMenuTrigger";

import "../../styles/chat-overlay-layer.css";
import "./ChatConversationMenu.css";

type ChatConversationMenuProps = {
  open: boolean;
  disabled?: boolean;
  onOpenChange: (open: boolean) => void;
  onShare?: () => void;
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
  onShare,
  onRename,
  pinLabel = "Fixar chat",
  archiveLabel = "Arquivar",
  onPin,
  onArchive,
  onDelete,
}: ChatConversationMenuProps) {
  const menuItems = [
    ...(onShare
      ? [
          {
            id: "share",
            label: "Compartilhar",
            icon: <Share2 size={18} aria-hidden="true" />,
            onSelect: () => onShare(),
          },
        ]
      : []),
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
      panelClassName="mdc-chat-conversation-menu__panel"
      scrim="backdrop"
    />
  );
}
