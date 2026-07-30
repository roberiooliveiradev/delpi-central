import { NativeTextControl } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useRef, useState } from "react";
import { Image as ImageIcon, Trash2, Type, Upload, Video } from "lucide-react";

import {
  adminMediaUrl,
  deletePlaylistMedia,
  listPlaylistMedia,
  uploadPlaylistMedia,
  type MediaAsset,
} from "../api/tvDashboardApi";
import {
  validateMediaUploadFile,
  type MediaUploadKind,
} from "../api/mediaUploadLimits";
import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import type { MediaLibraryTarget } from "./comunicadoEditorTypes";
import { HostContainedDialog } from "./ui/Modal";

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

  if (asset.mediaKind === "font") {
    return (
      <div className="td-media-library__thumb td-media-library__thumb--font">
        <Type size={28} aria-hidden />
      </div>
    );
  }

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

function targetMediaKind(target: MediaLibraryTarget): "image" | "video" | "font" | undefined {
  if (target === "insert-image" || target === "background") return "image";
  if (target === "insert-video") return "video";
  if (target === "custom-font") return "font";
  return undefined;
}

function targetTitle(target: MediaLibraryTarget): string {
  if (target === "background") return "Biblioteca — fundo do slide";
  if (target === "insert-image") return "Biblioteca — inserir imagem";
  if (target === "insert-video") return "Biblioteca — inserir vídeo";
  if (target === "custom-font") return "Biblioteca — fontes personalizadas";
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
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const kindFilter = targetMediaKind(target);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setError(null);
      setUploadProgress(null);
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

  async function handleUpload(file: File) {
    const allowed: MediaUploadKind[] | undefined = kindFilter ? [kindFilter] : undefined;
    const validationError = validateMediaUploadFile(file, allowed);
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    try {
      const asset = await uploadPlaylistMedia(playlistId, file, {
        onProgress: (ratio) => setUploadProgress(ratio),
      });
      onPick(asset);
      onUploaded();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar arquivo.");
    } finally {
      setLoading(false);
      setUploadProgress(null);
    }
  }

  async function handleDelete(asset: MediaAsset) {
    const label = asset.originalName ?? asset.storedName;
    const confirmed = window.confirm(
      `Excluir “${label}”? Slides que usam este arquivo ficam sem mídia.`,
    );
    if (!confirmed) return;
    setDeletingId(asset.id);
    setError(null);
    try {
      await deletePlaylistMedia(playlistId, asset.id);
      setItems((current) => current.filter((item) => item.id !== asset.id));
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir arquivo.");
    } finally {
      setDeletingId(null);
    }
  }

  const busy = uploading || loading || deletingId != null;

  return (
    <HostContainedDialog open={open} title={targetTitle(target)} onClose={onClose} className="td-modal--wide">
      <div className="td-media-library__toolbar">
        <NativeTextControl
          type="text"
          placeholder="Buscar por nome…"
          value={query}
          aria-label="Buscar por nome"
          onChange={setQuery}
        />
        <button
          type="button"
          className="td-btn td-btn--sm"
          disabled={busy}
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
              : kindFilter === "font"
                ? ".woff2,.ttf,.otf,font/woff2,font/ttf,font/otf"
                : kindFilter === "image"
                  ? "image/jpeg,image/png,image/webp,image/gif"
                  : "image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,.woff2,.ttf,.otf,font/woff2,font/ttf,font/otf"
          }
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void handleUpload(file);
          }}
        />
      </div>
      {uploadProgress != null ? (
        <p className="td-subtitle" role="status">
          Enviando… {Math.round(uploadProgress * 100)}%
        </p>
      ) : null}
      {loading && uploadProgress == null ? <p className="td-subtitle">Carregando biblioteca…</p> : null}
      {error ? <p className="td-error">{error}</p> : null}
      {!loading && filtered.length === 0 ? (
        <p className="td-subtitle">Nenhum arquivo na playlist. Envie o primeiro acima.</p>
      ) : null}
      <ul className="td-media-library__grid">
        {filtered.map((asset) => (
          <li key={asset.id} className="td-media-library__item">
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
                {asset.mediaKind === "video"
                  ? "Vídeo"
                  : asset.mediaKind === "font"
                    ? "Fonte"
                    : "Imagem"}{" "}
                · {formatBytes(asset.fileSizeBytes)}
              </span>
            </button>
            <button
              type="button"
              className="td-media-library__delete"
              title="Excluir da biblioteca"
              aria-label={`Excluir ${asset.originalName ?? asset.storedName}`}
              disabled={busy}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                void handleDelete(asset);
              }}
            >
              <Trash2 size={14} aria-hidden />
            </button>
          </li>
        ))}
      </ul>
    </HostContainedDialog>
  );
}
