export const PURCHASE_REQUESTS_CONTENT = {
  title: "Solicitações de compras",
  eyebrow: "Portal Suprimentos",
  description:
    "Linhas de SC no seu escopo de centro de custo e filial. O detalhe abre no painel abaixo da lista.",
  helpAriaLabel: "Ajuda sobre solicitações de compras",
  filtersAriaLabel: "Filtros de solicitações de compras",
  filtersTitle: "Filtros",
  moreFilters: "Mais filtros",
  lessFilters: "Menos filtros",
  listTitle: "Lista de solicitações",
  listHint:
    "Linhas no escopo CC + filial. Clique na SC ou na linha para abrir o detalhe. Lista vazia pode significar falta de CC liberado.",
  tableMeta: (columns: number, rows: number) =>
    `${columns} coluna(s) · ${rows.toLocaleString("pt-BR")} linha(s)`,
  openScLinkTitle: (number: string) => `Abrir solicitação ${number}`,
  branchLabel: "Filial",
  dateFromLabel: "Período de",
  dateToLabel: "Período até",
  requestNumberLabel: "Número SC",
  productLabel: "Produto",
  stageLabel: "Situação",
  stageAll: "Todas",
  clearFilters: "Limpar",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  exportLabel: "Excel",
  exportTitle: "Baixa o recorte filtrado em Excel (exige permissão de exportação)",
  excelExporting: "Gerando Excel…",
  excelError: "Não foi possível exportar o Excel.",
  viewAriaLabel: "Modo de visualização",
  viewTable: "Tabela",
  viewCards: "Cards",
  cardsAriaLabel: "Cards de solicitações de compra",
  cardRequester: "Solicitante",
  cardCc: "Centro de custo",
  cardOpened: "Abertura",
  cardStage: "Situação",
  loading: "Carregando solicitações…",
  emptyTitle: "Nenhuma solicitação neste recorte",
  emptyMessage:
    "Ajuste filtros ou período. Sem centros de custo liberados, a lista fica vazia (fail-closed).",
  noUnitsTitle: "Nenhuma filial liberada",
  noUnitsMessage:
    "Seu acesso não inclui unidades neste módulo. Peça o escopo canônico ao administrador.",
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
  tableScrollRegion:
    "Tabela de solicitações — deslize horizontalmente para ver todas as colunas",
} as const;

export function mapPurchaseRequestsFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return PURCHASE_REQUESTS_CONTENT.forbiddenUnit;
  }
  return message || PURCHASE_REQUESTS_CONTENT.error;
}
