/**
 * Snippet + highlight helpers for find-in-chat results (pure).
 */

export type FindHighlightSegment = {
  text: string;
  match: boolean;
};

/** Case-insensitive segments; empty query → single non-match segment. */
export function splitFindHighlightSegments(
  text: string,
  query: string,
): FindHighlightSegment[] {
  const source = String(text ?? "");
  const q = String(query ?? "").trim();
  if (!source) return [];
  if (!q) return [{ text: source, match: false }];
  const lower = source.toLowerCase();
  const needle = q.toLowerCase();
  const out: FindHighlightSegment[] = [];
  let cursor = 0;
  while (cursor < source.length) {
    const at = lower.indexOf(needle, cursor);
    if (at < 0) {
      out.push({ text: source.slice(cursor), match: false });
      break;
    }
    if (at > cursor) {
      out.push({ text: source.slice(cursor, at), match: false });
    }
    out.push({ text: source.slice(at, at + needle.length), match: true });
    cursor = at + needle.length;
  }
  return out;
}

/** Build a short snippet around the first match (±radius chars). */
export function buildFindSnippet(
  text: string,
  query: string,
  radius = 48,
): string {
  const source = String(text ?? "").replace(/\s+/g, " ").trim();
  const q = String(query ?? "").trim();
  if (!source) return "";
  if (!q) {
    return source.length > radius * 2
      ? `${source.slice(0, radius * 2)}…`
      : source;
  }
  const at = source.toLowerCase().indexOf(q.toLowerCase());
  if (at < 0) {
    return source.length > radius * 2
      ? `${source.slice(0, radius * 2)}…`
      : source;
  }
  const start = Math.max(0, at - radius);
  const end = Math.min(source.length, at + q.length + radius);
  const prefix = start > 0 ? "…" : "";
  const suffix = end < source.length ? "…" : "";
  return `${prefix}${source.slice(start, end)}${suffix}`;
}
