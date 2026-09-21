export type TicketListView =
  | "loading"
  | "forbidden"
  | "link"
  | "empty"
  | "list"
  | "unavailable"
  | "error";

export function viewForTicketLoad(input: {
  loading: boolean;
  errorCode?: string | null;
  itemCount: number;
  filterActive?: boolean;
}): TicketListView {
  if (input.loading) return "loading";
  if (input.errorCode === "forbidden" || input.errorCode === "glpi_forbidden") {
    return "forbidden";
  }
  if (input.errorCode === "glpi_link_required") return "link";
  if (input.errorCode === "glpi_unavailable") return "unavailable";
  if (input.errorCode) return "error";
  if (input.itemCount === 0) return "empty";
  return "list";
}

export type TicketRecordField = {
  id: string;
  label: string;
  value: string;
  present: boolean;
};

export function ticketRecordFields(input: {
  id: number;
  category: string;
  urgency: string;
  assigned_display_name?: string;
  observers_display_name?: string;
  created_at?: string;
  updated_at?: string;
  solved_at?: string;
  closed_at?: string;
  sla_ttr?: string;
  sla_tto?: string;
}): TicketRecordField[] {
  const created = absoluteDateTimeLabel(input.created_at ?? "");
  const updated = absoluteDateTimeLabel(input.updated_at ?? "");
  const solved = absoluteDateTimeLabel(input.solved_at ?? "");
  const closed = absoluteDateTimeLabel(input.closed_at ?? "");
  const observers = (input.observers_display_name ?? "").trim();
  const ttr = (input.sla_ttr ?? "").trim();
  const tto = (input.sla_tto ?? "").trim();
  return [
    { id: "id", label: "Chamado", value: String(input.id), present: input.id > 0 },
    { id: "category", label: "Categoria", value: input.category, present: input.category.trim().length > 0 },
    { id: "urgency", label: "Urgência", value: input.urgency, present: input.urgency.trim().length > 0 },
    {
      id: "assigned",
      label: "Técnico",
      value: (input.assigned_display_name ?? "").trim(),
      present: (input.assigned_display_name ?? "").trim().length > 0,
    },
    {
      id: "observers",
      label: "Observador",
      value: observers,
      present: observers.length > 0,
    },
    {
      id: "sla_tto",
      label: "TTO",
      value: tto,
      present: tto.length > 0,
    },
    {
      id: "sla_ttr",
      label: "TTR",
      value: ttr,
      present: ttr.length > 0,
    },
    {
      id: "created_at",
      label: "Aberto",
      value: created,
      present: Boolean(created),
    },
    {
      id: "updated_at",
      label: "Atualizado",
      value: updated,
      present: Boolean(updated),
    },
    {
      id: "solved_at",
      label: "Resolvido",
      value: solved,
      present: Boolean(solved),
    },
    {
      id: "closed_at",
      label: "Fechado",
      value: closed,
      present: Boolean(closed),
    },
  ];
}

export type TicketListFilters = {
  q: string;
  status: string;
  urgency_id: string;
  category_id: string;
  updated_from: string;
  updated_to: string;
  created_from: string;
  created_to: string;
  sort: string;
  page: number;
  page_size: number;
};

export const TICKET_PAGE_SIZE_OPTIONS = [
  { value: "10", label: "10 por página" },
  { value: "20", label: "20 por página" },
  { value: "50", label: "50 por página" },
] as const;

const ALLOWED_PAGE_SIZES = new Set([10, 20, 50]);

export const TICKET_STATUS_FILTERS = [
  { value: "", label: "Todos" },
  { value: "open", label: "Abertos" },
  { value: "in_progress", label: "Em atendimento" },
  { value: "pending", label: "Pendentes" },
  { value: "approval", label: "Aguardando aprovação" },
  { value: "solved", label: "Solucionados" },
  { value: "closed", label: "Fechados" },
] as const;

export const TICKET_LIST_SORTABLE_COLUMNS = [
  "id",
  "title",
  "status",
  "category",
  "urgency",
  "created_at",
  "updated_at",
  "solved_at",
] as const;

export type TicketListSortKey = (typeof TICKET_LIST_SORTABLE_COLUMNS)[number];

const DESC_FIRST_SORT_KEYS = new Set<TicketListSortKey>(["created_at", "updated_at", "solved_at"]);

export function parseTicketSort(sort: string): { key: TicketListSortKey; direction: "asc" | "desc" } {
  const primary = (sort || "updated_at:desc").split(",")[0]?.trim() || "updated_at:desc";
  const [field, direction] = primary.split(":");
  const key = TICKET_LIST_SORTABLE_COLUMNS.includes(field as TicketListSortKey)
    ? (field as TicketListSortKey)
    : "updated_at";
  return { key, direction: direction === "asc" ? "asc" : "desc" };
}

