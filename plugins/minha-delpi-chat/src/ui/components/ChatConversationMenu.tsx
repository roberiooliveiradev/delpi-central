import {
  Archive,
  MoreHorizontal,
  Pencil,
  Pin,
  Share2,
  Trash2,
} from "lucide-react";
import { useRef } from "react";

import { AnchoredMenuPortal } from "./shared/overlay/AnchoredMenuPortal";
import { ActionMenuPanel } from "./shared/menus/ActionMenuPanel";

import "./chat-overlay-layer.css";
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
  const triggerRef = useRef<HTMLButtonElement | null>(null);

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
    <div className="mdc-chat-conversation-menu">
      <button
        ref={triggerRef}
        type="button"
        className="mdc-chat-conversation-menu__trigger"
        disabled={disabled}
        onClick={(event) => {
          event.stopPropagation();
          onOpenChange(!open);
        }}
        aria-label="Abrir opções da conversa"
        aria-expanded={open}
        title="Opções"
      >
        <MoreHorizontal size={17} aria-hidden="true" />
      </button>

      <AnchoredMenuPortal
        open={open}
        triggerRef={triggerRef}
        itemCount={menuItems.length}
        placement="action-menu"
        menuLabel="Opções da conversa"
        menuRole="menu"
        scrim="backdrop"
        panelClassName="mdc-chat-conversation-menu__panel"
        onClose={() => onOpenChange(false)}
      >
        <ActionMenuPanel items={menuItems} onItemSelect={() => onOpenChange(false)} />
      </AnchoredMenuPortal>
    </div>
  );
}
