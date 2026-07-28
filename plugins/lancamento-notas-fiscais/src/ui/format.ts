import type { ListFilters } from "../domain/types";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("pt-BR");
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value.length <= 10 ? `${value}T12:00:00` : value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("pt-BR");
}

export function formatMoney(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatDocument(
  documentNumber: string,
  series: string | null | undefined,
): string {
  const digits = String(documentNumber ?? "").replace(/\D/g, "");
  const display = digits ? digits.padStart(9, "0") : String(documentNumber ?? "");
  const serie = (series ?? "").trim();
  return serie ? `${display} / ${serie}` : display;
}

export function hasActiveFilters(
  filters: ListFilters,
  defaults?: Pick<ListFilters, "branch" | "status">,
): boolean {
  const defaultBranch = defaults?.branch;
  const defaultStatus = defaults?.status ?? "open";
  const branchDiffers =
    defaultBranch != null
      ? (filters.branch ?? "") !== defaultBranch
      : Boolean(filters.branch);
  const statusDiffers = (filters.status ?? "") !== (defaultStatus ?? "");
  return Boolean(
    branchDiffers ||
      statusDiffers ||
      (filters.supplier && filters.supplier.trim()) ||
      (filters.document && filters.document.trim()) ||
      filters.issued_from ||
      filters.issued_to ||
      filters.received_from ||
      filters.received_to,
  );
}

const EVENT_LABELS: Record<string, string> = {
  created: "Solicitação criada",
  updated: "Dados atualizados",
  status_changed: "Status alterado",
  reconciled: "Conciliada com o Protheus",
  divergence_detected: "Divergência detectada",
  manual_posted: "Marcada como lançada",
  cancelled: "Cancelada",
  comment_added: "Comentário adicionado",
  blocked: "Pendência registrada",
  resumed: "Atendimento retomado",
  started: "Atendimento iniciado",
  purchase_order_linked: "Pedido de compra amarrado",
};

export function historyEventLabel(
  eventType: string,
  toStatus?: string | null,
  fromStatus?: string | null,
): string {
  if (eventType === "status_changed" && toStatus) {
    if (toStatus === "blocked") return EVENT_LABELS.blocked;
    if (toStatus === "in_progress") {
      return fromStatus === "blocked" ? EVENT_LABELS.resumed : EVENT_LABELS.started;
    }
    if (toStatus === "posted") return "Lançada";
    if (toStatus === "cancelled") return EVENT_LABELS.cancelled;
    if (toStatus === "pending") return EVENT_LABELS.created;
  }
  return EVENT_LABELS[eventType] ?? eventType;
}

/**
 * Tom da faixa lateral do histórico — alinhado aos tons de status (`STATUS_TONES`)
 * e a eventos especiais (comentário, divergência, sistema).
 */
export function historyTimelineTone(event: {
  event_type: string;
  actor_origin?: string | null;
  to_status?: string | null;
}): string {
  const type = event.event_type;
  if (type === "comment_added") return "comment";
  if (type === "divergence_detected") return "danger";
  if (type === "cancelled") return "cancelled";
  if (type === "reconciled" || type === "manual_posted") return "posted";
  if (type === "purchase_order_linked") return "progress";
  if (type === "updated") return "updated";
  if (type === "created") return "pending";

  if (event.to_status) {
    if (event.to_status === "pending") return "pending";
    if (event.to_status === "in_progress") return "progress";
    if (event.to_status === "blocked") return "blocked";
    if (event.to_status === "posted") return "posted";
    if (event.to_status === "cancelled") return "cancelled";
  }

  if (event.actor_origin === "system") return "system";
  return "user";
}

/** Rótulo amigável de PC + data de entrega. */
export function linkedPurchaseOrderLabel(
  orderNumber: string | null | undefined,
  deliveryDate: string | null | undefined,
): string {
  const number = String(orderNumber ?? "").trim() || "—";
  const delivery = String(deliveryDate ?? "").trim();
  if (!delivery) return `PC ${number} · sem data de entrega`;
  return `PC ${number} · entrega ${formatDate(delivery)}`;
}

/** Números de PC amarrados para listagem (fila). */
export function linkedPurchaseOrderNumbersLabel(request: {
  linked_purchase_orders?: Array<{ order_number?: string | null }> | null;
  linked_po_number?: string | null;
}): string {
  const fromList = (request.linked_purchase_orders ?? [])
    .map((item) => String(item?.order_number ?? "").trim())
    .filter(Boolean);
  const numbers =
    fromList.length > 0
      ? Array.from(new Set(fromList))
      : String(request.linked_po_number ?? "").trim()
        ? [String(request.linked_po_number).trim()]
        : [];
  if (numbers.length === 0) return "—";
  if (numbers.length <= 2) return numbers.join(" · ");
  return `${numbers[0]} · +${numbers.length - 1}`;
}

/** Nome do responsável gravado em `changes.assignee_name` (string ou `{ to }`). */
export function historyAssigneeName(
  changes: Record<string, unknown> | null | undefined,
): string | null {
  if (!changes || typeof changes !== "object") return null;
  const raw = changes.assignee_name;
  if (typeof raw === "string") {
    const trimmed = raw.trim();
    return trimmed || null;
  }
  if (raw && typeof raw === "object" && "to" in raw) {
    const to = (raw as { to?: unknown }).to;
    if (typeof to === "string") {
      const trimmed = to.trim();
      return trimmed || null;
    }
  }
  return null;
}

/** Formata duração em linguagem curta (ex.: `2d 3h`, `45min`). */
export function formatDurationMs(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "—";
  const totalMinutes = Math.round(ms / 60_000);
  if (totalMinutes < 1) return "menos de 1 min";

  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  const parts: string[] = [];

  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0 && days === 0) parts.push(`${minutes}min`);
  if (parts.length === 0) parts.push(`${minutes}min`);

  return parts.join(" ");
}

type PostedTimingRequest = {
  status: string;
  received_at: string;
  reconciled_at: string | null;
};

type PostedTimingHistory = {
  event_type: string;
  to_status: string | null;
  created_at: string;
};

export function resolvePostedAt(
  request: PostedTimingRequest,
  history: PostedTimingHistory[],
): string | null {
  if (request.status !== "posted") return null;
  if (request.reconciled_at) return request.reconciled_at;

  for (let i = history.length - 1; i >= 0; i -= 1) {
    const event = history[i];
    if (
      event.to_status === "posted" ||
      event.event_type === "reconciled" ||
      event.event_type === "manual_posted"
    ) {
      return event.created_at;
    }
  }
  return null;
}

/** Tempo do recebimento físico até o lançamento (quando já postada). */
export function postingLeadTimeLabel(
  request: PostedTimingRequest,
  history: PostedTimingHistory[] = [],
): string | null {
  const postedAt = resolvePostedAt(request, history);
  if (!postedAt) return null;

  const start = new Date(request.received_at).getTime();
  const end = new Date(postedAt).getTime();
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) return null;

  return formatDurationMs(end - start);
}
