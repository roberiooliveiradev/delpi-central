export const PURCHASE_REQUESTS_CONTENT = {
  title: "Solicitações de compras",
  eyebrow: "Portal Suprimentos",
  description:
    "Linhas de SC no seu escopo de centro de custo e filial. O detalhe abre no painel abaixo da lista.",
  helpAriaLabel: "Ajuda sobre solicitações de compras",
  filtersAriaLabel: "Filtros de solicitações de compras",
  listTitle: "Lista de solicitações",
  listHint:
    "Linhas no escopo CC + filial. Clique em uma linha para abrir o detalhe. Lista vazia pode significar falta de CC liberado.",
  branchLabel: "Filial",
  dateFromLabel: "De",
  dateToLabel: "Até",
  requestNumberLabel: "Número SC",
  productLabel: "Produto",
  stageLabel: "Situação",
  stageAll: "Todas",
  applyFilters: "Aplicar filtros",
  clearFilters: "Limpar",
  exportLabel: "Exportar CSV",
  exportTitle: "Baixa o recorte filtrado (exige permissão de exportação)",
  loading: "Carregando solicitações…",
  emptyTitle: "Nenhuma solicitação neste recorte",
  emptyMessage:
    "Ajuste filtros ou período. Sem centros de custo liberados, a lista fica vazia (fail-closed).",
  error: "Não foi possível carregar as solicitações.",
  forbiddenUnit:
    "Você não tem permissão para esta filial neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  retry: "Tentar novamente",
  detailTitle: "Detalhe da SC",
  detailHint: "Cabeçalho e itens visíveis no seu escopo de centro de custo.",
  detailLoading: "Carregando detalhe…",
  detailError: "Não foi possível carregar o detalhe.",
  detailNotFound: "Solicitação não encontrada no seu escopo.",
  detailClose: "Fechar",
  detailRetry: "Tentar novamente",
  colSc: "SC",
  colItem: "Item",
  colProduct: "Produto",
  colRequester: "Solicitante",
  colCc: "Centro de custo",
  colOpened: "Abertura",
  colStage: "Situação",
  pageLabel: "Página",
  prevPage: "Anterior",
  nextPage: "Próxima",
  totalLabel: (total: number) => `${total} linha(s)`,
} as const;

export function mapPurchaseRequestsFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return PURCHASE_REQUESTS_CONTENT.forbiddenUnit;
  }
  return message || PURCHASE_REQUESTS_CONTENT.error;
}
