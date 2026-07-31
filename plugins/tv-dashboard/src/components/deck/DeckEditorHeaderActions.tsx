import {
  Copy,
  Eye,
  Keyboard,
  MonitorOff,
  Pencil,
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
  /** Aviso de coedição ao vivo — fica na top bar, à esquerda do nome. */
  editingPresence?: string | null;
  /** Duplo clique no nome abre renomear. */
  onRename?: () => void;
};

export type DeckHomePlaylistChromeProps = DeckPlaylistIdentityProps & {
  linkActive: boolean;
  /** Usado pela top bar («Lista de Painéis») — não duplicar tile na ribbon. */
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
  onRename?: () => void;
};

/** Título da programação + badge TV — barra superior (ao lado das abas). */
export function DeckPlaylistIdentity({
  playlistName,
  tvStatusLabel,
  tvStatusClass,
  onRename,
}: DeckPlaylistIdentityProps) {
  return (
    <div className="td-deck-chrome__identity" aria-label="Programação">
      <button
        type="button"
        className="td-deck-chrome__playlist-name"
        title={onRename ? `${playlistName} (duplo clique para renomear)` : playlistName}
        onDoubleClick={(event) => {
          if (!onRename) return;
          event.preventDefault();
          event.stopPropagation();
          onRename();
        }}
      >
        {playlistName}
      </button>
      {tvStatusLabel ? <span className={tvStatusClass}>{tvStatusLabel}</span> : null}
    </div>
  );
}

/**
 * Controles da programação/TV na aba Programação (tiles na ribbon).
 * Identidade (nome/status) fica em `DeckPlaylistIdentity` na barra superior.
 * Voltar à lista: só na top bar («Lista de Painéis»).
 */
export function DeckHomePlaylistChrome({
  linkActive,
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
  onRename,
}: DeckHomePlaylistChromeProps) {
  const { openCatalog } = useKeyboardShortcutsTips();

  return (
    <DeckRibbonGroup groupId="playlist-chrome" label="Programação" hint={R.playlistChrome}>
      <div className="td-deck-ribbon__playlist-chrome">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--playlist">
          <DeckRibbonTile icon={Eye} label="Prévia" hint={H.preview} onClick={onPreview} />
          {onRefreshVisual ? (
            <DeckRibbonTile
              icon={RefreshCw}
              label="Atualizar"
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
          {onRename ? (
            <DeckRibbonTile icon={Pencil} label="Renomear" hint={H.rename} onClick={onRename} />
          ) : null}
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
