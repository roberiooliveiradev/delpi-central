/**
 * Navegação de topo do Portal Controladoria & Finanças.
 * Fonte única — o shell só aplica ícone e navega.
 *
 * A ordem canônica (doc 24) é Início, Visão geral, Sala de
 * interação, Minhas tarefas, Administração, Ajuda — itens entram
 * aqui apenas quando a rota existir em runtime. Implementadas:
 * «Início» e «Minhas tarefas».
 */
import type { PluginNavId } from "../app/pluginRoutes";

export type ShellNavCapability = "always" | "manage";

export type ShellNavItem = {
  id: PluginNavId;
  label: string;
  requiredCap: ShellNavCapability;
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  { id: "home", label: "Início", requiredCap: "always" },
  { id: "my_tasks", label: "Minhas tarefas", requiredCap: "always" },
] as const;

export type ShellNavCapabilities = Record<
  Exclude<ShellNavCapability, "always">,
  boolean
>;

export function resolveShellNavItems(
  capabilities: ShellNavCapabilities,
  items: readonly ShellNavItem[] = SHELL_NAV_ITEMS,
): ShellNavItem[] {
  return items.filter(
    (item) => item.requiredCap === "always" || capabilities[item.requiredCap],
  );
}

export const SHELL_NAV_CONTENT = {
  ariaLabel: "Áreas do Portal Controladoria & Finanças",
  collapseLabel: "Recolher navegação",
  expandLabel: "Expandir navegação",
  menuLabel: "Menu de navegação",
  searchLabel: "Buscar",
  searchTitle: "Buscar caminhos e funcionalidades (Ctrl+K)",
  searchAriaLabel: "Abrir busca do Portal Controladoria & Finanças",
  searchShortcutLabel: "Ctrl+K",
  userMenu: {
    nameFallback: "Usuário",
    profileAriaLabel: "Identidade da sessão",
  },
  homeHero: {
    eyebrow: "Controladoria & Finanças",
    ariaLabel: "Saudação",
    description:
      "Acompanhe o contexto operacional e abra as funcionalidades do portal a partir daqui.",
    scopeOwn: "Acesso ao portal",
    highlights: {
      competence: "Competência",
      tasks: "Tarefas pendentes",
      attention: "Atenções",
    },
    highlightsUnavailable: "—",
  },
} as const;
