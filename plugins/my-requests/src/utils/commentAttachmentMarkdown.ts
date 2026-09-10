/**
 * Embed uploaded conversation images into markdown so MessageThread can render them.
 * Clip (paperclip) uploads are not caret-inline; they must be appended as attachment: tokens.
 */

export function sanitizeAttachmentAlt(fileName: string | null | undefined): string {
  const cleaned = (fileName || "")
    .replace(/[\[\]]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned || "imagem";
}

export function appendAttachmentMarkdown(
  body: string,
  attachments: ReadonlyArray<{ id: string; fileName: string }>,
): string {
  let next = (body || "").trim();
  for (const item of attachments) {
    const id = (item.id || "").trim();
    if (!id) continue;
    const token = `![${sanitizeAttachmentAlt(item.fileName)}](attachment:${id})`;
    next = next ? `${next}\n\n${token}` : token;
  }
  return next;
}
