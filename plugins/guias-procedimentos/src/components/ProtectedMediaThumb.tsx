import { Film, ImageIcon, Link2 } from "lucide-react";

import type { ProcedureMedia } from "../api/guiasProcedimentosApi";
import { useAuthenticatedObjectUrl } from "../hooks/useAuthenticatedObjectUrl";
import { externalVideoEmbedUrl } from "../utils/externalVideo";

type ProtectedMediaThumbProps = {
  media: ProcedureMedia;
  size?: number;
};

export function ProtectedMediaThumb({
  media,
  size = 48,
}: ProtectedMediaThumbProps) {
  if (media.media_kind === "image") {
    return <ImageThumb src={media.content_url} size={size} alt={media.alt_text || media.title} />;
  }
  if (media.media_kind === "video_file") {
    return <VideoThumb src={media.content_url} size={size} />;
  }
  return (
    <span
      className="gp-media-thumb gp-media-thumb--icon"
      style={{ width: size, height: size }}
      title={media.external_provider || "Vídeo externo"}
    >
      <Link2 size={18} strokeWidth={1.75} aria-hidden="true" />
    </span>
  );
}

function ImageThumb({
  src,
  size,
  alt,
}: {
  src: string | null;
  size: number;
  alt: string;
}) {
  const { objectUrl, loading } = useAuthenticatedObjectUrl(src);
  if (loading) {
    return (
      <span
        className="gp-media-thumb gp-media-thumb--placeholder"
        style={{ width: size, height: size }}
      />
    );
  }
  if (!objectUrl) {
    return (
      <span
        className="gp-media-thumb gp-media-thumb--icon"
        style={{ width: size, height: size }}
      >
        <ImageIcon size={18} strokeWidth={1.75} aria-hidden="true" />
      </span>
    );
  }
  return (
    <img
      className="gp-media-thumb"
      src={objectUrl}
      alt={alt || ""}
      width={size}
      height={size}
    />
  );
}

function VideoThumb({ src, size }: { src: string | null; size: number }) {
  return (
    <span
      className="gp-media-thumb gp-media-thumb--icon"
      style={{ width: size, height: size }}
      title={src || "Vídeo"}
    >
      <Film size={18} strokeWidth={1.75} aria-hidden="true" />
    </span>
  );
}

type MediaPreviewProps = {
  media: ProcedureMedia;
};

export function MediaPreviewPlayer({ media }: MediaPreviewProps) {
  if (media.media_kind === "image") {
    return <ImagePreview src={media.content_url} alt={media.alt_text || media.title} />;
  }
  if (media.media_kind === "video_file") {
    return <VideoPreview src={media.content_url} />;
  }
  const embed = media.external_url
    ? externalVideoEmbedUrl(media.external_url, media.external_provider)
    : null;
  if (!embed) {
    return (
      <p className="gp-field__hint">
        Prévia indisponível.{" "}
        {media.external_url ? (
          <a href={media.external_url} target="_blank" rel="noopener noreferrer">
            Abrir URL
          </a>
        ) : null}
      </p>
    );
  }
  return (
    <div className="gp-media-embed">
      <iframe
        src={embed}
        title={media.title || "Vídeo externo"}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}

function ImagePreview({ src, alt }: { src: string | null; alt: string }) {
  const { objectUrl, loading, error } = useAuthenticatedObjectUrl(src);
  if (loading) return <p className="gp-field__hint">Carregando prévia…</p>;
  if (error || !objectUrl) {
    return <p className="gp-feedback gp-feedback--error">{error || "Prévia indisponível."}</p>;
  }
  return <img className="gp-media-preview-img" src={objectUrl} alt={alt || ""} />;
}

function VideoPreview({ src }: { src: string | null }) {
  const { objectUrl, loading, error } = useAuthenticatedObjectUrl(src);
  if (loading) return <p className="gp-field__hint">Carregando prévia…</p>;
  if (error || !objectUrl) {
    return <p className="gp-feedback gp-feedback--error">{error || "Prévia indisponível."}</p>;
  }
  return (
    <video
      className="gp-media-preview-video"
      src={objectUrl}
      controls
      preload="metadata"
      playsInline
    />
  );
}
