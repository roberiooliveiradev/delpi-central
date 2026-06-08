export type BranchCode = "ES" | "SC";

export type ResourceType = "meeting_room" | "training_room" | "company_car" | "other";

export const API_BASE = "/apps/api-delpi/scheduling";

export const BRANCH_LABELS: Record<BranchCode, string> = {
  ES: "Filial ES",
  SC: "Filial SC",
};

export const RESOURCE_TYPES: { value: ResourceType; label: string }[] = [
  { value: "meeting_room", label: "Sala de Reunião" },
  { value: "training_room", label: "Sala de Treinamento" },
  { value: "company_car", label: "Carro da Empresa" },
  { value: "other", label: "Outros" },
];

/** Paleta alinhada ao portal (`--primary`, `--success`, `--warning`). */
export const RESOURCE_TYPE_COLORS: Record<ResourceType, string> = {
  meeting_room: "#089bdb",
  training_room: "#067647",
  company_car: "#f59e0b",
  other: "#6b7280",
};

export function resourceTypeLabel(type: ResourceType): string {
  return RESOURCE_TYPES.find((item) => item.value === type)?.label ?? type;
}

export function branchFromPathname(pathname?: string): BranchCode | null {
  if (!pathname) return null;
  if (pathname.includes("/filial-es")) return "ES";
  if (pathname.includes("/filial-sc")) return "SC";
  return null;
}

export function managePermissionForBranch(branch: BranchCode): string {
  return `central-agendamento.manage.filial-${branch.toLowerCase()}`;
}

export function viewPermissionForBranch(branch: BranchCode): string {
  return `central-agendamento.view.filial-${branch.toLowerCase()}`;
}
