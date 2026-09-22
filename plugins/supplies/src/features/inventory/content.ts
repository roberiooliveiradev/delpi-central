export const INVENTORY_CONTENT = {
  title: "Controle de Estoques",
  eyebrow: "Portal Suprimentos",
  description:
    "Posição física de estoque no Protheus por produto, unidade e armazém. Inclui saldo positivo, zero e negativo.",
  filtersAriaLabel: "Filtros de controle de estoques",
  filtersTitle: "Filtros",
  listTitle: "Saldos físicos",
  listHint:
    "Cada linha é uma posição produto × unidade × armazém. Não é estoque de segurança nem giro.",
  tableMeta: (columns: number, rows: number) =>
    `${columns} coluna(s) · ${rows.toLocaleString("pt-BR")} linha(s)`,
  warehouseLabel: "Armazém",
  warehouseEmptyOption: "Todos",
  warehouseCodeEmpty: "Sem código",
  heroProducts: "Produtos",
  heroWarehouses: "Armazéns",
  heroStockValue: "Valor do estoque",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  clearFilters: "Limpar",
  loading: "Carregando saldos…",
  loadingSummary: "Atualizando resumo…",
  emptyTitle: "Nenhuma posição de estoque encontrada",
  emptyMessage:
    "Nenhuma posição de estoque encontrada para os filtros selecionados.",
  emptyClearAction: "Limpar filtros",
  emptyHelpAction: "Abrir Ajuda",
  noUnitsTitle: "Nenhuma filial liberada",
  noUnitsMessage:
    "Seu acesso não inclui unidades neste módulo. Peça o escopo canônico ao administrador.",
  error: "Não foi possível carregar os saldos de estoque.",
  forbiddenUnit:
    "Você não tem permissão para esta filial neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  retry: "Tentar novamente",
  colProduct: "Produto",
  colDescription: "Descrição",
  colUm: "UM",
  colUnit: "Unidade",
  colWarehouse: "Armazém",
  colQuantity: "Saldo físico",
  colUnitCost: "Custo unitário",
  colStockValue: "Valor do saldo",
  tableScrollRegion:
    "Tabela de saldos físicos — deslize horizontalmente para ver todas as colunas",
} as const;

export function mapInventoryFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return INVENTORY_CONTENT.forbiddenUnit;
  }
  return message || INVENTORY_CONTENT.error;
}
