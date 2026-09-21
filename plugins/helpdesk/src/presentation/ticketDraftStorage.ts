/** Session drafts for create/reply — survive F5, clear on successful send or tab close. */

export type HelpdeskCreateDraft = {
  title: string;
  description: string;
  observerIdsInput: string;
  categoryId: string;
  urgencyId: string;
};

const CREATE_KEY = "helpdesk:ticket-create-draft:v1";

function replyKey(ticketId: string): string {
  return `helpdesk:ticket-reply-draft:v1:${ticketId}`;
}

function readJson<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function writeJson(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* quota / private mode — ignore */
  }
}

export function readCreateDraft(): HelpdeskCreateDraft | null {
  const draft = readJson<Partial<HelpdeskCreateDraft>>(CREATE_KEY);
  if (!draft || typeof draft !== "object") return null;
  return {
    title: typeof draft.title === "string" ? draft.title : "",
    description: typeof draft.description === "string" ? draft.description : "",
    observerIdsInput: typeof draft.observerIdsInput === "string" ? draft.observerIdsInput : "",
    categoryId: typeof draft.categoryId === "string" ? draft.categoryId : "",
    urgencyId: typeof draft.urgencyId === "string" ? draft.urgencyId : "",
  };
}

export function writeCreateDraft(draft: HelpdeskCreateDraft): void {
  const empty =
    !draft.title.trim() &&
    !draft.description.trim() &&
    !draft.observerIdsInput.trim() &&
    !draft.categoryId &&
    !draft.urgencyId;
  if (empty) {
    clearCreateDraft();
    return;
  }
  writeJson(CREATE_KEY, draft);
}

export function clearCreateDraft(): void {
  try {
    sessionStorage.removeItem(CREATE_KEY);
  } catch {
    /* ignore */
  }
}

export function readReplyDraft(ticketId: string): string {
  const draft = readJson<{ content?: string }>(replyKey(ticketId));
  return typeof draft?.content === "string" ? draft.content : "";
}

export function writeReplyDraft(ticketId: string, content: string): void {
  if (!content.trim()) {
    clearReplyDraft(ticketId);
    return;
  }
  writeJson(replyKey(ticketId), { content });
}

export function clearReplyDraft(ticketId: string): void {
  try {
    sessionStorage.removeItem(replyKey(ticketId));
  } catch {
    /* ignore */
  }
}
