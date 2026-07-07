import {
  ArrowLeft,
  Copy,
  Eye,
  Link2,
  QrCode,
  RefreshCw,
  Trash2,
} from "lucide-react";

type Props = {
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

/** Ações da playlist integradas à faixa do chrome (sem barra extra no topo). */
export function DeckEditorHeaderActions({
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
}: Props) {
  return (
    <div className="td-deck-chrome__actions">
      <button type="button" className="td-btn td-btn--compact" onClick={onBack} title="Voltar">
        <ArrowLeft size={16} />
      </button>
      <span className="td-deck-chrome__actions-title" title={playlistName}>
        {playlistName}
      </span>
      {tvStatusLabel ? <span className={tvStatusClass}>{tvStatusLabel}</span> : null}
      <div className="td-deck-chrome__actions-group">
        <button type="button" className="td-btn td-btn--compact" onClick={onPreview} title="Pré-visualizar">
          <Eye size={16} />
        </button>
        <button type="button" className="td-btn td-btn--compact" onClick={onShare} title="Compartilhar">
          <Link2 size={16} />
        </button>
        <button type="button" className="td-btn td-btn--compact" onClick={onCopyLink} title="Copiar link">
          <Copy size={16} />
        </button>
        <button type="button" className="td-btn td-btn--compact" onClick={onQr} title="QR code">
          <QrCode size={16} />
        </button>
        <button type="button" className="td-btn td-btn--compact" onClick={onRegenerateToken} title="Novo link">
          <RefreshCw size={16} />
        </button>
        <button
          type="button"
          className="td-btn td-btn--compact"
          onClick={onToggleLink}
          title={linkActive ? "Desativar link" : "Reativar link"}
        >
          <Link2 size={16} />
        </button>
        <button type="button" className="td-btn td-btn--compact td-btn--danger" onClick={onDelete} title="Excluir">
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
}
