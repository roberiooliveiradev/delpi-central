import { getEmojiCatalog } from "./emojiCatalog";

/**
 * Display label for a stored reaction code.
 * Catalog ids (e.g. `check`) become glyphs (`✅`); unknown codes pass through.
 */
export function reactionLabelForCode(code: string): string {
  const key = code.trim();
  if (!key) return "";
  const fromCatalog = getEmojiCatalog().find((item) => item.id === key);
  if (fromCatalog?.glyph) return fromCatalog.glyph;
  return key;
}

export type ReactionSourceRow = {
  code: string;
  user_id?: string | null;
};

export type AggregatedReactionItem = {
  code: string;
  label: string;
  count: number;
  reactedByMe?: boolean;
};

/** Group raw reaction rows into ReactionBar chips with glyph labels. */
export function aggregateReactionBarItems(
  reactions: readonly ReactionSourceRow[] | null | undefined,
  sessionUserId: string | null | undefined,
): AggregatedReactionItem[] {
  const me = (sessionUserId || "").trim();
  const counts = new Map<string, { count: number; reactedByMe: boolean }>();
  for (const row of reactions ?? []) {
    const code = String(row.code || "").trim();
    if (!code) continue;
    const current = counts.get(code) ?? { count: 0, reactedByMe: false };
    current.count += 1;
    if (me && String(row.user_id || "").trim() === me) {
      current.reactedByMe = true;
    }
    counts.set(code, current);
  }
  return [...counts.entries()]
    .map(([code, value]) => ({
      code,
      label: reactionLabelForCode(code),
      count: value.count,
      reactedByMe: value.reactedByMe,
    }))
    .sort((a, b) => a.code.localeCompare(b.code));
}
