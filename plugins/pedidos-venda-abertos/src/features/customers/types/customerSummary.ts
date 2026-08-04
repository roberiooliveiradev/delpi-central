import type { PedidosVendaAbertosItem } from "../../../types/pedidosVendaAbertos";

export type CustomerCommercialStatus = "ativo" | "atencao" | "inativo";

export type CustomerSummary = {
  key: string;
  codigo: string;
  loja: string;
  nome: string;
  quantidadePedidosAbertos: number;
  quantidadeLinhasAbertas: number;
  valorTotalAberto: number;
  quantidadePedidosAtrasados: number;
  maiorAtrasoDias: number;
  proximaEntrega: string | null;
  quantidadePedidosParciais: number;
  temAtraso: boolean;
  temPedidoParcial: boolean;
  /** Referências às linhas do dataset (não clonar). */
  lines: PedidosVendaAbertosItem[];
  /** Enrichment (SA1 / NF / avatar). */
  city?: string | null;
  state?: string | null;
  lastPurchaseDate?: string | null;
  billed12m?: number | null;
  hasAvatar?: boolean;
  /** Tendência: últimos 6m vs. 6m anteriores. */
  billingTrend?: "up" | "down" | "stable" | "insufficient" | null;
  billingTrendPct?: number | null;
  status?: CustomerCommercialStatus;
  nextAction?: string;
  /** Vendedor responsável pela carteira do cliente. */
  sellerName?: string | null;
};

export type CustomerAggregationResult = {
  customers: CustomerSummary[];
  incompleteLineCount: number;
  /** Pedidos distintos (filial+pedido) entre clientes válidos. */
  totalPedidosAbertos: number;
  totalValorAberto: number;
  clientesComAtraso: number;
};

export type CustomerAttentionFilter = "all" | "overdue" | "partial";

export type CustomerListSortKey =
  | "attention"
  | "nome"
  | "quantidadePedidosAtrasados"
  | "maiorAtrasoDias"
  | "valorTotalAberto"
  | "quantidadePedidosAbertos"
  | "proximaEntrega"
  | "billed12m"
  | "lastPurchaseDate"
  | "city"
  | "sellerName"
  | "billingTrend";

export type CustomerListSortDirection = "asc" | "desc";
