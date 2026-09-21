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
