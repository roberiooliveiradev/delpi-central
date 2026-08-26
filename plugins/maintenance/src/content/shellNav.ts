import type { MaintenanceNavId } from "../app/maintenanceNav";

export type ShellNavCapability =
  | "always"
  | "filiais"
  | "mini-aplicadores"
  | "programas-maquinas"
  | "manutencao-geral";

export type ShellNavItem = {
  id: MaintenanceNavId;
  label: string;
  requiredCap: ShellNavCapability;
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  { id: "home", label: "Início", requiredCap: "always" },
  { id: "filiais", label: "Filiais", requiredCap: "filiais" },
  { id: "mini-aplicadores", label: "Mini-aplicadores", requiredCap: "mini-aplicadores" },
  { id: "programas-maquinas", label: "Programas de máquina", requiredCap: "programas-maquinas" },
  { id: "manutencao-geral", label: "Manutenção geral", requiredCap: "manutencao-geral" },
] as const;

export type ShellNavCapabilities = Record<Exclude<ShellNavCapability, "always">, boolean>;

export function resolveShellNavItems(
  capabilities: ShellNavCapabilities,
  items: readonly ShellNavItem[] = SHELL_NAV_ITEMS,
): ShellNavItem[] {
  return items.filter(
    (item) => item.requiredCap === "always" || capabilities[item.requiredCap],
  );
}

export const SHELL_NAV_CONTENT = {
  ariaLabel: "Áreas do portal Manutenção",
  collapseLabel: "Recolher navegação",
  expandLabel: "Expandir navegação",
  menuLabel: "Menu de navegação",
} as const;
