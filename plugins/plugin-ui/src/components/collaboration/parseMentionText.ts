/**
 * Split message body into plain text and @mention segments.
 * Known labels from the consumer win over the bare `@token` heuristic.
 */

export type MentionTextItem = {
  /** Opaque kind from the host catalog (user, order, …). */
  kind: string;
  /** Label as stored / typed (with or without leading `@`). */
  label: string;
  /** Opaque reference payload from the API — kit does not interpret. */
  ref?: Record<string, unknown> | null;
  href?: string;
  /** Native tooltip / default aria when interactive. */
  title?: string;
  id?: string;
};

export type MentionTextSegment =
  | { type: "text"; value: string }
  | { type: "mention"; value: string; item?: MentionTextItem };

/** Bare `@token` — letters, digits, underscore, dot, hyphen (Unicode-aware). */
const BARE_MENTION_PATTERN = /@([\p{L}\p{N}_][\p{L}\p{N}_.'-]*)/gu;

function normalizeLabel(label: string): string {
  return (label || "").trim().replace(/\s+/g, " ");
}

function labelVariants(label: string): string[] {
  const cleaned = normalizeLabel(label);
  if (!cleaned) return [];
  const withAt = cleaned.startsWith("@") ? cleaned : `@${cleaned}`;
  const withoutAt = withAt.slice(1);
  return withoutAt ? [withAt, withoutAt] : [withAt];
}

type Hit = {
  start: number;
  end: number;
  value: string;
  item?: MentionTextItem;
};

function findLabelHits(source: string, items: MentionTextItem[]): Hit[] {
  const hits: Hit[] = [];
  const lowerSource = source.toLowerCase();

  const ranked = [...items]
    .map((item) => ({ item, variants: labelVariants(item.label) }))
    .filter((entry) => entry.variants.length > 0)
    .sort((a, b) => {
      const aLen = Math.max(...a.variants.map((v) => v.length));
      const bLen = Math.max(...b.variants.map((v) => v.length));
      return bLen - aLen;
    });

  const occupied: Array<{ start: number; end: number }> = [];
  const overlaps = (start: number, end: number) =>
    occupied.some((range) => start < range.end && end > range.start);

  for (const { item, variants } of ranked) {
    for (const variant of variants) {
      const needle = variant.toLowerCase();
      let from = 0;
      while (from < lowerSource.length) {
        const at = lowerSource.indexOf(needle, from);
        if (at < 0) break;
        const end = at + variant.length;
        if (!overlaps(at, end)) {
          hits.push({
            start: at,
            end,
            value: source.slice(at, end),
            item,
          });
          occupied.push({ start: at, end });
        }
        from = at + 1;
      }
    }
  }

  return hits;
}

function findBareHits(source: string, occupied: Hit[]): Hit[] {
  const hits: Hit[] = [];
  const overlaps = (start: number, end: number) =>
    occupied.some((range) => start < range.end && end > range.start);

  for (const match of source.matchAll(BARE_MENTION_PATTERN)) {
    const full = match[0] ?? "";
    const start = match.index ?? 0;
    const end = start + full.length;
    if (!full || overlaps(start, end)) continue;
    hits.push({ start, end, value: full });
  }
  return hits;
}

function hitsToSegments(source: string, hits: Hit[]): MentionTextSegment[] {
  if (!source) return [];
  if (hits.length === 0) return [{ type: "text", value: source }];

  const ordered = [...hits].sort((a, b) => a.start - b.start || b.end - a.end);
  const segments: MentionTextSegment[] = [];
  let cursor = 0;

  for (const hit of ordered) {
    if (hit.start < cursor) continue;
    if (hit.start > cursor) {
      segments.push({ type: "text", value: source.slice(cursor, hit.start) });
    }
    segments.push({
      type: "mention",
      value: hit.value,
      item: hit.item,
    });
    cursor = hit.end;
  }

  if (cursor < source.length) {
    segments.push({ type: "text", value: source.slice(cursor) });
  }

  return segments.length > 0 ? segments : [{ type: "text", value: source }];
}

/**
 * Parse `text` into text/mention segments.
 * When `mentions` is provided, those labels are preferred (longest first);
 * remaining `@token` runs still become mention segments without `item`.
 */
export function parseMentionText(
  text: string,
  mentions: MentionTextItem[] | null | undefined = undefined,
): MentionTextSegment[] {
  const source = text ?? "";
  if (!source) return [];

  const items = (mentions ?? []).filter((item) => normalizeLabel(item.label));
  const labeled = findLabelHits(source, items);
  const bare = findBareHits(source, labeled);
  return hitsToSegments(source, [...labeled, ...bare]);
}
