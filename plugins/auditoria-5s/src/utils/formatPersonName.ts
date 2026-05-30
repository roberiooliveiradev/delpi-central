const LOWERCASE_PARTICLES = new Set(["de", "da", "do", "das", "dos", "e"]);

function capitalizeToken(token: string): string {
  if (!token) return token;
  return token.charAt(0).toLocaleUpperCase("pt-BR") + token.slice(1).toLocaleLowerCase("pt-BR");
}

function formatNameToken(token: string, tokenIndex: number): string {
  const lower = token.toLocaleLowerCase("pt-BR");
  if (tokenIndex > 0 && LOWERCASE_PARTICLES.has(lower)) {
    return lower;
  }

  return token
    .split("-")
    .map((part) => capitalizeToken(part))
    .join("-");
}

export function formatPersonName(value: string | null | undefined): string {
  if (!value?.trim()) return "";

  return value
    .trim()
    .split(/\s+/)
    .map((token, index) => formatNameToken(token, index))
    .join(" ");
}

export function formatPersonNamesList(
  value: string | null | undefined,
  fallback = "—",
): string {
  if (!value?.trim()) return fallback;

  const formatted = value
    .split(",")
    .map((part) => formatPersonName(part))
    .filter(Boolean)
    .join(", ");

  return formatted || fallback;
}
