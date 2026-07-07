import { useEffect, useMemo, useRef, useState } from "react";
import { Image as ImageIcon, Upload, Video, X } from "lucide-react";

import {
  adminMediaUrl,
  listPlaylistMedia,
  uploadPlaylistMedia,
  type MediaAsset,
} from "../api/tvDashboardApi";
import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import type { MediaLibraryTarget } from "./comunicadoEditorTypes";

type Props = {
  open: boolean;
  target: MediaLibraryTarget;
  playlistId: string;
  uploading: boolean;
  onClose: () => void;
  onPick: (asset: MediaAsset) => void;
  onUploaded: () => void;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function MediaLibraryThumbnail({ asset, playlistId }: { asset: MediaAsset; playlistId: string }) {
  const url = adminMediaUrl(playlistId, asset.id);
  const { src, loading, error } = useAuthenticatedBlobUrl(url);

  if (asset.mediaKind === "video") {
    return (
      <div className="td-media-library__thumb td-media-library__thumb--video">
        {src ? (
          <video src={src} muted playsInline preload="metadata" />
        ) : loading ? (
          <span className="td-media-library__thumb-placeholder">…</span>
        ) : error ? (
          <Video size={28} aria-hidden />
        ) : (
          <Video size={28} aria-hidden />
        )}
      </div>
    );
  }

  return (
    <div className="td-media-library__thumb">
      {src ? (
        <img src={src} alt="" />
      ) : loading ? (
        <span className="td-media-library__thumb-placeholder">…</span>
      ) : error ? (
        <ImageIcon size={28} aria-hidden />
      ) : (
        <ImageIcon size={28} aria-hidden />
      )}
    </div>
  );
}

function targetMediaKind(target: MediaLibraryTarget): "image" | "video" | undefined {
  if (target === "insert-image" || target === "background") return "image";
  if (target === "insert-video") return "video";
  return undefined;
}

function targetTitle(target: MediaLibraryTarget): string {
  if (target === "background") return "Biblioteca — fundo do slide";
  if (target === "insert-image") return "Biblioteca — inserir imagem";
  if (target === "insert-video") return "Biblioteca — inserir vídeo";
  return "Biblioteca de mídia";
}

export function MediaLibraryModal({
  open,
  target,
  playlistId,
  uploading,
  onClose,
  onPick,
  onUploaded,
}: Props) {
  const [items, setItems] = useState<MediaAsset[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const kindFilter = targetMediaKind(target);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    void listPlaylistMedia(playlistId, kindFilter)
      .then(setItems)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [open, playlistId, kindFilter]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((asset) => {
      const name = (asset.originalName ?? asset.storedName).toLowerCase();
      return name.includes(q) || asset.mimeType.toLowerCase().includes(q);
    });
  }, [items, query]);

  if (!open) return null;

  async function handleUpload(file: File) {
    setLoading(true);
    setError(null);
    try {
      const asset = await uploadPlaylistMedia(playlistId, file);
      onPick(asset);
      onUploaded();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar arquivo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="td-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="td-modal td-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-label={targetTitle(target)}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="td-modal__header">
          <h2>{targetTitle(target)}</h2>
          <button type="button" className="td-icon-btn" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </header>
        <div className="td-modal__body">
          <div className="td-media-library__toolbar">
            <input
              type="search"
              placeholder="Buscar por nome…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={uploading || loading}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={15} aria-hidden />
              Enviar novo
            </button>
            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept={
                kindFilter === "video"
                  ? "video/mp4,video/webm"
                  : kindFilter === "image"
                    ? "image/jpeg,image/png,image/webp,image/gif"
                    : "image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
              }
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (file) void handleUpload(file);
              }}
            />
          </div>
          {loading ? <p className="td-subtitle">Carregando biblioteca…</p> : null}
          {error ? <p className="td-error">{error}</p> : null}
          {!loading && filtered.length === 0 ? (
            <p className="td-subtitle">Nenhum arquivo na playlist. Envie o primeiro acima.</p>
          ) : null}
          <ul className="td-media-library__grid">
            {filtered.map((asset) => (
              <li key={asset.id}>
                <button
                  type="button"
                  className="td-media-library__card"
                  onClick={() => {
                    onPick(asset);
                    onClose();
                  }}
                >
                  <MediaLibraryThumbnail asset={asset} playlistId={playlistId} />
                  <span className="td-media-library__name" title={asset.originalName ?? asset.storedName}>
                    {asset.originalName ?? asset.storedName}
                  </span>
                  <span className="td-media-library__meta">
                    {asset.mediaKind === "video" ? "Vídeo" : "Imagem"} · {formatBytes(asset.fileSizeBytes)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
