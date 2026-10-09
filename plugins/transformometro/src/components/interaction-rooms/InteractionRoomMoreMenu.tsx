import { useRef, useState } from "react";
import {
  ActionButton,
  AnchoredPanelPortal,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";
import { MoreHorizontal, Trash2 } from "lucide-react";

type Props = {
  deleteDisabled?: boolean;
  onDelete?: () => void;
  portalScopeClassName: string;
};

/** Menu «…» da topbar da sala — ações destrutivas ficam aqui, não no canvas. */
export function InteractionRoomMoreMenu({
  deleteDisabled = false,
  onDelete,
  portalScopeClassName,
}: Props) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  return (
    <div ref={anchorRef} className="tm-room-more-menu">
      <ActionButton
        type="button"
        variant="ghost"
        aria-label="Opções da sala"
        title="Opções da sala"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
      >
        <MoreHorizontal size={16} aria-hidden />
      </ActionButton>
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        className="delpi-ui-context-menu tm-room-more-menu__panel"
        variant="bare"
        role="menu"
        aria-label="Opções da sala"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={10}
        portalScopeClassName={portalScopeClassName}
        onDismiss={() => setOpen(false)}
      >
        <ContextMenuItem
          label="Excluir sala"
          icon={Trash2}
          destructive
          disabled={deleteDisabled}
          onSelect={() => {
            setOpen(false);
            onDelete?.();
          }}
        />
      </AnchoredPanelPortal>
    </div>
  );
}
