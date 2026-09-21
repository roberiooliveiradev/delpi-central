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
