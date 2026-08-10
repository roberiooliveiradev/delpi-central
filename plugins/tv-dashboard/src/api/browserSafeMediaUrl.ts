import { getAccessToken } from "./httpClient";
import { adminMediaUrl, publicPresentMediaUrl } from "./tvDashboardApi";

/**
 * Detecta URL de mídia admin protegida por JWT
 * (`/playlists/{id}/media/{assetId}`), não a rota pública.
 */
export function isAdminProtectedMediaUrl(url: string): boolean {
  const trimmed = url.trim();
  if (!trimmed) return false;
  if (trimmed.includes("/public/present/")) return false;
  return /\/playlists\/[^/]+\/media\/[^/?#]+/i.test(trimmed);
}

/** Extrai assetId de URL admin `/playlists/{id}/media/{assetId}`. */
export function extractAdminMediaAssetId(url: string): string | null {
  const match = url
    .trim()
    .match(/\/playlists\/[^/?#]+\/media\/([^/?#]+)/i);
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

/**
 * Token público a partir de `publicUrl` (`…/present/{token}`) ou valor já limpo.
 */
export function resolvePublicMediaToken(
  publicTokenOrUrl?: string | null,
): string | null {
  const raw = typeof publicTokenOrUrl === "string" ? publicTokenOrUrl.trim() : "";
  if (!raw) return null;
  if (!raw.includes("/") && !raw.includes("?")) return raw;
  try {
    const path = raw.includes("://") ? new URL(raw).pathname : raw.split("?")[0] || "";
    const match = path.match(/\/present\/([^/]+)\/?$/i);
    if (match?.[1]) return decodeURIComponent(match[1]);
  } catch {
    /* ignore */
  }
  const fallback = pathTokenFromPresent(raw);
  return fallback;
}

function pathTokenFromPresent(raw: string): string | null {
  const match = raw.match(/\/present\/([^/?#]+)/i);
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

/**
 * URL canônica para carga nativa do browser (`<img>`, `<video>`, CSS, filmstrip, prévia).
 *
 * Ordem: token público → rota `/public/present/...` (sem JWT);
 * senão admin + `access_token` (último recurso; JWT longo é frágil).
 */
export function resolveBrowserDisplayMediaUrl(
  playlistId: string,
  assetId: string,
  publicToken?: string | null,
): string {
  const asset = assetId.trim();
  const playlist = playlistId.trim();
  if (!playlist || !asset) return "";
  const token = resolvePublicMediaToken(publicToken);
  if (token) return publicPresentMediaUrl(token, asset);
  return withBrowserMediaAccessToken(adminMediaUrl(playlist, asset));
}

/**
 * Garante URL carregável sem header Authorization.
 * Com `publicToken`, reescreve admin → pública; senão anexa `access_token`.
 */
export function ensureBrowserSafeMediaUrl(
  url: string,
  options?: { publicToken?: string | null },
): string {
  const trimmed = url.trim();
  if (!trimmed) return trimmed;
  if (trimmed.includes("/public/present/")) return trimmed;

  const token = resolvePublicMediaToken(options?.publicToken);
  if (token && isAdminProtectedMediaUrl(trimmed)) {
    const assetId = extractAdminMediaAssetId(trimmed);
    if (assetId) return publicPresentMediaUrl(token, assetId);
  }
  return withBrowserMediaAccessToken(trimmed);
}

/**
 * Anexa `access_token` para cargas nativas do browser (`<img>`, CSS, `@font-face`, `<video>`)
 * que não enviam `Authorization` — mesmo contrato do WS admin.
 * Preferir `resolveBrowserDisplayMediaUrl` / `ensureBrowserSafeMediaUrl` com publicToken.
 * Não usar ao persistir config (serialize já omite url).
 */
export function withBrowserMediaAccessToken(url: string): string {
  const trimmed = url.trim();
  if (!trimmed || !isAdminProtectedMediaUrl(trimmed)) return trimmed;
  if (/(?:^|[?&])access_token=/.test(trimmed)) return trimmed;
  const token = getAccessToken()?.trim();
  if (!token) return trimmed;
  const sep = trimmed.includes("?") ? "&" : "?";
  return `${trimmed}${sep}access_token=${encodeURIComponent(token)}`;
}

/**
 * Reescreve recursivamente URLs de mídia admin em payloads de preview/miniatura.
 * Com `publicToken`, converte para `/public/present/...` (fluxo canônico).
 */
export function rewriteAdminMediaUrlsForBrowser<T>(
  value: T,
  publicToken?: string | null,
): T {
  const token = resolvePublicMediaToken(publicToken);
  if (!token && !getAccessToken()?.trim()) return value;
  return rewriteNode(value, token) as T;
}

function rewriteNode(node: unknown, publicToken: string | null): unknown {
  if (typeof node === "string") {
    return ensureBrowserSafeMediaUrl(node, { publicToken });
  }
  if (Array.isArray(node)) {
    return node.map((item) => rewriteNode(item, publicToken));
  }
  if (node && typeof node === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(node as Record<string, unknown>)) {
      out[key] = rewriteNode(child, publicToken);
    }
    return out;
  }
  return node;
}
