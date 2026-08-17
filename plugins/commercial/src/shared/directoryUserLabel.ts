/** Rótulo amigável de usuário do diretório — nunca exibe UUID/id bruto. */

export type DirectoryUserLabelParts = {
  name?: string | null;
  email?: string | null;
};

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function looksLikeUserId(value: string): boolean {
  const normalized = value.trim();
  if (!normalized) return false;
  return UUID_RE.test(normalized);
}

function safePart(value: string | null | undefined): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed || looksLikeUserId(trimmed)) return "";
  return trimmed;
}

export function formatDirectoryUserLabel(parts: DirectoryUserLabelParts): string {
  const name = safePart(parts.name);
  const email = safePart(parts.email);
  if (name && email) return `${name} · ${email}`;
  if (name) return name;
  if (email) return email;
  return "";
}

/** Fallback seguro quando o diretório não resolve (nunca o id). */
export function directoryUserLabelOrFallback(
  parts: DirectoryUserLabelParts,
  fallback?: string | null,
): string {
  const primary = formatDirectoryUserLabel(parts);
  if (primary) return primary;
  const alt = safePart(fallback);
  if (alt) return alt;
  return "Usuário";
}
