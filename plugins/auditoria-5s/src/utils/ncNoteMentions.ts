export type MentionCandidate = {
  id: string;
  name: string;
  email: string;
};

export type ActiveMention = {
  query: string;
  start: number;
  end: number;
};

export type NoteMentionSegment =
  | { type: "text"; value: string }
  | { type: "mention"; value: string };

/** Nome após @ no histórico: palavras capitalizadas + partículas (ex.: @Rodrigo de Souza). */
const MENTION_TOKEN_PATTERN =
  /@([A-ZÀ-Ý][\p{L}\p{M}'’.-]*(?:\s+(?:(?:de|da|do|das|dos|e)|[A-ZÀ-Ý][\p{L}\p{M}'’.-]*))*)/gu;

/** Detecta `@query` ativo sob o cursor no textarea. */
export function detectActiveMention(
  value: string,
  cursor: number,
): ActiveMention | null {
  const safeCursor = Math.max(0, Math.min(cursor, value.length));
  const before = value.slice(0, safeCursor);
  const match = before.match(/(^|[\s([{])@([^\s@]*)$/);
  if (!match) return null;

  const query = match[2] ?? "";
  const atIndex = before.lastIndexOf("@");
  if (atIndex < 0) return null;

  return {
    query,
    start: atIndex,
    end: safeCursor,
  };
}

export function insertMentionToken(
  value: string,
  cursor: number,
  mentionStart: number,
  displayName: string,
): { nextValue: string; nextCursor: number; token: string } {
  const token = `@${displayName.trim().replace(/\s+/g, " ")}`;
  const before = value.slice(0, mentionStart);
  const after = value.slice(cursor);
  const needsSpace = after.length === 0 || !/^\s/.test(after);
  const insertion = needsSpace ? `${token} ` : token;
  const nextValue = `${before}${insertion}${after}`;
  const nextCursor = before.length + insertion.length;
  return { nextValue, nextCursor, token };
}

export function filterMentionCandidates(
  items: MentionCandidate[],
  query: string,
  excludeIds: Set<string> = new Set(),
): MentionCandidate[] {
  const normalized = query.trim().toLowerCase();
  return items
    .filter((item) => !excludeIds.has(item.id))
    .filter((item) => {
      if (!normalized) return true;
      const name = item.name.toLowerCase();
      const email = item.email.toLowerCase();
      return name.includes(normalized) || email.includes(normalized);
    })
    .slice(0, 8);
}

/** Quebra o texto da nota em segmentos de texto e menção (sem o @ na exibição). */
export function splitNoteMentionSegments(text: string): NoteMentionSegment[] {
  const source = text ?? "";
  if (!source) return [];

  const segments: NoteMentionSegment[] = [];
  let lastIndex = 0;
  const pattern = new RegExp(MENTION_TOKEN_PATTERN.source, MENTION_TOKEN_PATTERN.flags);

  for (const match of source.matchAll(pattern)) {
    const full = match[0] ?? "";
    const name = (match[1] ?? "").trim();
    const start = match.index ?? 0;
    if (start > lastIndex) {
      segments.push({ type: "text", value: source.slice(lastIndex, start) });
    }
    if (name) {
      segments.push({ type: "mention", value: name });
    } else if (full) {
      segments.push({ type: "text", value: full });
    }
    lastIndex = start + full.length;
  }

  if (lastIndex < source.length) {
    segments.push({ type: "text", value: source.slice(lastIndex) });
  }

  return segments.length > 0 ? segments : [{ type: "text", value: source }];
}
