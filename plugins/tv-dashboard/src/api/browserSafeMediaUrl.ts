import { getAccessToken } from "./httpClient";

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

/**
 * Anexa `access_token` para cargas nativas do browser (`<img>`, CSS, `@font-face`)
 * que não enviam `Authorization` — mesmo contrato do WS admin.
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

/** Reescreve recursivamente URLs de mídia admin em payloads de preview/miniatura. */
export function rewriteAdminMediaUrlsForBrowser<T>(value: T): T {
  const token = getAccessToken()?.trim();
  if (!token) return value;
  return rewriteNode(value) as T;
}

function rewriteNode(node: unknown): unknown {
  if (typeof node === "string") {
    return isAdminProtectedMediaUrl(node) ? withBrowserMediaAccessToken(node) : node;
  }
  if (Array.isArray(node)) {
    return node.map(rewriteNode);
  }
  if (node && typeof node === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(node as Record<string, unknown>)) {
      out[key] = rewriteNode(child);
    }
    return out;
  }
  return node;
}
