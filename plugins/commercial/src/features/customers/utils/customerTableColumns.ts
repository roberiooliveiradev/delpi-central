export const CUSTOMER_COLUMN_CATALOG = [
  { key: "nome", label: "Cliente" },
  { key: "sellerName", label: "Vendedor" },
  { key: "city", label: "Cidade / UF" },
  { key: "lastPurchaseDate", label: "Última venda" },
  { key: "billed12m", label: "Fat. 12 meses" },
  { key: "billingTrend", label: "Tendência" },
  { key: "status", label: "Status" },
  { key: "valorTotalAberto", label: "Em aberto" },
  { key: "quantidadePedidosAtrasados", label: "Atrasos" },
  { key: "proximaEntrega", label: "Próxima entrega" },
] as const;

export type CustomerColumnKey = (typeof CUSTOMER_COLUMN_CATALOG)[number]["key"];
export type CustomerColumnDef = (typeof CUSTOMER_COLUMN_CATALOG)[number];

export function createCustomerDefaultColumnVisibility(
  canUseTeamScope: boolean,
): Record<CustomerColumnKey, boolean> {
  return {
    nome: true,
    sellerName: canUseTeamScope,
    city: false,
    lastPurchaseDate: true,
    billed12m: true,
    billingTrend: true,
    status: true,
    valorTotalAberto: true,
    quantidadePedidosAtrasados: true,
    proximaEntrega: true,
  };
}
