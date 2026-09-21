export const PURCHASE_REQUESTS_CONTENT = {
  title: "Solicitações de compras",
  eyebrow: "Portal Suprimentos",
  description:
    "Acompanhamento global das solicitações no período. A unidade é filtro, não permissão. Clique na SC para abrir a ficha.",
  helpAriaLabel: "Ajuda sobre solicitações de compras",
  filtersAriaLabel: "Filtros de solicitações de compras",
  filtersTitle: "Filtros",
  listTitle: "Lista de solicitações",
  listHint:
    "Clique na SC ou na linha para abrir a ficha. Lista vazia significa ausência de item no período ou nos filtros.",
  tableMeta: (columns: number, requests: number) =>
    `${columns} coluna(s) · ${requests.toLocaleString("pt-BR")} SC(s)`,
  cardsMeta: (requests: number) => `${requests.toLocaleString("pt-BR")} SC(s)`,
  heroRequests: "Solicitações",
  heroOrdering: "Aguardando pedido",
  heroReceiving: "Aguardando recebimento",
  attentionLabel: "Atenção",
  attentionAriaLabel: "Atalhos de situação das solicitações",
  attentionAll: "Todos",
  attentionOrdering: "Aguardando pedido",
  attentionReceiving: "Aguardando recebimento",
  attentionCompleted: "Concluídas",
  attentionAllWithCount: (count: number) => `Todos (${count.toLocaleString("pt-BR")})`,
  attentionOrderingWithCount: (count: number) =>
    `Aguardando pedido (${count.toLocaleString("pt-BR")})`,
  attentionReceivingWithCount: (count: number) =>
    `Aguardando recebimento (${count.toLocaleString("pt-BR")})`,
  attentionCompletedWithCount: (count: number) =>
    `Concluídas (${count.toLocaleString("pt-BR")})`,
  openScLinkTitle: (number: string) => `Abrir solicitação ${number}`,
  branchLabel: "Unidade",
  dateFromLabel: "De",
  dateToLabel: "Até",
  periodLabel: "Período",
  requestNumberLabel: "Número SC",
  productLabel: "Produto",
  stageLabel: "Situação",
  stageAll: "Todas",
  sortByLabel: "Ordenar por",
  sortAscLabel: "Crescente",
  sortDescLabel: "Decrescente",
  sortDirectionAriaLabel: "Direção da ordenação",
  clearFilters: "Limpar",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  exportLabel: "Excel",
  exportTitle: "Baixa o recorte filtrado em Excel",
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
    "Ajuste filtros ou período. Nesta tela o uso normal do Portal acompanha as solicitações das duas unidades.",
  noUnitsTitle: "Nenhuma unidade liberada",
  noUnitsMessage:
    "Seu acesso não inclui unidades neste módulo. Peça o escopo canônico ao administrador.",
  error: "Não foi possível carregar as solicitações.",
  stageSortTooLarge:
    "Ordenação por situação exige um recorte menor. Reduza o período ou selecione uma unidade.",
  forbiddenUnit:
    "Você não tem permissão para esta unidade neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  retry: "Tentar novamente",
  detailTitle: "Solicitação",
  detailEyebrow: "Solicitação de compra",
  detailDescription:
    "Dados da solicitação e de todos os itens. A unidade é o recorte do filtro.",
  detailHint: "Itens da solicitação no recorte escolhido.",
  detailBack: "Solicitações de compras",
  detailLoading: "Carregando a solicitação…",
  detailError: "Não foi possível carregar esta solicitação de compra.",
  detailNotFound: "Solicitação não encontrada no seu escopo.",
  detailForbidden:
    "Você não tem permissão para esta unidade neste módulo. Peça o acesso canônico ao administrador.",
  detailRetry: "Tentar novamente",
  itemsTitle: "Itens",
  itemsEmpty: "Esta solicitação não retornou itens visíveis no seu escopo.",
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
  if (
    /recorte menor/i.test(message) ||
    (/422/.test(message) && /situação|situacao|overall_stage|ordenação por situação/i.test(message))
  ) {
    return PURCHASE_REQUESTS_CONTENT.stageSortTooLarge;
  }
  return message || PURCHASE_REQUESTS_CONTENT.error;
}

export function classifyPurchaseRequestDetailError(message: string): {
  kind: "forbidden" | "not_found" | "error";
  text: string;
} {
  if (/403|forbidden/i.test(message)) {
    return { kind: "forbidden", text: PURCHASE_REQUESTS_CONTENT.detailForbidden };
  }
  if (/404|não encontrada|not found/i.test(message)) {
    return { kind: "not_found", text: PURCHASE_REQUESTS_CONTENT.detailNotFound };
  }
  return {
    kind: "error",
    text: message || PURCHASE_REQUESTS_CONTENT.detailError,
  };
}
