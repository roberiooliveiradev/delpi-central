import type { SafetyStockStatus } from "./types";

export const SAFETY_STOCK_CONTENT = {
  title: "Estoque de Segurança",
  eyebrow: "Portal Suprimentos",
  description:
    "Materiais com estoque de segurança parametrizado no Protheus: saldos, déficit e classificação por unidade. Valores calculados pelo servidor.",
  filtersAriaLabel: "Filtros de estoque de segurança",
  filtersTitle: "Filtros",
  listTitle: "Materiais",
  listHint:
    "Cada linha é um produto em uma filial. Classificação e déficit vêm do servidor; o Portal não recalcula.",
  tableMeta: (columns: number, rows: number) =>
    `${columns} coluna(s) · ${rows.toLocaleString("pt-BR")} material(is)`,
  branchLabel: "Filial",
  branchAllOption: "Todas as Filiais",
  statusLabel: "Status",
  statusEmptyOption: "Todos",
  productGroupLabel: "Grupo",
  productGroupEmptyOption: "Todos",
  unitLabel: "UM",
  unitEmptyOption: "Todas",
  searchLabel: "Busca",
  searchPlaceholder: "Código ou descrição do produto",
  includeBlockedLabel: "Incluir materiais bloqueados",
  includeWithoutSafetyStockLabel: "Incluir materiais sem estoque de segurança",
  coverageTitle: "Cobertura do recorte",
  coverageWithPrimary: "Com saldo principal",
  coverageWithoutPrimary: "Sem saldo principal",
  coverageWorkInProcess: "Com saldo em processo",
  deficitTitle: "Déficit por unidade de medida",
  deficitEmpty: "Sem déficit no recorte.",
  deficitChip: (unit: string, quantity: string, count: number) =>
    `${unit}: ${quantity} (${count.toLocaleString("pt-BR")} material(is))`,
  heroTotal: "Materiais",
  heroWithSafetyStock: "Com estoque de segurança",
  heroWithoutSafetyStock: "Sem estoque de segurança",
  heroBelow: "Abaixo do estoque de segurança",
  heroAt: "No estoque de segurança",
  heroAbove: "Acima do estoque de segurança",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  clearFilters: "Limpar",
  loading: "Carregando materiais…",
  loadingFilters: "Carregando filtros…",
  filtersUnavailable:
    "Opções de filtro indisponíveis — os filtros básicos continuam funcionando.",
  emptyTitle: "Nenhum material encontrado",
  emptyMessage:
    "Nenhum material corresponde aos filtros selecionados neste recorte.",
  emptyClearAction: "Limpar filtros",
  emptyHelpAction: "Abrir Ajuda",
  error: "Não foi possível carregar o estoque de segurança.",
  errorSummary: "Resumo indisponível — a listagem não foi afetada.",
  forbidden:
    "Você não tem permissão para consultar o estoque de segurança. Peça o acesso canônico ao administrador.",
  invalidResponse:
    "Resposta inválida do servidor — os dados não puderam ser interpretados.",
  retry: "Tentar novamente",
  colProduct: "Produto",
  colDescription: "Descrição",
  colBranch: "Filial",
  colType: "Tipo",
  colGroup: "Grupo",
  colUm: "UM",
  colSafetyStock: "Estoque de Segurança",
  colPrimaryStock: "Saldo principal",
  colWorkInProcessStock: "Em processo",
  colDeficit: "Déficit",
  colStatus: "Status",
  colDetails: "Detalhes",
  tableScrollRegion:
    "Tabela de materiais — deslize horizontalmente para ver todas as colunas",
} as const;

/** Rótulos PT-BR; a classificação em si é sempre do produtor. */
export const SAFETY_STOCK_STATUS_LABELS: Record<SafetyStockStatus, string> = {
  without_safety_stock: "Sem estoque de segurança",
  below_safety_stock: "Abaixo do estoque de segurança",
  at_safety_stock: "No estoque de segurança",
  above_safety_stock: "Acima do estoque de segurança",
};

