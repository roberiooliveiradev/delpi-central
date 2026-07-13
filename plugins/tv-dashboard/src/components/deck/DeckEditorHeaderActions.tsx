import {
  ArrowLeft,
  Copy,
  Eye,
  Keyboard,
  MonitorOff,
  QrCode,
  RefreshCw,
  Trash2,
  Tv,
  Users,
} from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useKeyboardShortcutsTips } from "../../context/KeyboardShortcutsTipsProvider";
import { DeckRibbonGroup } from "./DeckRibbonGroup";
import { DeckRibbonTile } from "./DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.header;
const R = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

export type DeckHomePlaylistChromeProps = {
  playlistName: string;
  tvStatusLabel?: string | null;
  tvStatusClass?: string;
  linkActive: boolean;
  onBack: () => void;
  onPreview: () => void;
  onShare: () => void;
  onCopyLink: () => void;
  onQr: () => void;
  onRegenerateToken: () => void;
  onToggleLink: () => void;
  onDelete: () => void;
};

/**
 * Controles da programação/TV na aba Página Inicial (antes ficavam à direita das abas).
 */
export function DeckHomePlaylistChrome({
  playlistName,
  tvStatusLabel,
  tvStatusClass,
  linkActive,
  onBack,
  onPreview,
  onShare,
  onCopyLink,
  onQr,
  onRegenerateToken,
  onToggleLink,
  onDelete,
}: DeckHomePlaylistChromeProps) {
  const { openCatalog } = useKeyboardShortcutsTips();

  return (
    <>
      <DeckRibbonGroup label="Programação" hint={R.playlistChrome}>
        <div className="td-deck-ribbon__playlist-chrome">
          <div className="td-deck-ribbon__playlist-meta">
            <span className="td-deck-ribbon__playlist-name" title={playlistName}>
              {playlistName}
            </span>
            {tvStatusLabel ? <span className={tvStatusClass}>{tvStatusLabel}</span> : null}
          </div>
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTile icon={ArrowLeft} label="Voltar" hint={H.back} onClick={onBack} />
            <DeckRibbonTile icon={Eye} label="Prévia" hint={H.preview} onClick={onPreview} />
            <DeckRibbonTile
              icon={Keyboard}
              label="Atalhos"
              hint="Catálogo de atalhos. Alt revela balões (Ctrl e F1–F8 nas abas)."
              onClick={openCatalog}
            />
            <DeckRibbonTile icon={Users} label="Editores" hint={H.share} onClick={onShare} />
            <DeckRibbonTile icon={Copy} label="Link TV" hint={H.copyLink} onClick={onCopyLink} />
            <DeckRibbonTile icon={QrCode} label="QR" hint={H.qr} onClick={onQr} />
            <DeckRibbonTile
              icon={RefreshCw}
              label="Novo link"
              hint={H.regenerateToken}
              onClick={onRegenerateToken}
            />
            <DeckRibbonTile
              icon={linkActive ? Tv : MonitorOff}
              label={linkActive ? "TV on" : "TV off"}
              hint={H.toggleLink}
              active={linkActive}
              onClick={onToggleLink}
            />
            <DeckRibbonTile icon={Trash2} label="Excluir" hint={H.delete} onClick={onDelete} />
          </div>
        </div>
      </DeckRibbonGroup>
    </>
  );
}

/** @deprecated Use DeckHomePlaylistChrome — mantido para imports legados. */
export const DeckEditorHeaderActions = DeckHomePlaylistChrome;
