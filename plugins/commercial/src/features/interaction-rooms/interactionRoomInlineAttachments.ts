/**
 * Room message inline attachment helpers — list/rewrite use the kit parser
 * so `"align=…"` titles never pollute `attachment:pending:` ids.
 */
import {
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  parseMarkdownImages,
  rewriteInlinePendingInMarkdown,
} from "@delpi/plugin-ui/index";

export {
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
};

export function countFilesTowardAttachmentCap(
  pendingAttachmentCount: number,
  inlinePendingFileCount: number,
): number {
  return pendingAttachmentCount + inlinePendingFileCount;
}

/** Drop `attachment:pending:` tokens whose File was not restored from draft. */
export function stripMissingInlinePendingFromMarkdown(
  bodyText: string,
  availablePendingIds: ReadonlySet<string>,
): string {
  const tokens = parseMarkdownImages(bodyText);
  let out = bodyText;
  for (const token of tokens) {
    if (!token.href.startsWith("attachment:pending:")) continue;
    const id = token.href.slice("attachment:pending:".length).trim();
    if (availablePendingIds.has(id)) continue;
    out = out.split(token.fullMatch).join("");
  }
  return out.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n");
}
