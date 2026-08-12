/**
 * Textos da timeline de auditoria da carteira (E6.3 + histórico do membro).
 */
export const PORTFOLIO_AUDIT_CONTENT = {
  title: "Histórico",
  titleMember: "Histórico da carteira",
  subtitle: "Vínculos de clientes, membros, responsável, transferência e status.",
  subtitleMember:
    "Alterações recentes na carteira selecionada — vínculos, membros e responsável.",
  loading: "Carregando histórico…",
  empty: "Ainda não há eventos de auditoria nesta carteira.",
  emptyFiltered: "Nenhum evento neste filtro.",
  errorRetry: "Tentar novamente",
  ariaLabel: "Timeline de auditoria da carteira",
  filterAriaLabel: "Filtrar eventos do histórico",
  actorPrefix: "Por",
  anonymousUser: "um usuário",
  selectPortfolioLabel: "Carteira do histórico",
  selectPortfolioHint:
    "Com «Todas» no filtro da página, escolha qual carteira exibir no histórico.",
  selectPortfolioPlaceholder: "Selecione uma carteira",
  filters: {
    all: "Todos",
    customers: "Clientes",
    members: "Equipe",
    status: "Status",
    transfers: "Transferências",
  },
} as const;

export type PortfolioAuditEventFilter = keyof typeof PORTFOLIO_AUDIT_CONTENT.filters;
