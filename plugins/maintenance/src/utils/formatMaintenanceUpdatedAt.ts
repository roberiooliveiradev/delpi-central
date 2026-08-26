export function formatMaintenanceUpdatedAt(value: Date | null | undefined): string {
  if (!value) return "—";
  return value.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}
