/** Validação client-side alinhada a validate_external_video_url da API. */

const YOUTUBE_HOSTS = new Set([
  "www.youtube.com",
  "youtube.com",
  "youtu.be",
  "m.youtube.com",
]);

const VIMEO_HOSTS = new Set([
  "vimeo.com",
  "www.vimeo.com",
  "player.vimeo.com",
]);

const GOOGLE_DRIVE_HOSTS = new Set([
  "drive.google.com",
  "www.drive.google.com",
]);

const GOOGLE_DRIVE_FILE_ID_RE = /^[A-Za-z0-9_-]{10,128}$/;

export type ExternalVideoProvider = "youtube" | "vimeo" | "google_drive";

export function parseExternalVideoUrl(
  url: string,
): { ok: true; url: string; provider: ExternalVideoProvider } | { ok: false; reason: string } {
  const raw = url.trim();
  if (!raw) {
    return { ok: false, reason: "Informe a URL do vídeo." };
  }
  if (raw.includes("<") || /iframe/i.test(raw)) {
    return { ok: false, reason: "Informe apenas a URL HTTPS, sem código HTML." };
  }
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    return { ok: false, reason: "URL inválida." };
  }
  if (parsed.protocol !== "https:") {
    return { ok: false, reason: "A URL deve usar HTTPS." };
  }
  const host = parsed.hostname.toLowerCase();
  if (YOUTUBE_HOSTS.has(host)) {
    return { ok: true, url: raw, provider: "youtube" };
  }
  if (VIMEO_HOSTS.has(host)) {
    return { ok: true, url: raw, provider: "vimeo" };
  }
  if (GOOGLE_DRIVE_HOSTS.has(host)) {
    const fileId = extractGoogleDriveFileId(parsed);
    if (!fileId) {
      return {
        ok: false,
        reason:
          "URL do Google Drive inválida. Use um link público do arquivo (ex.: /file/d/.../view).",
      };
    }
    return {
      ok: true,
      url: `https://drive.google.com/file/d/${fileId}/view`,
      provider: "google_drive",
    };
  }
  return {
    ok: false,
    reason: "Provedor não permitido. Use YouTube, Vimeo ou Google Drive.",
  };
}

/** URL de embed para prévia (não inserir iframe no HTML do artigo). */
export function externalVideoEmbedUrl(
  url: string,
  provider: ExternalVideoProvider | string | null | undefined,
): string | null {
  const resolved = provider || parseExternalVideoUrl(url);
  const kind =
    typeof resolved === "string"
      ? resolved
      : resolved && "ok" in resolved && resolved.ok
        ? resolved.provider
        : provider;
  try {
    const parsed = new URL(url);
    if (kind === "youtube" || YOUTUBE_HOSTS.has(parsed.hostname.toLowerCase())) {
      const id = extractYoutubeId(parsed);
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (kind === "vimeo" || VIMEO_HOSTS.has(parsed.hostname.toLowerCase())) {
      const id = extractVimeoId(parsed);
      return id ? `https://player.vimeo.com/video/${id}` : null;
    }
    if (
      kind === "google_drive" ||
      GOOGLE_DRIVE_HOSTS.has(parsed.hostname.toLowerCase())
    ) {
      const id = extractGoogleDriveFileId(parsed);
      return id ? `https://drive.google.com/file/d/${id}/preview` : null;
    }
  } catch {
    return null;
  }
  return null;
}

function extractYoutubeId(parsed: URL): string | null {
  if (parsed.hostname.toLowerCase() === "youtu.be") {
    const id = parsed.pathname.replace(/^\//, "").split("/")[0];
    return id || null;
  }
  const v = parsed.searchParams.get("v");
  if (v) return v;
  const parts = parsed.pathname.split("/").filter(Boolean);
  const embedIdx = parts.indexOf("embed");
  if (embedIdx >= 0 && parts[embedIdx + 1]) return parts[embedIdx + 1];
  const shortsIdx = parts.indexOf("shorts");
  if (shortsIdx >= 0 && parts[shortsIdx + 1]) return parts[shortsIdx + 1];
  return null;
}

function extractVimeoId(parsed: URL): string | null {
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts[0] === "video" && parts[1]) return parts[1];
  const numeric = parts.find((part) => /^\d+$/.test(part));
  return numeric || null;
}

function extractGoogleDriveFileId(parsed: URL): string | null {
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts[0] === "file" && parts[1] === "d" && parts[2]) {
    return GOOGLE_DRIVE_FILE_ID_RE.test(parts[2]) ? parts[2] : null;
  }
  const id = parsed.searchParams.get("id") || parsed.searchParams.get("fileId");
  if (id && GOOGLE_DRIVE_FILE_ID_RE.test(id)) return id;
  return null;
}
