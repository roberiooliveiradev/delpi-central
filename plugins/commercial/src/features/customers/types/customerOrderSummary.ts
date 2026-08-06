import type { PedidosVendaAbertosItem } from "../../../types/pedidosVendaAbertos.ts";

export type CustomerOrderSituation = "atrasado" | "parcial" | "em_aberto";

export type CustomerOrderSummary = {
  key: string;
  filial: string;
  pedido: string;
  pedidoCliente: string;
  quantidadeLinhas: number;
  valorTotalAberto: number;
  quantidadeLinhasAtrasadas: number;
  maiorAtrasoDias: number;
  proximaEntrega: string | null;
  temAtraso: boolean;
  temParcial: boolean;
  situacao: CustomerOrderSituation;
  /** Referências às linhas do dataset (não clonar). */
  lines: PedidosVendaAbertosItem[];
};
