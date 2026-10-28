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
  /** Item visível quando o viewer detém QUALQUER capability listada. */
  requiredCaps: readonly ShellNavCapability[];
};

export const SHELL_NAV_ITEMS: readonly ShellNavItem[] = [
  // RW04 — UMA top bar, UM «Início»: interno e DRE navegam para a
  // mesma Home no basePath. Itens futuros (Visão geral, Minhas
  // tarefas, áreas DRE…) entram aqui sob as capabilities
  // correspondentes quando a rota existir em runtime.
  { id: "home", label: "Início", requiredCaps: ["access", "accessDre"] },
] as const;

export type ShellNavCapabilities = Record<ShellNavCapability, boolean>;

export function resolveShellNavItems(
  capabilities: ShellNavCapabilities,
  items: readonly ShellNavItem[] = SHELL_NAV_ITEMS,
): ShellNavItem[] {
  return items.filter((item) =>
    item.requiredCaps.some((cap) => capabilities[cap]),
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