export function nextTicketSort(current: string, columnKey: string): string {
  if (!TICKET_LIST_SORTABLE_COLUMNS.includes(columnKey as TicketListSortKey)) return current;
  const parsed = parseTicketSort(current);
  if (parsed.key === columnKey) {
    return `${columnKey}:${parsed.direction === "asc" ? "desc" : "asc"}`;
  }
  const direction = DESC_FIRST_SORT_KEYS.has(columnKey as TicketListSortKey) ? "desc" : "asc";
  return `${columnKey}:${direction}`;
}

export const DEFAULT_TICKET_LIST_FILTERS: TicketListFilters = {
  q: "",
  status: "",
  urgency_id: "",
  category_id: "",
  updated_from: "",
  updated_to: "",
  created_from: "",
  created_to: "",
  sort: "updated_at:desc",
  page: 1,
  page_size: 20,
};

export function parseTicketListFilters(search: string): TicketListFilters {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const page = Number(params.get("page") || "1");
  const pageSize = Number(params.get("page_size") || String(DEFAULT_TICKET_LIST_FILTERS.page_size));
  return {
    q: (params.get("q") || "").trim(),
    status: (params.get("status") || "").trim(),
    urgency_id: (params.get("urgency_id") || "").trim(),
    category_id: (params.get("category_id") || "").trim(),
    updated_from: (params.get("updated_from") || "").trim(),
    updated_to: (params.get("updated_to") || "").trim(),
    created_from: (params.get("created_from") || "").trim(),
    created_to: (params.get("created_to") || "").trim(),
    sort: (params.get("sort") || DEFAULT_TICKET_LIST_FILTERS.sort).trim(),
    page: Number.isInteger(page) && page > 0 ? page : 1,
    page_size: ALLOWED_PAGE_SIZES.has(pageSize) ? pageSize : DEFAULT_TICKET_LIST_FILTERS.page_size,
  };
}

