/** Caret helpers for @ mention composers (domain-neutral). */

export type ActiveMentionQuery = {
  query: string;
  start: number;
  end: number;
};

/**
 * Detects an active `@query` ending at `cursor` (Notion-style).
 * Trigger after whitespace or start of string / open brackets.
 */
export function detectActiveMention(
  value: string,
  cursor: number,
): ActiveMentionQuery | null {
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
  displayLabel: string,
): { nextValue: string; nextCursor: number; token: string } {
  const cleaned = displayLabel.trim().replace(/\s+/g, " ");
  const token = cleaned.startsWith("@") ? cleaned : `@${cleaned}`;
  const before = value.slice(0, mentionStart);
  const after = value.slice(cursor);
  const needsSpace = after.length === 0 || !/^\s/.test(after);
  const insertion = needsSpace ? `${token} ` : token;
  const nextValue = `${before}${insertion}${after}`;
  const nextCursor = before.length + insertion.length;
  return { nextValue, nextCursor, token };
}
