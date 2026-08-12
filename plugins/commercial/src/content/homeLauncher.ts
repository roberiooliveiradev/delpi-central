/**
 * Launcher do Início (IA 2026): cards de funcionalidades e textos das seções.
 * Fonte única — a Home só filtra por capacidade e navega; nada de card fixo no JSX.
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

/** Capacidade exigida para o card aparecer no launcher. */
export type HomeLauncherCapability =
  | "analytics"
  | "worklist"
  | "proposals"
  | "customers"
  | "team"
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
  | "analytics_team"
  | "administration";

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
  quickLinks?: readonly HomeLauncherQuickLink[];
};

export const HOME_LAUNCHER_CARDS: readonly HomeLauncherCard[] = [
  {
    id: "overview",
    title: "Visão geral",
    description: "Indicadores comerciais do período: receita, conversão e pontualidade.",
    viewId: "overview",
    requiredCap: "analytics",
  },
  {
    id: "my_tasks",
    title: "Minhas tarefas",
    description: "Fila de follow-ups atribuídos a você: atrasadas, hoje e depois.",
    viewId: "my_tasks",
    requiredCap: "worklist",
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
    quickLinks: [
      { id: "late", label: "Em atraso", viewId: "open_orders", search: "?focus=late" },
      {
        id: "billable",
        label: "Pode faturar",
        viewId: "open_orders",
        search: "?stock=com_estoque",
      },
    ],
  },
  {
    id: "customers",
    title: "Minha Carteira",
    description: "Clientes da carteira com pedidos em aberto e histórico de faturamento.",
    viewId: "customers",
    requiredCap: "customers",
  },
  {
    id: "proposals",
    title: "Propostas",
    description: "Propostas comerciais para consulta e emissão em PDF.",
    viewId: "proposals",
    requiredCap: "proposals",
  },
  {
    id: "analytics_otd",
    title: "Pontualidade (OTD)",
    description: "Entrega no prazo das linhas de pedido, com detalhe por item.",
    viewId: "analytics_otd",
    requiredCap: "analytics",
  },
  {
    id: "analytics_opportunities",
    title: "Oportunidades",
    description: "Funil e ciclo das oportunidades de venda no período filtrado.",
    viewId: "analytics_opportunities",
    requiredCap: "analytics",
  },
  {
    id: "analytics_team",
    title: "Equipe",
    description: "Carteiras ativas da equipe: clientes, linhas abertas e valor.",
    viewId: "analytics_team",
    requiredCap: "team",
  },
  {
    id: "administration",
    title: "Administração",
    description: "Carteiras, membros e transferência de clientes entre vendedores.",
    viewId: "administration",
    requiredCap: "admin",
  },
] as const;

export type HomeLauncherCapabilities = Record<
  Exclude<HomeLauncherCapability, "always">,
  boolean
>;

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
    empty: "Nenhuma funcionalidade disponível para o seu acesso.",
  },
} as const;
