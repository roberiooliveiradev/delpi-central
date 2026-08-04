/**
 * Persistência de sessão do chat embarcado (TV Copiloto).
 * Chave por surface + playlist — não muta URL do host.
 */

const STORAGE_PREFIX = "mdc.embedded.session.v1:";

export function buildEmbeddedSessionScopeKey(input: {
  surface?: string | null;
  playlistId?: string | null;
}): string {
  const surface = String(input.surface || "tv-dashboard").trim() || "tv-dashboard";
  const playlist = String(input.playlistId || "").trim() || "_default";
  return `${surface}:${playlist}`;
}

export function readEmbeddedSessionId(scopeKey: string): string | null {
  if (typeof window === "undefined") return null;
  const key = String(scopeKey || "").trim();
  if (!key) return null;
  try {
    const raw = window.localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    const id = String(raw || "").trim();
    return id || null;
  } catch {
    return null;
  }
}

export function writeEmbeddedSessionId(scopeKey: string, sessionId: string): void {
  if (typeof window === "undefined") return;
  const key = String(scopeKey || "").trim();
  const id = String(sessionId || "").trim();
  if (!key || !id) return;
  try {
    window.localStorage.setItem(`${STORAGE_PREFIX}${key}`, id);
  } catch {
    /* quota / private mode */
  }
}

export function clearEmbeddedSessionId(scopeKey: string): void {
  if (typeof window === "undefined") return;
  const key = String(scopeKey || "").trim();
  if (!key) return;
  try {
    window.localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
  } catch {
    /* ignore */
  }
}