export function labelSafetyStockStatus(status: string | null | undefined): string {
  const code = String(status ?? "").trim();
  if (code && code in SAFETY_STOCK_STATUS_LABELS) {
    return SAFETY_STOCK_STATUS_LABELS[code as SafetyStockStatus];
  }
  return code || "—";
}

export function statusBadgeVariant(
  status: string | null | undefined,
): "neutral" | "warning" | "danger" {
  switch (status) {
    case "below_safety_stock":
      return "danger";
    case "at_safety_stock":
      return "warning";
    default:
      return "neutral";
  }
}

export function mapSafetyStockFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return SAFETY_STOCK_CONTENT.forbidden;
  }
  return message || SAFETY_STOCK_CONTENT.error;
}

/* ------------------------------------------------------------------ */
/* E11.S3 — detalhe do item (drawer/modal)                              */
/* ------------------------------------------------------------------ */

export const SAFETY_STOCK_DETAIL_CONTENT = {
  openAction: "Ver detalhes",
  openActionLabel: (code: string) =>
    `Ver detalhes do material ${code}`,
  title: (code: string) => `Material ${code}`,
  description:
    "Dados de estoque de segurança do material nesta filial, calculados pelo servidor.",
  loading: "Carregando detalhes do material…",
  loadingSuppliers: "Carregando fornecedores…",
  error:
    "Não foi possível carregar os detalhes deste material.",
  errorSuppliers:
    "Fornecedores indisponíveis — as demais seções não foram afetadas.",
  notFound: "Material não encontrado nesta filial.",
  forbidden:
    "Você não tem permissão para consultar os detalhes deste material.",
  invalidResponse:
    "Resposta inválida do servidor — os dados não puderam ser interpretados.",
  retry: "Tentar novamente",
  sectionUnavailable:
    "Esta seção não foi retornada pelo servidor e não pode ser exibida.",
  sectionIdentification: "Identificação",
  sectionStock: "Estoque e cobertura",
  sectionSupply: "Abastecimento",
  sectionProjection: "Projeção de estoque",
  sectionConsumption: "Consumo",
  sectionSuppliers: "Fornecedores vinculados",
  labelProduct: "Produto",
  labelDescription: "Descrição",
  labelBranch: "Filial",
  labelUnit: "UM",
  labelSecondaryUnit: "UM secundária",
  labelConversionFactor: "Fator de conversão",
  labelConversionType: "Tipo de conversão",
  labelGroup: "Grupo",
  labelType: "Tipo",
  labelBlocked: "Bloqueado",
  labelStatus: "Status",
  labelSafetyStock: "Estoque de Segurança",
  labelAvailableStock: "Saldo disponível (01+98+99)",
  labelPrimaryStock: "Saldo armazém principal (01)",
  labelWarehouse50: "Saldo armazém 50",
  labelWarehouse98: "Saldo armazém 98",
  labelWarehouse99: "Saldo armazém 99",
  labelWorkInProcess: "Em processo",
  labelWorkInProcessCommitted: "Em processo (empenhado)",
  labelWorkInProcessAvailable: "Em processo (disponível)",
  labelDeficit: "Déficit",
  labelLastInventoryDate: "Último inventário",
  coverageTitle: "Cobertura do déficit",
  coverageStatus: "Situação da cobertura",
  coverageDeficit: "Déficit",
  coverageEligible: "Em aberto elegível",
  coverageRemaining: "Falta comprar",
  coverageOpenOrders: "Pedidos em aberto",
  coverageEligibleOrders: "Pedidos elegíveis",
  coverageNextDelivery: "Próxima entrega",
  ordersTitle: "Pedidos de compra em aberto",
  ordersEmpty: "Nenhum pedido de compra em aberto para este material.",
  requestsTitle: "Solicitações de compra em aberto",
  requestsEmpty: "Nenhuma solicitação de compra em aberto para este material.",
  commitmentsTitle: "Empenhos",
  commitmentsEmpty: "Nenhum empenho em aberto para este material.",
  projectionEmpty: "Sem movimentos projetados para este material.",
  projectionInitial: "Saldo inicial",
  projectionPurchases: "Compras elegíveis",
  projectionCommitments: "Empenhos elegíveis",
  projectionFinal: "Saldo final projetado",
  projectionAfterSafety: "Saldo final após o estoque de segurança",
  projectionMinimum: "Saldo mínimo projetado",
  projectionFirstShortage: "Primeira ruptura",
  projectionRemainingToBuy: "Quantidade projetada a comprar",
  projectionAsOf: "Data base",
  monthlyConsumptionTitle: "Consumo mensal",
  monthlyConsumptionEmpty: "Sem consumo registrado no período.",
  monthlyPeriodConsumption: "Consumo do período",
  monthlyPeriod: "Período",
  annualComparisonTitle: "Comparação anual",
  annualComparisonEmpty: "Sem histórico de consumo para comparar.",
  suppliersTitle: "Fornecedores vinculados",
  suppliersEmpty: "Nenhum fornecedor vinculado a este material.",
  supplierLastPurchase: "Última compra",
  supplierNoPurchase: "Sem compra registrada",
  colOrder: "Pedido",
  colRequest: "Solicitação",
  colItem: "Item",
  colSupplier: "Fornecedor",
  colWarehouse: "Armazém",
  colUnit: "UM",
  colQuantity: "Quantidade",
  colOpenQuantity: "Qtd. em aberto",
  colRequested: "Solicitada",
  colOrdered: "Atendida",
  colDelivered: "Entregue",
  colIssueDate: "Emissão",
  colExpectedDelivery: "Entrega prevista",
  colRequiredDate: "Necessidade",
  colCommitmentDate: "Data empenho",
  colProductionOrder: "Ordem produção",
  colFinishedProduct: "Produto acabado",
  colOriginal: "Original",
  colConsumed: "Consumida",
  colUnitPrice: "Preço unit.",
  colOpenValue: "Valor em aberto",
  colTotalValue: "Valor total",
  colEvent: "Evento",
  colDate: "Data",
  colReference: "Referência",
  colMovement: "Movimento",
  colInflow: "Entrada",
  colOutflow: "Saída",
  colRunningBalance: "Saldo",
  colMonth: "Mês",
  colConsumption: "Consumo",
  colMovements: "Movimentos",
  colSupplierCode: "Código",
  colSupplierStore: "Loja",
  colSupplierName: "Fornecedor",
  colDocument: "CNPJ",
  colPartNumber: "Cód. fornecedor",
  colLastDate: "Data",
  colLastInvoice: "Nota fiscal",
  warningsTitle: "Alertas do produtor",
} as const;

/** Cobertura de déficit (produtor: sufficient|partial|none). */
export const SAFETY_STOCK_COVERAGE_STATUS_LABELS: Record<string, string> = {
  sufficient: "Coberta",
  partial: "Parcialmente coberta",
  none: "Sem cobertura",
};

/** Status da projeção (produtor). */
export const SAFETY_STOCK_PROJECTION_STATUS_LABELS: Record<string, string> = {
  sufficient: "Suficiente",
  temporary_shortage: "Ruptura temporária",
  projected_deficit: "Déficit projetado",
};

/** Status de data do extrato (produtor). */
export const SAFETY_STOCK_DATE_STATUS_LABELS: Record<string, string> = {
  today: "Hoje",
  scheduled: "Agendado",
  overdue: "Vencido",
  unscheduled: "Sem data",
};

export function labelDetailStatus(
  labels: Record<string, string>,
  status: string | null | undefined,
): string {
  const code = String(status ?? "").trim();
  if (code && code in labels) return labels[code];
  return code || "—";
}
