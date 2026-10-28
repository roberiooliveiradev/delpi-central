/**
 * Navegação de topo do Portal Controladoria & Finanças.
 * Fonte única — o shell só aplica ícone e navega.
 *
 * A ordem canônica (doc 24) é Início, Visão geral, Sala de
 * interação, Minhas tarefas, Administração, Ajuda — itens entram
 * aqui apenas quando a rota existir em runtime. Implementada:
 * «Início». «Minhas tarefas» permanece implementada em rota/código,
 * mas fora da navegação desta release (CF-PROC0072-CLARA-COMPLETE-001
 * §18 — escopo adiado, sem exclusão destrutiva).
 */
import type { PluginNavId } from "../app/pluginRoutes";

export type ShellNavCapability = "access" | "manage" | "accessDre";

export type ShellNavItem = {
  id: PluginNavId;
  label: string;
  requiredCap: ShellNavCapability;
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  { id: "home", label: "Início", requiredCap: "access" },
  // RW03 — a DRE também tem top bar: «Início» aponta para a Home DRE.
  // Itens futuros (Visão geral DRE, Minhas tarefas…) entram aqui sob
  // a capability correspondente quando a rota existir em runtime.
  { id: "dre_home", label: "Início", requiredCap: "accessDre" },
] as const;

export type ShellNavCapabilities = Record<ShellNavCapability, boolean>;

export function resolveShellNavItems(
  capabilities: ShellNavCapabilities,
  items: readonly ShellNavItem[] = SHELL_NAV_ITEMS,
): ShellNavItem[] {
  return items.filter((item) => capabilities[item.requiredCap]);
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
      attention: "Atenções",
    },
    highlightsUnavailable: "—",
  },
  dreHero: {
    eyebrow: "Controladoria & Finanças",
    ariaLabel: "Saudação",
    description:
      "Acompanhe seus fechamentos, documentos e interações com a Controladoria.",
    scopeDre: "Acesso DRE",
  },
} as const;
