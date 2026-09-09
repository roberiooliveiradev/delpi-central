import type { ProductionPulseNavId } from "../utils/resolvePulseNavId";

export type ShellNavItem = {
  id: ProductionPulseNavId;
  label: string;
  requiresOperator?: boolean;
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  { id: "panel", label: "Painel" },
  { id: "firmwares", label: "Firmwares" },
  { id: "firmwareLinks", label: "Hub OTA" },
  { id: "operator", label: "Operador", requiresOperator: true },
] as const;

export const SHELL_NAV_CONTENT = {
  ariaLabel: "Áreas do Pulso de Produção",
  collapseLabel: "Recolher navegação",
  expandLabel: "Expandir navegação",
  menuLabel: "Menu de navegação",
} as const;

export function resolveShellNavItems(
  permissions: { canOperator: boolean },
  items: readonly ShellNavItem[] = SHELL_NAV_ITEMS,
): ShellNavItem[] {
  return items.filter((item) => !item.requiresOperator || permissions.canOperator);
}
