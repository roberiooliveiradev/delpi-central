import {
  ArrowLeft,
  Copy,
  Eye,
  QrCode,
  RefreshCw,
  Trash2,
  Tv,
  TvOff,
  Users,
} from "lucide-react";
import type { ReactNode } from "react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";

const H = TV_DASHBOARD_HELP_TOOLTIPS.header;

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

function HeaderActionButton({
  hint,
  ariaLabel,
  onClick,
  danger,
  children,
}: {
  hint: string;
  ariaLabel: string;
  onClick: () => void;
  danger?: boolean;
  children: ReactNode;
}) {
  return (
    <HintAction hint={hint} ariaLabel={ariaLabel} placement="bottom">
      <button
        type="button"
        className={["td-btn", "td-btn--compact", danger ? "td-btn--danger" : null]
          .filter(Boolean)
          .join(" ")}
        aria-label={ariaLabel}
        onClick={onClick}
      >
        {children}
      </button>
    </HintAction>
  );
}

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
      <HeaderActionButton hint={H.back} ariaLabel="Voltar" onClick={onBack}>
        <ArrowLeft size={16} />
      </HeaderActionButton>
      <span className="td-deck-chrome__actions-title" title={playlistName}>
        {playlistName}
      </span>
      {tvStatusLabel ? <span className={tvStatusClass}>{tvStatusLabel}</span> : null}
      <div className="td-deck-chrome__actions-group">
        <HeaderActionButton hint={H.preview} ariaLabel="Pré-visualizar" onClick={onPreview}>
          <Eye size={16} />
        </HeaderActionButton>

        <span className="td-deck-chrome__actions-sep" aria-hidden="true" />

        <HeaderActionButton
          hint={H.share}
          ariaLabel="Colaboradores e edição"
          onClick={onShare}
        >
          <Users size={16} />
        </HeaderActionButton>

        <span className="td-deck-chrome__actions-sep" aria-hidden="true" />

        <HeaderActionButton hint={H.copyLink} ariaLabel="Copiar link da TV" onClick={onCopyLink}>
          <Copy size={16} />
        </HeaderActionButton>
        <HeaderActionButton hint={H.qr} ariaLabel="QR code da TV" onClick={onQr}>
          <QrCode size={16} />
        </HeaderActionButton>
        <HeaderActionButton
          hint={H.regenerateToken}
          ariaLabel="Novo link da TV"
          onClick={onRegenerateToken}
        >
          <RefreshCw size={16} />
        </HeaderActionButton>
        <HeaderActionButton
          hint={H.toggleLink}
          ariaLabel={linkActive ? "Desativar link da TV" : "Ativar link da TV"}
          onClick={onToggleLink}
        >
          {linkActive ? <Tv size={16} /> : <TvOff size={16} />}
        </HeaderActionButton>

        <span className="td-deck-chrome__actions-sep" aria-hidden="true" />

        <HeaderActionButton hint={H.delete} ariaLabel="Excluir" onClick={onDelete} danger>
          <Trash2 size={16} />
        </HeaderActionButton>
      </div>
    </div>
  );
}
