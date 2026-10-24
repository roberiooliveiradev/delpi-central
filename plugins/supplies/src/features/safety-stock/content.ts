import type { SafetyStockStatus } from "./types";

export const SAFETY_STOCK_CONTENT = {
  title: "Estoque de Segurança",
  eyebrow: "Portal Suprimentos",
  description:
    "Materiais com estoque de segurança parametrizado no Protheus: saldo × ESTSEG, déficit e classificação por unidade. Valores calculados pelo servidor.",
  filtersAriaLabel: "Filtros de estoque de segurança",
  filtersTitle: "Filtros",
  listTitle: "Materiais",
  listHint:
    "Cada linha é um produto em uma filial. Classificação e déficit vêm do servidor; o Portal não recalcula.",
  tableMeta: (columns: number, rows: number) =>
    `${columns} coluna(s) · ${rows.toLocaleString("pt-BR")} material(is)`,
  branchLabel: "Filial",
  branchAllOption: "Todas as filiais",
  statusLabel: "Status",
  statusEmptyOption: "Todos",
  productGroupLabel: "Grupo",
  productGroupEmptyOption: "Todos",
  unitLabel: "UM",
  unitEmptyOption: "Todas",
  searchLabel: "Busca",
  searchPlaceholder: "Código ou descrição do produto",
  includeBlockedLabel: "Incluir bloqueados",
  includeWithoutSafetyStockLabel: "Incluir sem ESTSEG",
  coverageTitle: "Cobertura do recorte",
  coverageWithPrimary: "Com saldo principal",
  coverageWithoutPrimary: "Sem saldo principal",
  coverageWorkInProcess: "Com saldo em processo",
  deficitTitle: "Déficit por unidade de medida",
  deficitEmpty: "Sem déficit no recorte.",
  deficitChip: (unit: string, quantity: string, count: number) =>
    `${unit}: ${quantity} (${count.toLocaleString("pt-BR")} material(is))`,
  heroTotal: "Materiais",
  heroWithSafetyStock: "Com ESTSEG",
  heroWithoutSafetyStock: "Sem ESTSEG",
  heroBelow: "Abaixo do ESTSEG",
  heroAt: "No ESTSEG",
  heroAbove: "Acima do ESTSEG",
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
  colSafetyStock: "ESTSEG",
  colPrimaryStock: "Saldo principal",
  colWorkInProcessStock: "Em processo",
  colDeficit: "Déficit",
  colStatus: "Status",
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
