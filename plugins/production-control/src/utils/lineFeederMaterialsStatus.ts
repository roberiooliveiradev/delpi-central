import type { LineFeederStatus } from "../types";

export function materialStatusLabel(status: LineFeederStatus): string {
  switch (status) {
    case "covered":
      return "Já na fábrica";
    case "to_pick":
      return "A coletar";
    case "at_risk":
      return "Em risco";
    case "unknown":
      return "Estoque indisponível";
    default:
      return status;
  }
}

export function materialBadgeVariant(
  status: LineFeederStatus,
): "success" | "warning" | "danger" | "neutral" {
  switch (status) {
    case "covered":
      return "success";
    case "to_pick":
      return "warning";
    case "at_risk":
      return "danger";
    default:
      return "neutral";
  }
}

export type MaterialsListFilter = "to_collect" | "at_risk" | "all";

export function matchesMaterialsFilter(
  status: LineFeederStatus,
  filter: MaterialsListFilter,
): boolean {
  if (filter === "all") return true;
  if (filter === "at_risk") return status === "at_risk";
  return status === "to_pick" || status === "at_risk" || status === "unknown";
}
