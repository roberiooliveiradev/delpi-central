const EDITOR_CLIENT_ID_KEY = "tv-dashboard:editor-presence-client-id";

type AccessTokenClaims = {
  name?: string;
  given_name?: string;
  family_name?: string;
  preferred_username?: string;
};

function clean(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.trim().replace(/\s+/g, " ");
  return normalized || null;
}

function readAccessTokenClaims(accessToken: string): AccessTokenClaims | null {
  try {
    const encoded = accessToken.split(".")[1];
    if (!encoded) return null;
    const base64 = encoded.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as AccessTokenClaims;
  } catch {
    return null;
  }
}

export function resolveEditorDisplayName(accessToken: string | undefined): string {
  if (!accessToken) return "Editor";
  const claims = readAccessTokenClaims(accessToken);
  if (!claims) return "Editor";
  const fullName = clean(claims.name);
  if (fullName) return fullName;
  const composedName = [clean(claims.given_name), clean(claims.family_name)]
    .filter(Boolean)
    .join(" ");
  return composedName || clean(claims.preferred_username) || "Editor";
}

export function getEditorPresenceClientId(): string {
  if (typeof window === "undefined") return "editor-server";
  const stored = window.sessionStorage.getItem(EDITOR_CLIENT_ID_KEY);
  if (stored) return stored;
  const generated =
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `editor-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  window.sessionStorage.setItem(EDITOR_CLIENT_ID_KEY, generated);
  return generated;
}
