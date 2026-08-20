/** Client helpers for inline `attachment:` / `pending:` in room message markdown. */

const IMAGE_RE = /!\[([^\]]*)]\(([^)]+)\)/g;
const PENDING_PREFIX = "attachment:pending:";
const ATTACHMENT_PREFIX = "attachment:";

export function listInlinePendingIdsFromMarkdown(bodyText: string): string[] {
  const text = String(bodyText ?? "");
  const ids: string[] = [];
  const seen = new Set<string>();
  IMAGE_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = IMAGE_RE.exec(text))) {
    const href = String(match[2] || "").trim();
    if (!href.startsWith(PENDING_PREFIX)) continue;
    const id = href.slice(PENDING_PREFIX.length);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function listInlineAttachmentIdsFromMarkdown(bodyText: string): string[] {
  const text = String(bodyText ?? "");
  const ids: string[] = [];
  const seen = new Set<string>();
  IMAGE_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = IMAGE_RE.exec(text))) {
    const href = String(match[2] || "").trim();
    if (!href.startsWith(ATTACHMENT_PREFIX) || href.startsWith(PENDING_PREFIX)) {
      continue;
    }
    const id = href.slice(ATTACHMENT_PREFIX.length);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function rewriteInlinePendingInMarkdown(
  bodyText: string,
  pendingToUuid: Record<string, string>,
): string {
  const text = String(bodyText ?? "");
  if (!Object.keys(pendingToUuid).length) return text;
  return text.replace(IMAGE_RE, (full, alt: string, hrefRaw: string) => {
    const href = String(hrefRaw || "").trim();
    if (!href.startsWith(PENDING_PREFIX)) return full;
    const clientId = href.slice(PENDING_PREFIX.length);
    const uuid = String(pendingToUuid[clientId] || "").trim();
    if (!uuid) return full;
    return `![${alt}](${ATTACHMENT_PREFIX}${uuid})`;
  });
}

export function countFilesTowardAttachmentCap(
  pendingAttachmentCount: number,
  inlinePendingFileCount: number,
): number {
  return pendingAttachmentCount + inlinePendingFileCount;
}
