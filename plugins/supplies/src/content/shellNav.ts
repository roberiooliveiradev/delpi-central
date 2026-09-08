import type { PluginNavId } from "../app/pluginRoutes";

export type ShellNavCapability =
  | "always"
  | "analytics"
  | "purchaseRequests"
  | "operations"
  | "administration";

export type ShellNavItem = {
  id: PluginNavId;
  label: string;
  requiredCap: ShellNavCapability;
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  { id: "home", label: "Início", requiredCap: "always" },
  { id: "overview", label: "Visão geral", requiredCap: "analytics" },
  { id: "my_tasks", label: "Minhas tarefas", requiredCap: "always" },
  { id: "purchase_requests", label: "Solicitações", requiredCap: "purchaseRequests" },
  { id: "operations", label: "Operações", requiredCap: "operations" },
  { id: "administration", label: "Administração", requiredCap: "administration" },
  { id: "help", label: "Ajuda", requiredCap: "always" },
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
  ariaLabel: "Áreas do Portal Suprimentos",
  collapseLabel: "Recolher navegação",
  expandLabel: "Expandir navegação",
  menuLabel: "Menu de navegação",
  searchLabel: "Buscar",
  searchShortcutLabel: "Ctrl+K",
  searchTitle: "Buscar áreas do Portal (Ctrl+K)",
  searchAriaLabel: "Abrir busca do Portal Suprimentos",
  homeHero: {
    eyebrow: "Portal Suprimentos",
    ariaLabel: "Saudação",
    description:
      "Acompanhe a atenção do dia e abra as funcionalidades — indicadores do período ficam na Visão geral.",
    scopeUnits: "Filiais no escopo",
    scopeEmpty: "Sem filial liberada",
    helpAriaLabel: "Ajuda: Início",
    highlights: {
      attention: "Atenção",
      attentionClear: "Em dia",
      units: "Filiais",
      overview: "Visão geral",
      overviewCta: "Abrir",
      overviewLocked: "Sem acesso",
    },
  },
} as const;
