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

export function hasActiveFilters(filters: ListFilters): boolean {
  return Boolean(
    filters.branch ||
      filters.status ||
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
};

export function historyEventLabel(eventType: string): string {
  return EVENT_LABELS[eventType] ?? eventType;
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
