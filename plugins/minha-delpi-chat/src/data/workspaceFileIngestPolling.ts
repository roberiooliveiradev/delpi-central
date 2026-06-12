import type { ChatAttachment } from "./api/chatTypes";
import { fetchChatSessionAttachments } from "./api/chatApi";

/**
 * Polling canônico de ingestão (Playbook 17).
 * Hoje: família `session_attachment`. Agent/project aguardam status na API.
 */
export type WorkspaceFileIngestFamily = "session_attachment" | "agent_source" | "project_source";

type ChatApiOptions = NonNullable<Parameters<typeof fetchChatSessionAttachments>[1]>;

const TERMINAL_ATTACHMENT_STATUSES = new Set([
  "indexed",
  "unsupported",
  "index_failed",
]);

export function isAttachmentIndexPending(status?: string | null): boolean {
  const normalized = String(status || "").trim().toLowerCase();
  return normalized === "indexing" || normalized === "uploaded";
}

export function isTerminalAttachmentStatus(status?: string | null): boolean {
  return TERMINAL_ATTACHMENT_STATUSES.has(String(status || "").trim().toLowerCase());
}

export async function waitForSessionAttachmentIndexed(
  sessionId: string,
  attachmentId: string,
  options: ChatApiOptions = {},
  pollOptions: {
    intervalMs?: number;
    timeoutMs?: number;
  } = {},
): Promise<ChatAttachment | null> {
  const intervalMs = pollOptions.intervalMs ?? 2000;
  const timeoutMs = pollOptions.timeoutMs ?? 120000;
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const attachments = await fetchChatSessionAttachments(sessionId, options);
    const match = attachments.find((item) => item.id === attachmentId);

    if (match && !isAttachmentIndexPending(match.status)) {
      return match;
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  return null;
}

export async function waitForSessionAttachmentsIndexed(
  sessionId: string,
  attachmentIds: string[],
  options: ChatApiOptions = {},
  pollOptions?: {
    intervalMs?: number;
    timeoutMs?: number;
  },
): Promise<ChatAttachment[]> {
  if (attachmentIds.length === 0) {
    return [];
  }

  const settled = await Promise.all(
    attachmentIds.map((attachmentId) =>
      waitForSessionAttachmentIndexed(sessionId, attachmentId, options, pollOptions),
    ),
  );

  return settled.filter((item): item is ChatAttachment => item !== null);
}
