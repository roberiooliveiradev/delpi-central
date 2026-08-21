import { useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  ContextMenuDivider,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";

import {
  CommercialActionButton,
  CM_PORTAL_SCOPE,
} from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

type Props = {
  canRename?: boolean;
  canDelete?: boolean;
  renameDisabled?: boolean;
  deleteDisabled?: boolean;
  onRename?: () => void;
  onDelete?: () => void;
};

/** Menu «…» da topbar — opções da conversa no popover ancorado ao gatilho. */
export function InteractionRoomMoreMenu({
  canRename = false,
  canDelete = false,
  renameDisabled = false,
  deleteDisabled = false,
  onRename,
  onDelete,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  if (!canRename && !canDelete) return null;

  return (
    <div ref={anchorRef} className="cm-room-more-menu">
      <CommercialActionButton
        type="button"
        variant="ghost"
        aria-label={content.roomMoreOptionsAriaLabel}
        title={content.roomMoreOptionsAriaLabel}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
      >
        <MoreHorizontal size={16} aria-hidden />
      </CommercialActionButton>
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        className="delpi-ui-context-menu cm-room-more-menu__panel"
        variant="bare"
        role="menu"
        aria-label={content.roomMoreOptionsMenuAriaLabel}
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={10}
        portalScopeClassName={CM_PORTAL_SCOPE}
        onDismiss={() => setOpen(false)}
      >
        {canRename ? (
          <ContextMenuItem
            label={content.renameRoomActionLabel}
            icon={Pencil}
            disabled={renameDisabled}
            onSelect={() => {
              setOpen(false);
              onRename?.();
            }}
          />
        ) : null}
        {canRename && canDelete ? <ContextMenuDivider /> : null}
        {canDelete ? (
          <ContextMenuItem
            label={content.deleteRoomActionLabel}
            icon={Trash2}
            destructive
            disabled={deleteDisabled}
            onSelect={() => {
              setOpen(false);
              onDelete?.();
            }}
          />
        ) : null}
      </AnchoredPanelPortal>
    </div>
  );
}
