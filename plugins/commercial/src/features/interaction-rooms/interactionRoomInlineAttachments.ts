/**
 * Room message inline attachment helpers — list/rewrite use the kit parser
 * so `"align=…"` titles never pollute `attachment:pending:` ids.
 */
export {
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "@delpi/plugin-ui/index";

export function countFilesTowardAttachmentCap(
  pendingAttachmentCount: number,
  inlinePendingFileCount: number,
): number {
  return pendingAttachmentCount + inlinePendingFileCount;
}
