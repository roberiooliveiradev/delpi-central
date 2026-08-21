import { useRef, useState } from "react";
import { AnchoredPanelPortal, ContextMenuItem } from "@delpi/plugin-ui/index";
import { MoreHorizontal, Trash2 } from "lucide-react";

import {
  CommercialActionButton,
  CM_PORTAL_SCOPE,
} from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

type Props = {
  canDelete: boolean;
  deleteDisabled?: boolean;
  onDelete: () => void;
};

/** Menu «…» da topbar da sala — opções sensíveis (excluir) ficam no popover. */
export function InteractionRoomMoreMenu({
  canDelete,
  deleteDisabled = false,
  onDelete,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  if (!canDelete) return null;

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
        className="delpi-ui-context-menu"
        variant="bare"
        role="menu"
        aria-label={content.roomMoreOptionsMenuAriaLabel}
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName={CM_PORTAL_SCOPE}
        onDismiss={() => setOpen(false)}
      >
        <ContextMenuItem
          label={content.deleteRoomActionLabel}
          icon={Trash2}
          destructive
          disabled={deleteDisabled}
          onSelect={() => {
            setOpen(false);
            onDelete();
          }}
        />
      </AnchoredPanelPortal>
    </div>
  );
}
