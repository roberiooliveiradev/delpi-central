/**
 * Launcher do Início (IA 2026): cards de funcionalidades e textos das seções.
 * Fonte única — a Home só filtra por capacidade e navega; nada de card fixo no JSX.
 * Ranking Equipe não entra no launcher — Administração cobre carteiras.
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

/** Capacidade exigida para o card aparecer no launcher. */
export type HomeLauncherCapability =
  | "analytics"
  | "worklist"
  | "proposals"
  | "customers"
  | "admin"
  | "always";

export type HomeLauncherCardId =
  | "overview"
  | "my_tasks"
  | "open_orders"
  | "customers"
  | "proposals"
  | "analytics_otd"
  | "analytics_opportunities"
  | "administration";

export type HomeLauncherTier = "primary" | "secondary";

export type HomeLauncherQuickLink = {
  id: string;
  label: string;
  viewId: PluginNavigationTarget;
  search?: string;
};

export type HomeLauncherCard = {
  id: HomeLauncherCardId;
  title: string;
  description: string;
  viewId: PluginNavigationTarget;
  requiredCap: HomeLauncherCapability;
  /** primary = featured tile; secondary = compacto. */
  tier: HomeLauncherTier;
  quickLinks?: readonly HomeLauncherQuickLink[];
};

export const HOME_LAUNCHER_CARDS: readonly HomeLauncherCard[] = [
  {
    id: "overview",
    title: "Visão geral",
    description: "Indicadores comerciais do período: receita, conversão e pontualidade.",
    viewId: "overview",
    requiredCap: "analytics",
    tier: "primary",
  },
  {
    id: "my_tasks",
    title: "Minhas tarefas",
    description: "Fila de follow-ups atribuídos a você: atrasadas, hoje e depois.",
    viewId: "my_tasks",
    requiredCap: "worklist",
    tier: "primary",
    quickLinks: [
      { id: "overdue", label: "Atrasadas", viewId: "my_tasks", search: "?bucket=overdue" },
      { id: "today", label: "Hoje", viewId: "my_tasks", search: "?bucket=today" },
    ],
  },
  {
    id: "open_orders",
    title: "Meus pedidos",
    description: "Itens de pedidos de venda em aberto nas carteiras que você atende.",
    viewId: "open_orders",
    requiredCap: "always",
    tier: "primary",
    quickLinks: [
      { id: "late", label: "Em atraso", viewId: "open_orders", search: "?focus=late" },
      {
        id: "billable",
        label: "Pode faturar",
        viewId: "open_orders",
        search: "?stock=com_estoque",
      },
      {
        id: "postponed",
        label: "Postergado",
        viewId: "open_orders",
        search: "?postponed=1",
      },
    ],
  },
  {
    id: "customers",
    title: "Minha Carteira",
    description: "Clientes vinculados à carteira, com histórico de faturamento e indicadores de aberto.",
    viewId: "customers",
    requiredCap: "customers",
    tier: "primary",
  },
  {
    id: "proposals",
    title: "Propostas",
    description: "Propostas comerciais para consulta e emissão em PDF.",
    viewId: "proposals",
    requiredCap: "proposals",
    tier: "secondary",
  },
  {
    id: "analytics_otd",
    title: "Pontualidade (OTD)",
    description: "Entrega no prazo das linhas de pedido, com detalhe por item.",
    viewId: "analytics_otd",
    requiredCap: "analytics",
    tier: "secondary",
  },
  {
    id: "analytics_opportunities",
    title: "Oportunidades",
    description:
      "Visão por colaborador ou por oportunidade: funil e ciclo das OVs no período filtrado.",
    viewId: "analytics_opportunities",
    requiredCap: "analytics",
    tier: "secondary",
  },
  {
    id: "administration",
    title: "Administração",
    description: "Carteiras, membros e transferência de clientes entre vendedores.",
    viewId: "administration",
    requiredCap: "admin",
    tier: "secondary",
  },
] as const;

export type HomeLauncherCapabilities = Record<
  Exclude<HomeLauncherCapability, "always">,
  boolean
>;

/** Contagens opcionais para a linha `meta` do NavigationCard. */
export type HomeLauncherMetaCounts = {
  followUpsOpen?: number | null;
  openOrderLines?: number | null;
  lateLines?: number | null;
};

export function formatHomeLauncherMeta(
  cardId: HomeLauncherCardId,
  counts: HomeLauncherMetaCounts,
): string | undefined {
  const fmt = (n: number) => n.toLocaleString("pt-BR");
  if (cardId === "my_tasks" && counts.followUpsOpen != null && counts.followUpsOpen > 0) {
    return `${fmt(counts.followUpsOpen)} na fila`;
  }
  if (cardId === "open_orders") {
    const lines = counts.openOrderLines;
    const late = counts.lateLines;
    if (lines == null) return undefined;
    if (late != null && late > 0) {
      return `${fmt(lines)} linha(s) · ${fmt(late)} em atraso`;
    }
    if (lines > 0) return `${fmt(lines)} linha(s) aberta(s)`;
    return undefined;
  }
  return undefined;
}

/** Cards visíveis para as capacidades da sessão (sem capacidade, o card é omitido). */
export function resolveHomeLauncherCards(
  capabilities: HomeLauncherCapabilities,
  cards: readonly HomeLauncherCard[] = HOME_LAUNCHER_CARDS,
): HomeLauncherCard[] {
  return cards.filter(
    (card) => card.requiredCap === "always" || capabilities[card.requiredCap],
  );
}

export const HOME_LAUNCHER_CONTENT = {
  events: {
    title: "Eventos e interações",
    subtitle: "Tarefas e alertas do seu dia.",
    cta: "Abrir Minhas tarefas",
    refresh: "Atualizar",
    loading: "Carregando eventos…",
    queueLabel: "Fila",
    listAriaLabel: "Eventos e interações pendentes",
    emptyTitle: "Nenhuma interação pendente",
    emptyMessage: "Sua fila está em dia. Use as funcionalidades ao lado para operar.",
    alertsEmpty: "Nada precisa de atenção agora. Bom trabalho!",
    openTask: "Abrir",
    openOverdue: "Ver atrasadas",
    noDueDate: "Sem prazo",
    buckets: {
      overdue: "Atrasadas",
      today: "Hoje",
      later: "Depois",
    },
  },
  features: {
    title: "Funcionalidades",
    subtitle: "Selecione uma funcionalidade para começar.",
    gridAriaLabel: "Funcionalidades do Portal Comercial",
    primaryAriaLabel: "Funcionalidades principais",
    secondaryAriaLabel: "Mais funcionalidades",
    empty: "Nenhuma funcionalidade disponível para o seu acesso.",
  },
} as const;
