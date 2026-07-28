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
  FolderPlus,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const C = TV_DASHBOARD_HELP_TOOLTIPS.filmstripContextMenu;

function formatCount(template: string, count: number): string {
  return template.replace("{count}", String(count));
}

export type SlideFilmstripContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  slideTitle: string;
  slideActive: boolean;
  selectionCount?: number;
  canPaste: boolean;
  onClose: () => void;
  onCopy: () => void;
  onPaste: () => void;
  onDuplicate: () => void;
  onAdd: () => void;
  onCreateSection?: () => void;
  onRename: () => void;
  onToggleActive: () => void;
  onRemove: () => void;
};

export function SlideFilmstripContextMenu({
  open,
  position,
  slideTitle,
  slideActive,
  selectionCount = 1,
  canPaste,
  onClose,
  onCopy,
  onPaste,
  onDuplicate,
  onAdd,
  onCreateSection,
  onRename,
  onToggleActive,
  onRemove,
}: SlideFilmstripContextMenuProps) {
  function run(action: () => void) {
    action();
    onClose();
  }

  const many = selectionCount > 1;
  const duplicateLabel = many ? formatCount(C.duplicateMany, selectionCount) : C.duplicate;
  const toggleLabel = slideActive
    ? many
      ? formatCount(C.hideMany, selectionCount)
      : C.hide
    : many
      ? formatCount(C.showMany, selectionCount)
      : C.show;
  const deleteLabel = many ? formatCount(C.deleteMany, selectionCount) : C.delete;

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
      {onCreateSection ? (
        <ContextMenuItem
          label={C.createSection}
          icon={FolderPlus}
          onSelect={() => run(onCreateSection)}
        />
      ) : null}
      <ContextMenuItem label={duplicateLabel} icon={Copy} onSelect={() => run(onDuplicate)} />
      <ContextMenuItem
        label={C.rename}
        icon={Pencil}
        disabled={many}
        onSelect={() => run(onRename)}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label={toggleLabel}
        icon={slideActive ? EyeOff : Eye}
        onSelect={() => run(onToggleActive)}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label={deleteLabel}
        icon={Trash2}
        shortcut="Del"
        destructive
        onSelect={() => run(onRemove)}
      />
    </ContextMenu>
  );
}
