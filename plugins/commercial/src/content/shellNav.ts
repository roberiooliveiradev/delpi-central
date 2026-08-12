/**
 * Navegação de topo do Portal Comercial (IA 2026): rótulos e ordem das seis áreas.
 * Fonte única — o shell só filtra por capacidade, aplica ícone e navega.
 */
import type { PluginNavId } from "../app/pluginRoutes";

/** Capacidade exigida para o item aparecer na navegação de topo. */
export type ShellNavCapability = "always" | "analytics" | "worklist" | "customers" | "admin";

export type ShellNavItem = {
  id: PluginNavId;
  label: string;
  requiredCap: ShellNavCapability;
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  { id: "home", label: "Início", requiredCap: "always" },
  { id: "overview", label: "Visão geral", requiredCap: "analytics" },
  { id: "my_tasks", label: "Minhas tarefas", requiredCap: "worklist" },
  { id: "open_orders", label: "Meus pedidos", requiredCap: "always" },
  { id: "customers", label: "Minha Carteira", requiredCap: "customers" },
  { id: "administration", label: "Administração", requiredCap: "admin" },
] as const;

export type ShellNavCapabilities = Record<Exclude<ShellNavCapability, "always">, boolean>;

/** Itens visíveis para as capacidades da sessão (sem capacidade, o item é omitido). */
export function resolveShellNavItems(
  capabilities: ShellNavCapabilities,
  items: readonly ShellNavItem[] = SHELL_NAV_ITEMS,
): ShellNavItem[] {
  return items.filter(
    (item) => item.requiredCap === "always" || capabilities[item.requiredCap],
  );
}

export const SHELL_NAV_CONTENT = {
  ariaLabel: "Áreas do Portal Comercial",
  scopeLabel: "Escopo",
  scopeHelpAriaLabel: "Ajuda: Escopo",
} as const;
