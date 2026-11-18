export const DELIVERIES_CONTENT = {
  title: "Entregas / Atrasos",
  eyebrow: "Portal Suprimentos",
  description:
    "Linhas de recebimento de matéria-prima classificadas pela data efetiva do OTD: física quando conciliada no Lançamento de Notas Fiscais, ou digitação no Protheus.",
  helpAriaLabel: "Ajuda sobre entregas e atrasos",
  filtersAriaLabel: "Filtros de entregas e atrasos",
  filtersTitle: "Filtros",
  listTitle: "Recebimentos MP",
  listHint:
    "Histórico de recebimentos no período considerado pelo OTD. Pedidos em aberto ficam em Pedidos de compra.",
  tableMeta: (columns: number, rows: number) =>
    `${columns} coluna(s) · ${rows.toLocaleString("pt-BR")} linha(s)`,
  branchLabel: "Unidade",
  statusLabel: "Situação",
  periodLabel: "Período do OTD",
  entryFromLabel: "De",
  entryToLabel: "Até",
  heroTotal: "Linhas",
  heroLate: "Em atraso",
  heroOnTime: "No prazo",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  clearFilters: "Limpar",
  loading: "Carregando recebimentos…",
  emptyTitle: "Nenhum recebimento neste recorte",
  emptyMessage:
    "Ajuste unidade, período do OTD ou situação. Pedidos sem entrada não aparecem aqui.",
  emptyClearAction: "Limpar filtros",
  emptyHelpAction: "Abrir Ajuda",
  noUnitsTitle: "Nenhuma filial liberada",
  noUnitsMessage:
    "Seu acesso não inclui unidades neste módulo. Peça o escopo canônico ao administrador.",
  error: "Não foi possível carregar as entregas.",
  forbiddenUnit:
    "Você não tem permissão para esta filial neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  retry: "Tentar novamente",
  colUnit: "Unidade",
  colPc: "Pedido",
  colItem: "Item",
  colSupplier: "Fornecedor",
  colProduct: "Produto",
  colQty: "Qtd.",
  colPromised: "Data prometida",
  colEntry: "Digitação ERP",
  colEffective: "Recebimento OTD",
  colDays: "Dias",
  colStatus: "Situação",
  pageLabel: "Página",
  prevPage: "Anterior",
  nextPage: "Próxima",
  totalLabel: (total: number) => `${total} linha(s)`,
  tableScrollRegion:
    "Tabela de entregas — deslize horizontalmente para ver todas as colunas",
} as const;

export function mapDeliveriesFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return DELIVERIES_CONTENT.forbiddenUnit;
  }
  return message || DELIVERIES_CONTENT.error;
}
