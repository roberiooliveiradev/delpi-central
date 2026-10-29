import type { TicketAttachment } from "../api/helpdeskApi";

/**
 * Degraded upload authorship surfacing.
 *
 * The BFF persists the document even when GLPI authorship verification
 * degrades (`author_state` = mismatch | unverified). The UI must not
 * present that as integral success — the file is kept, the divergence is
 * reported, and no automatic retry is offered (a new upload would
 * duplicate the document).
 */
export const ATTACHMENT_AUTHOR_NOTICE_TEXT =
  "O arquivo foi anexado, mas a autoria do envio não pôde ser confirmada no GLPI. " +
  "O documento está preservado e a divergência foi registrada para auditoria.";

const STAGED_NOTICE_KEY = "helpdesk:attachment-author-notice";

export function attachmentAuthorDegraded(
  attachment: Pick<TicketAttachment, "author_verified" | "outcome"> | null | undefined,
): boolean {
  if (attachment?.outcome) return attachment.outcome !== "verified";
  return attachment?.author_verified === false;
}

const STAGED_TEXT_KEY = "helpdesk:staged-ticket-notice";

/** Stage a free-text notice before navigating away (e.g. partial links). */
export function stageTicketNotice(text: string): void {
  try {
    const trimmed = text.trim();
    if (trimmed) sessionStorage.setItem(STAGED_TEXT_KEY, trimmed);
  } catch {
    /* storage unavailable — notice simply isn't staged */
  }
}

/** Consume a staged free-text notice once (ticket detail mount). */
export function consumeTicketNotice(): string | null {
  try {
    const text = sessionStorage.getItem(STAGED_TEXT_KEY);
    if (!text) return null;
    sessionStorage.removeItem(STAGED_TEXT_KEY);
    return text;
  } catch {
    return null;
  }
}

/** Stage the notice before navigating away (create flow → ticket detail). */
export function stageAttachmentAuthorNotice(): void {
  try {
    sessionStorage.setItem(STAGED_NOTICE_KEY, "1");
  } catch {
    /* storage unavailable — notice simply isn't staged */
  }
}

/** Consume a staged notice once (ticket detail mount). */
export function consumeAttachmentAuthorNotice(): string | null {
  try {
    if (!sessionStorage.getItem(STAGED_NOTICE_KEY)) return null;
    sessionStorage.removeItem(STAGED_NOTICE_KEY);
    return ATTACHMENT_AUTHOR_NOTICE_TEXT;
  } catch {
    return null;
  }
}
