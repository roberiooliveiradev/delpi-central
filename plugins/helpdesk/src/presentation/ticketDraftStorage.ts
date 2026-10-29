/** Session drafts for create/reply — survive F5, clear on successful send or tab close. */

export type HelpdeskCreateDraftAssignee = {
  id: string;
  name: string;
  email: string;
  directoryUserId?: string;
  hasPhoto?: boolean;
};

export type HelpdeskCreateDraftItemLink = {
  itemtype: string;
  itemsId: number;
  name: string;
  typeLabel?: string;
};

export type HelpdeskCreateDraftRelatedTicket = {
  id: number;
  title: string;
};

export type HelpdeskCreateDraft = {
  title: string;
  description: string;
  observerIdsInput: string;
  assigneeId: string;
  /** Snapshot do técnico — evita «Usuário {id}» no F5. */
  assigneeName: string;
  assigneeEmail: string;
  assigneeDirectoryUserId: string;
  assigneeHasPhoto: boolean;
  categoryId: string;
  urgencyId: string;
  /** Etapa 1 — governed GLPI classification + link selections. */
  typeId: string;
  impactId: string;
  requestTypeId: string;
  itemLinks: HelpdeskCreateDraftItemLink[];
  relatedTickets: HelpdeskCreateDraftRelatedTicket[];
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

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function assigneeFromCreateDraft(
  draft: HelpdeskCreateDraft | null | undefined,
): HelpdeskCreateDraftAssignee | null {
  const id = (draft?.assigneeId || "").trim();
  if (!id) return null;
  const name = (draft?.assigneeName || "").trim() || `Usuário ${id}`;
  return {
    id,
    name,
    email: (draft?.assigneeEmail || "").trim(),
    directoryUserId: (draft?.assigneeDirectoryUserId || "").trim() || undefined,
    hasPhoto: Boolean(draft?.assigneeHasPhoto),
  };
}

export function readCreateDraft(): HelpdeskCreateDraft | null {
  const draft = readJson<Partial<HelpdeskCreateDraft>>(CREATE_KEY);
  if (!draft || typeof draft !== "object") return null;
  return {
    title: asString(draft.title),
    description: asString(draft.description),
    observerIdsInput: asString(draft.observerIdsInput),
    assigneeId: asString(draft.assigneeId),
    assigneeName: asString(draft.assigneeName),
    assigneeEmail: asString(draft.assigneeEmail),
    assigneeDirectoryUserId: asString(draft.assigneeDirectoryUserId),
    assigneeHasPhoto: Boolean(draft.assigneeHasPhoto),
    categoryId: asString(draft.categoryId),
    urgencyId: asString(draft.urgencyId),
    typeId: asString(draft.typeId),
    impactId: asString(draft.impactId),
    requestTypeId: asString(draft.requestTypeId),
    itemLinks: itemLinksFromDraft(draft.itemLinks),
    relatedTickets: relatedTicketsFromDraft(draft.relatedTickets),
  };
}

function itemLinksFromDraft(value: unknown): HelpdeskCreateDraftItemLink[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((row) => {
      if (!row || typeof row !== "object") return null;
      const entry = row as Record<string, unknown>;
      const itemsId = Number(entry.itemsId);
      const itemtype = asString(entry.itemtype).trim();
      if (!itemtype || !Number.isInteger(itemsId) || itemsId <= 0) return null;
      return {
        itemtype,
        itemsId,
        name: asString(entry.name),
        typeLabel: asString(entry.typeLabel) || undefined,
      };
    })
    .filter((row): row is HelpdeskCreateDraftItemLink => row !== null);
}

function relatedTicketsFromDraft(value: unknown): HelpdeskCreateDraftRelatedTicket[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((row) => {
      if (!row || typeof row !== "object") return null;
      const entry = row as Record<string, unknown>;
      const id = Number(entry.id);
      if (!Number.isInteger(id) || id <= 0) return null;
      return { id, title: asString(entry.title) };
    })
    .filter((row): row is HelpdeskCreateDraftRelatedTicket => row !== null);
}

export function writeCreateDraft(draft: HelpdeskCreateDraft): void {
  const empty =
    !draft.title.trim() &&
    !draft.description.trim() &&
    !draft.observerIdsInput.trim() &&
    !draft.assigneeId &&
    !draft.categoryId &&
    !draft.urgencyId &&
    !draft.typeId &&
    !draft.impactId &&
    !draft.requestTypeId &&
    draft.itemLinks.length === 0 &&
    draft.relatedTickets.length === 0;
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
