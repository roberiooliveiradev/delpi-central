import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  Copy,
  Eye,
  MonitorOff,
  MonitorPlay,
  QrCode,
  RefreshCw,
  Trash2,
  Tv,
  Users,
} from "lucide-react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const C = TV_DASHBOARD_HELP_TOOLTIPS.homeContextMenu;

export type PlaylistHomeContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  playlistName: string;
  linkActive: boolean;
  onClose: () => void;
  onOpen: () => void;
  onDuplicate: () => void;
  onPreview: () => void;
  onShare: () => void;
  onCopyLink: () => void;
  onQr: () => void;
  onRegenerateToken: () => void;
  onToggleLink: () => void;
  onDelete: () => void;
};

/** Menu do botão direito nos cards da home (ações da antiga Página Inicial). */
export function PlaylistHomeContextMenu({
  open,
  position,
  playlistName,
  linkActive,
  onClose,
  onOpen,
  onDuplicate,
  onPreview,
  onShare,
  onCopyLink,
  onQr,
  onRegenerateToken,
  onToggleLink,
  onDelete,
}: PlaylistHomeContextMenuProps) {
  function run(action: () => void) {
    action();
    onClose();
  }

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={`${C.menu}: ${playlistName}`}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      <ContextMenuItem label={C.open} icon={MonitorPlay} onSelect={() => run(onOpen)} />
      <ContextMenuItem label={C.duplicate} icon={Copy} onSelect={() => run(onDuplicate)} />
      <ContextMenuItem label={C.preview} icon={Eye} onSelect={() => run(onPreview)} />
      <ContextMenuDivider />
      <ContextMenuItem label={C.share} icon={Users} onSelect={() => run(onShare)} />
      <ContextMenuItem label={C.copyLink} icon={Copy} onSelect={() => run(onCopyLink)} />
      <ContextMenuItem label={C.qr} icon={QrCode} onSelect={() => run(onQr)} />
      <ContextMenuItem
        label={C.regenerateToken}
        icon={RefreshCw}
        onSelect={() => run(onRegenerateToken)}
      />
      <ContextMenuItem
        label={linkActive ? C.tvOff : C.tvOn}
        icon={linkActive ? Tv : MonitorOff}
        onSelect={() => run(onToggleLink)}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label={C.delete}
        icon={Trash2}
        destructive
        onSelect={() => run(onDelete)}
      />
    </ContextMenu>
  );
}