export function ticketListSearch(filters: TicketListFilters): string {
  const params = new URLSearchParams();
  if (filters.q.trim()) params.set("q", filters.q.trim());
  if (filters.status.trim()) params.set("status", filters.status.trim());
  if (filters.urgency_id.trim()) params.set("urgency_id", filters.urgency_id.trim());
  if (filters.category_id.trim()) params.set("category_id", filters.category_id.trim());
  if (filters.updated_from.trim()) params.set("updated_from", filters.updated_from.trim());
  if (filters.updated_to.trim()) params.set("updated_to", filters.updated_to.trim());
  if (filters.created_from.trim()) params.set("created_from", filters.created_from.trim());
  if (filters.created_to.trim()) params.set("created_to", filters.created_to.trim());
  if (filters.sort && filters.sort !== DEFAULT_TICKET_LIST_FILTERS.sort) params.set("sort", filters.sort);
  if (filters.page > 1) params.set("page", String(filters.page));
  if (filters.page_size !== DEFAULT_TICKET_LIST_FILTERS.page_size) {
    params.set("page_size", String(filters.page_size));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function isTicketFilterActive(filters: TicketListFilters): boolean {
  return Boolean(
    filters.q.trim()
      || filters.status.trim()
      || filters.urgency_id.trim()
      || filters.category_id.trim()
      || filters.updated_from.trim()
      || filters.updated_to.trim()
      || filters.created_from.trim()
      || filters.created_to.trim(),
  );
}

export function detailRecordHeading(category: string, urgency: string): { title: string; subtitle?: string } {
  const categoryName = category.trim();
  const urgencyName = urgency.trim();
  if (categoryName) {
    return { title: categoryName, subtitle: urgencyName || undefined };
  }
  return { title: urgencyName || "Chamado" };
}

const STATUS_BADGE_BY_ID: Record<number, "neutral" | "info" | "success" | "warning" | "danger"> = {
  1: "info",
  2: "warning",
  3: "warning",
  4: "neutral",
  5: "success",
  6: "neutral",
  10: "warning",
};

export function statusBadgeVariant(statusId?: number | null): "neutral" | "info" | "success" | "warning" | "danger" {
  if (statusId == null) return "neutral";
  return STATUS_BADGE_BY_ID[statusId] ?? "neutral";
}

export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `helpdesk-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export type ConversationSource = {
  title: string;
  description: string;
  description_html?: string;
  created_at: string;
  requester_display_name: string;
  requester_mine?: boolean;
  timeline: {
    id: number;
    kind: string;
    content: string;
    content_html?: string;
    created_at: string;
    author_display_name: string;
    mine?: boolean;
  }[];
  attachments: { document_id: number }[];
};

export type ConversationMessage = {
  id: string;
  kind: "opening" | "followup";
  headingText: string;
  bodyText: string;
  bodyHtml: string;
  createdAtLabel: string;
  authorName: string;
  mine: boolean;
  attachmentIds: number[];
};

/** Marks BFF attachment URLs so MessageThread can resolve blobs and handle clicks. */
export function stampHelpdeskAttachmentIds(html: string): string {
  return String(html || "").replace(
    /src=(["'])(\/apps\/helpdesk-api\/tickets\/\d+\/attachments\/(\d+))\1/gi,
    (_full, quote: string, src: string, documentId: string) =>
      `src=${quote}${src}${quote} data-attachment-id=${quote}${documentId}${quote}`,
  );
}

/** True when rich-text HTML still has visible characters after stripping tags. */
/** Parses optional GLPI user ids from a comma/space separated field. */
export function parseObserverIdsInput(raw: string): number[] {
  const ids: number[] = [];
  const seen = new Set<number>();
  for (const token of String(raw || "").split(/[\s,;]+/)) {
    if (!token) continue;
    const id = Number(token);
    if (!Number.isInteger(id) || id <= 0 || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function hasVisibleRichText(html: string): boolean {
  const plain = String(html || "")
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return plain.length > 0;
}

export function listHelpdeskAttachmentIdsInHtml(html: string): number[] {
  const ids: number[] = [];
  const seen = new Set<number>();
  const re = /\/apps\/helpdesk-api\/tickets\/\d+\/attachments\/(\d+)/gi;
  let match: RegExpExecArray | null;
  while ((match = re.exec(String(html || "")))) {
    const id = Number(match[1]);
    if (!Number.isFinite(id) || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function relativeTimeLabel(value: string, now: Date): string {
  const trimmed = value.trim();
  const instant = Date.parse(trimmed);
  if (!trimmed || Number.isNaN(instant)) return "";
  const elapsed = now.getTime() - instant;
  const minute = 60_000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (elapsed < minute) return "agora";
  if (elapsed < hour) {
    const count = Math.floor(elapsed / minute);
    return count === 1 ? "1 minuto atrás" : `${count} minutos atrás`;
  }
  if (elapsed < day) {
    const count = Math.floor(elapsed / hour);
    return count === 1 ? "1 hora atrás" : `${count} horas atrás`;
  }
  if (elapsed < 7 * day) {
    const count = Math.floor(elapsed / day);
    return count === 1 ? "1 dia atrás" : `${count} dias atrás`;
  }
  const date = new Date(instant);
  const dayOfMonth = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${dayOfMonth}/${month}/${date.getFullYear()}`;
}

export function absoluteDateTimeLabel(value: string): string {
  const trimmed = value.trim();
  const instant = Date.parse(trimmed);
  if (!trimmed || Number.isNaN(instant)) return "";
  const date = new Date(instant);
  const dayOfMonth = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${dayOfMonth}/${month}/${date.getFullYear()} ${hours}:${minutes}`;
}

function openingTimeLabel(createdAt: string, requester: string, now: Date): string {
  const time = relativeTimeLabel(createdAt, now);
  if (!time) return requester ? `por ${requester}` : "";
  return `Criado em ${time}`;
}

export function conversationAuthorSrc(mine: boolean, photoUrl: string | null | undefined): string | undefined {
  if (!mine) return undefined;
  const src = (photoUrl ?? "").trim();
  return src || undefined;
}

export function conversationMessages(ticket: ConversationSource, now: Date): ConversationMessage[] {
  const requester = ticket.requester_display_name.trim();
  const openingHtml = stampHelpdeskAttachmentIds(ticket.description_html || "");
  const opening: ConversationMessage = {
    id: "opening",
    kind: "opening",
    headingText: ticket.title.trim(),
    bodyText: ticket.description,
    bodyHtml: openingHtml,
    createdAtLabel: openingTimeLabel(ticket.created_at, requester, now),
    authorName: requester,
    mine: ticket.requester_mine === true,
    attachmentIds: ticket.attachments.map((file) => file.document_id),
  };
  const followups = ticket.timeline
    .filter((entry) => entry.kind === "followup")
    .map((entry): ConversationMessage => {
      const bodyHtml = stampHelpdeskAttachmentIds(entry.content_html || "");
      return {
        id: String(entry.id),
        kind: "followup",
        headingText: "",
        bodyText: entry.content,
        bodyHtml,
        createdAtLabel: relativeTimeLabel(entry.created_at, now),
        authorName: entry.author_display_name.trim(),
        mine: entry.mine === true,
        attachmentIds: [],
      };
    });
  return [opening, ...followups];
}
