/** Limites espelhados de `tv_dashboard_settings.json` → mediaUpload. */
export const MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024;
export const MAX_VIDEO_UPLOAD_BYTES = 500 * 1024 * 1024;
export const MAX_FONT_UPLOAD_BYTES = 5 * 1024 * 1024;
/** Abaixo do teto ~100 MB do Cloudflare Free/Pro (multipart + margem). */
export const EDGE_SAFE_UPLOAD_CHUNK_BYTES = 90 * 1024 * 1024;

export function mediaUploadLimitMb(bytes: number = MAX_VIDEO_UPLOAD_BYTES): number {
  return Math.max(1, Math.floor(bytes / (1024 * 1024)));
}

const IMAGE_MIME = new Set([
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/svg+xml",
]);
const VIDEO_MIME = new Set(["video/mp4", "video/webm"]);
const FONT_MIME = new Set([
  "font/woff2",
  "font/ttf",
  "font/otf",
  "application/font-woff2",
  "application/x-font-ttf",
]);

export type MediaUploadKind = "image" | "video" | "font";

export function detectMediaUploadKind(file: File): MediaUploadKind | null {
  const mime = (file.type || "").split(";", 1)[0]!.trim().toLowerCase();
  if (IMAGE_MIME.has(mime)) return "image";
  if (VIDEO_MIME.has(mime)) return "video";
  if (FONT_MIME.has(mime)) return "font";
  const name = file.name.toLowerCase();
  if (/\.(jpe?g|png|webp|gif|svg)$/.test(name)) return "image";
  if (/\.(mp4|webm)$/.test(name)) return "video";
  if (/\.(woff2|ttf|otf)$/.test(name)) return "font";
  return null;
}

export function maxBytesForMediaKind(kind: MediaUploadKind): number {
  if (kind === "video") return MAX_VIDEO_UPLOAD_BYTES;
  if (kind === "font") return MAX_FONT_UPLOAD_BYTES;
  return MAX_IMAGE_UPLOAD_BYTES;
}

/** Valida tipo/tamanho antes do POST. Devolve mensagem PT ou null se ok. */
export function validateMediaUploadFile(
  file: File,
  allowedKinds?: MediaUploadKind[],
): string | null {
  const kind = detectMediaUploadKind(file);
  if (!kind) {
    return "Formato não suportado. Envie JPG, PNG, WEBP, GIF, SVG, MP4 ou WEBM.";
  }
  if (allowedKinds && !allowedKinds.includes(kind)) {
    if (allowedKinds.includes("video") && !allowedKinds.includes("image")) {
      return "Envie um vídeo MP4 ou WEBM.";
    }
    if (allowedKinds.includes("image") && !allowedKinds.includes("video")) {
      return "Envie uma imagem JPG, PNG, WEBP, GIF ou SVG.";
    }
    return "Tipo de arquivo não permitido neste contexto.";
  }
  const max = maxBytesForMediaKind(kind);
  if (file.size > max) {
    return `Arquivo acima do limite de ${mediaUploadLimitMb(max)} MB.`;
  }
  if (file.size <= 0) {
    return "Arquivo vazio.";
  }
  return null;
}

export function mediaUploadHttpErrorMessage(status: number, fallback: string): string {
  if (status === 413) {
    return (
      `Arquivo grande demais para a borda de rede (limite intermediário ~100 MB por requisição). ` +
      `O editor envia vídeos grandes em partes; se o erro persistir, tente novamente ou contate o suporte. ` +
      `(limite do Painéis TV: ${mediaUploadLimitMb()} MB).`
    );
  }
  return fallback;
}
