/**
 * Canonical markdown image token parser for collaboration bodies.
 * Separates destination (href) from optional title so
 * `![a](attachment:pending:x "align=center")` does not treat the title as part of the id.
 */

const PENDING_PREFIX = "attachment:pending:";
const ATTACHMENT_PREFIX = "attachment:";

/**
 * Captures: ![alt](href) or ![alt](href "title") / ![alt](href 'title').
 * Destination stops at whitespace or `)` so titles stay out of the href.
 */
const IMAGE_TOKEN_RE =
  /!\[([^\]]*)]\(\s*([^\s)"']+)(?:\s+(?:"([^"]*)"|'([^']*)'))?\s*\)/g;

export type MarkdownImageToken = {
  alt: string;
  href: string;
  title: string;
  fullMatch: string;
  index: number;
};

export function parseMarkdownImages(markdown: string): MarkdownImageToken[] {
  const text = String(markdown ?? "");
  const out: MarkdownImageToken[] = [];
  IMAGE_TOKEN_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = IMAGE_TOKEN_RE.exec(text))) {
    const alt = String(match[1] ?? "");
    const href = String(match[2] ?? "").trim();
    const title = String(match[3] ?? match[4] ?? "").trim();
    if (!href) continue;
    out.push({
      alt,
      href,
      title,
      fullMatch: match[0],
      index: match.index,
    });
  }
  return out;
}

export function listInlinePendingIdsFromMarkdown(bodyText: string): string[] {
  const ids: string[] = [];
  const seen = new Set<string>();
  for (const token of parseMarkdownImages(bodyText)) {
    if (!token.href.startsWith(PENDING_PREFIX)) continue;
    const id = token.href.slice(PENDING_PREFIX.length).trim();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function listInlineAttachmentIdsFromMarkdown(bodyText: string): string[] {
  const ids: string[] = [];
  const seen = new Set<string>();
  for (const token of parseMarkdownImages(bodyText)) {
    if (!token.href.startsWith(ATTACHMENT_PREFIX) || token.href.startsWith(PENDING_PREFIX)) {
      continue;
    }
    const id = token.href.slice(ATTACHMENT_PREFIX.length).trim();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

/** Rewrite `attachment:pending:{id}` → `attachment:{uuid}`; drops title from pending tokens. */
export function rewriteInlinePendingInMarkdown(
  bodyText: string,
  pendingToUuid: Record<string, string>,
): string {
  const text = String(bodyText ?? "");
  if (!Object.keys(pendingToUuid).length) return text;
  IMAGE_TOKEN_RE.lastIndex = 0;
  return text.replace(IMAGE_TOKEN_RE, (full, alt: string, hrefRaw: string) => {
    const href = String(hrefRaw || "").trim();
    if (!href.startsWith(PENDING_PREFIX)) return full;
    const clientId = href.slice(PENDING_PREFIX.length).trim();
    const uuid = String(pendingToUuid[clientId] || "").trim();
    if (!uuid) return full;
    return `![${alt}](${ATTACHMENT_PREFIX}${uuid})`;
  });
}
