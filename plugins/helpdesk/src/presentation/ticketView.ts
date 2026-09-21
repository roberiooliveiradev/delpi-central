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
  created_at?: string;
  updated_at?: string;
  now?: Date;
}): TicketRecordField[] {
  const now = input.now ?? new Date();
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
      id: "created_at",
      label: "Aberto",
      value: relativeTimeLabel(input.created_at ?? "", now),
      present: Boolean(relativeTimeLabel(input.created_at ?? "", now)),
    },
    {
      id: "updated_at",
      label: "Atualizado",
      value: relativeTimeLabel(input.updated_at ?? "", now),
      present: Boolean(relativeTimeLabel(input.updated_at ?? "", now)),
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
  sort: string;
  page: number;
};

export const TICKET_STATUS_FILTERS = [
  { value: "", label: "Todos" },
  { value: "open", label: "Abertos" },
  { value: "in_progress", label: "Em atendimento" },
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
] as const;

export type TicketListSortKey = (typeof TICKET_LIST_SORTABLE_COLUMNS)[number];

const DESC_FIRST_SORT_KEYS = new Set<TicketListSortKey>(["created_at", "updated_at"]);

export function parseTicketSort(sort: string): { key: TicketListSortKey; direction: "asc" | "desc" } {
  const [field, direction] = (sort || "updated_at:desc").split(":");
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
  sort: "updated_at:desc",
  page: 1,
};

export function parseTicketListFilters(search: string): TicketListFilters {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const page = Number(params.get("page") || "1");
  return {
    q: (params.get("q") || "").trim(),
    status: (params.get("status") || "").trim(),
    urgency_id: (params.get("urgency_id") || "").trim(),
    category_id: (params.get("category_id") || "").trim(),
    updated_from: (params.get("updated_from") || "").trim(),
    updated_to: (params.get("updated_to") || "").trim(),
    sort: (params.get("sort") || DEFAULT_TICKET_LIST_FILTERS.sort).trim(),
    page: Number.isInteger(page) && page > 0 ? page : 1,
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
  if (filters.sort && filters.sort !== DEFAULT_TICKET_LIST_FILTERS.sort) params.set("sort", filters.sort);
  if (filters.page > 1) params.set("page", String(filters.page));
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
      || filters.updated_to.trim(),
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

export function statusBadgeVariant(status: string): "neutral" | "info" | "success" | "warning" | "danger" {
  const normalized = status.trim().toLocaleLowerCase("pt-BR");
  if (normalized.startsWith("novo")) return "info";
  if (normalized.includes("solucion")) return "success";
  if (normalized.includes("atendimento") || normalized.includes("atribu")) return "warning";
  if (normalized.includes("pendente") || normalized.includes("fechado")) return "neutral";
  return "neutral";
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
  created_at: string;
  requester_display_name: string;
  requester_mine?: boolean;
  timeline: {
    id: number;
    kind: string;
    content: string;
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
  createdAtLabel: string;
  authorName: string;
  mine: boolean;
  attachmentIds: number[];
};

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
  const opening: ConversationMessage = {
    id: "opening",
    kind: "opening",
    headingText: ticket.title.trim(),
    bodyText: ticket.description,
    createdAtLabel: openingTimeLabel(ticket.created_at, requester, now),
    authorName: requester,
    mine: ticket.requester_mine === true,
    attachmentIds: ticket.attachments.map((file) => file.document_id),
  };
  const followups = ticket.timeline
    .filter((entry) => entry.kind === "followup")
    .map((entry): ConversationMessage => ({
      id: String(entry.id),
      kind: "followup",
      headingText: "",
      bodyText: entry.content,
      createdAtLabel: relativeTimeLabel(entry.created_at, now),
      authorName: entry.author_display_name.trim(),
      mine: entry.mine === true,
      attachmentIds: [],
    }));
  return [opening, ...followups];
}
