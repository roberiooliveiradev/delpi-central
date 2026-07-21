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

export type DeckPlaylistIdentityProps = {
  playlistName: string;
  tvStatusLabel?: string | null;
  tvStatusClass?: string;
};

export type DeckHomePlaylistChromeProps = DeckPlaylistIdentityProps & {
  linkActive: boolean;
  onBack: () => void;
  onPreview: () => void;
  /** Refresh dos dados no editor (não o link público). */
  onRefreshVisual?: () => void;
  dataPreviewStale?: boolean;
  dataPreviewLoading?: boolean;
  onShare: () => void;
  onCopyLink: () => void;
  onQr: () => void;
  onRegenerateToken: () => void;
  onToggleLink: () => void;
  onDelete: () => void;
};

/** Título da programação + badge TV — barra superior (ao lado das abas). */
export function DeckPlaylistIdentity({
  playlistName,
  tvStatusLabel,
  tvStatusClass,
}: DeckPlaylistIdentityProps) {
  return (
    <div className="td-deck-chrome__identity" aria-label="Programação">
      <span className="td-deck-chrome__playlist-name" title={playlistName}>
        {playlistName}
      </span>
      {tvStatusLabel ? <span className={tvStatusClass}>{tvStatusLabel}</span> : null}
    </div>
  );
}

/**
 * Controles da programação/TV na aba Programação (tiles na ribbon).
 * Identidade (nome/status) fica em `DeckPlaylistIdentity` na barra superior.
 */
export function DeckHomePlaylistChrome({
  linkActive,
  onBack,
  onPreview,
  onRefreshVisual,
  dataPreviewStale = false,
  dataPreviewLoading = false,
  onShare,
  onCopyLink,
  onQr,
  onRegenerateToken,
  onToggleLink,
  onDelete,
}: DeckHomePlaylistChromeProps) {
  const { openCatalog } = useKeyboardShortcutsTips();

  return (
    <DeckRibbonGroup label="Programação" hint={R.playlistChrome}>
      <div className="td-deck-ribbon__playlist-chrome">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--playlist">
          <DeckRibbonTile icon={ArrowLeft} label="Voltar" hint={H.back} onClick={onBack} />
          <DeckRibbonTile icon={Eye} label="Prévia" hint={H.preview} onClick={onPreview} />
          {onRefreshVisual ? (
            <DeckRibbonTile
              icon={RefreshCw}
              label="Atualizar visual"
              hint={H.refreshVisual}
              active={dataPreviewStale || dataPreviewLoading}
              onClick={onRefreshVisual}
            />
          ) : null}
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
            active={linkActive}
            hint={H.toggleLink}
            onClick={onToggleLink}
          />
          <DeckRibbonTile icon={Trash2} label="Excluir" hint={H.delete} onClick={onDelete} />
        </div>
      </div>
    </DeckRibbonGroup>
  );
}

/** @deprecated Use DeckHomePlaylistChrome — mantido para imports legados. */
export const DeckEditorHeaderActions = DeckHomePlaylistChrome;
