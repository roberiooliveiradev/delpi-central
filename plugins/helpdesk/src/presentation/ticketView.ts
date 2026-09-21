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

export function ticketRecordFields(category: string, urgency: string): TicketRecordField[] {
  return [
    { id: "category", label: "Categoria", value: category, present: category.trim().length > 0 },
    { id: "urgency", label: "Urgência", value: urgency, present: urgency.trim().length > 0 },
  ];
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
  timeline: {
    id: number;
    kind: string;
    content: string;
    created_at: string;
    author_display_name: string;
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

function writtenByRequester(author: string, requester: string): boolean {
  const authorName = author.trim();
  const requesterName = requester.trim();
  return requesterName.length > 0 && authorName === requesterName;
}

export function conversationMessages(ticket: ConversationSource, now: Date): ConversationMessage[] {
  const requester = ticket.requester_display_name.trim();
  const opening: ConversationMessage = {
    id: "opening",
    kind: "opening",
    headingText: ticket.title.trim(),
    bodyText: ticket.description,
    createdAtLabel: relativeTimeLabel(ticket.created_at, now),
    authorName: requester,
    mine: requester.length > 0,
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
      mine: writtenByRequester(entry.author_display_name, requester),
      attachmentIds: [],
    }));
  return [opening, ...followups];
}
