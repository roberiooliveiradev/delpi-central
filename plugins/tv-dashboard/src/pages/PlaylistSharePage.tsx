import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Copy, Link2, QrCode, RefreshCw } from "lucide-react";

import {
  activatePlaylist,
  deactivatePlaylist,
  downloadQrPng,
  getPlaylist,
  regeneratePlaylistToken,
  type Playlist,
} from "../api/tvDashboardApi";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { playlistPath } from "../routing";

type Props = {
  playlistId: string;
  onBack: () => void;
};

export function PlaylistSharePage({ playlistId, onBack }: Props) {
  const confirm = useConfirm();
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPlaylist(await getPlaylist(playlistId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar programação.");
    } finally {
      setLoading(false);
    }
  }, [playlistId]);

  useEffect(() => {
    void load();
  }, [load]);

  function copyLink() {
    if (!playlist?.publicUrl) return;
    void navigator.clipboard.writeText(playlist.publicUrl);
    window.alert("Link copiado.");
  }

  function openQr() {
    void downloadQrPng(playlistId)
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank", "noopener,noreferrer");
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      })
      .catch((err) => {
        window.alert(err instanceof Error ? err.message : "Erro ao gerar QR.");
      });
  }

  async function handleToggleActive() {
    if (!playlist) return;
    const updated = playlist.isActive
      ? await deactivatePlaylist(playlist.id)
      : await activatePlaylist(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides });
  }

  async function handleRegenerateToken() {
    if (!playlist) return;
    const confirmed = await confirm({
      title: "Gerar novo link",
      message:
        "Gerar novo link? TVs com o link atual deixarão de funcionar até usar o novo endereço.",
      confirmLabel: "Gerar novo link",
      variant: "danger",
    });
    if (!confirmed) {
      return;
    }
    const updated = await regeneratePlaylistToken(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides });
    window.alert("Novo link gerado.");
  }

  if (loading) return <div className="td-state">Carregando…</div>;
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

  return (
    <>
      <div className="td-toolbar">
        <button type="button" className="td-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar ao editor
        </button>
      </div>
      <div className="td-card" style={{ maxWidth: 640 }}>
        <h2 style={{ marginTop: 0 }}>Compartilhar — {playlist.name}</h2>
        <p className="td-subtitle">
          {playlist.viewCount ?? 0} visualizações
          {playlist.isActive ? "" : " · link inativo"}
        </p>
        <div className="td-link-box">
          <input readOnly value={playlist.publicUrl ?? ""} aria-label="Link público" />
        </div>
        <div className="td-toolbar" style={{ marginTop: 16 }}>
          <button type="button" className="td-btn" onClick={copyLink}>
            <Copy size={16} />
            Copiar link
          </button>
          <button type="button" className="td-btn" onClick={openQr}>
            <QrCode size={16} />
            QR code
          </button>
          <button type="button" className="td-btn" onClick={() => void handleRegenerateToken()}>
            <RefreshCw size={16} />
            Novo link
          </button>
          <button type="button" className="td-btn" onClick={() => void handleToggleActive()}>
            <Link2 size={16} />
            {playlist.isActive ? "Desativar link" : "Reativar link"}
          </button>
        </div>
      </div>
    </>
  );
}

export function editorPathForShare(playlistId: string) {
  return playlistPath(playlistId);
}
