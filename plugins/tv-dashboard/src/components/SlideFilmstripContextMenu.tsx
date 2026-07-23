import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  Clipboard,
  ClipboardPaste,
  Copy,
  Eye,
  EyeOff,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const C = TV_DASHBOARD_HELP_TOOLTIPS.filmstripContextMenu;

export type SlideFilmstripContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  slideTitle: string;
  slideActive: boolean;
  canPaste: boolean;
  onClose: () => void;
  onCopy: () => void;
  onPaste: () => void;
  onDuplicate: () => void;
  onAdd: () => void;
  onRename: () => void;
  onToggleActive: () => void;
  onRemove: () => void;
};

export function SlideFilmstripContextMenu({
  open,
  position,
  slideTitle,
  slideActive,
  canPaste,
  onClose,
  onCopy,
  onPaste,
  onDuplicate,
  onAdd,
  onRename,
  onToggleActive,
  onRemove,
}: SlideFilmstripContextMenuProps) {
  function run(action: () => void) {
    action();
    onClose();
  }

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={`${C.menu}: ${slideTitle}`}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      <ContextMenuItem
        label={C.copy}
        icon={Clipboard}
        shortcut="Ctrl+C"
        onSelect={() => run(onCopy)}
      />
      <ContextMenuItem
        label={C.paste}
        icon={ClipboardPaste}
        shortcut="Ctrl+V"
        disabled={!canPaste}
        onSelect={() => run(onPaste)}
      />
      <ContextMenuDivider />
      <ContextMenuItem label={C.newSlide} icon={Plus} onSelect={() => run(onAdd)} />
      <ContextMenuItem label={C.duplicate} icon={Copy} onSelect={() => run(onDuplicate)} />
      <ContextMenuItem label={C.rename} icon={Pencil} onSelect={() => run(onRename)} />
      <ContextMenuDivider />
      <ContextMenuItem
        label={slideActive ? C.hide : C.show}
        icon={slideActive ? EyeOff : Eye}
        onSelect={() => run(onToggleActive)}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label={C.delete}
        icon={Trash2}
        shortcut="Del"
        destructive
        onSelect={() => run(onRemove)}
      />
    </ContextMenu>
  );
}
