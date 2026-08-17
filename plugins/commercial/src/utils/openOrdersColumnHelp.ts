import { CM_HELP } from "../content/helpTooltips";
import type { TableColumnKey } from "./tableColumns";

/** Ajuda por coluna — tabela, cards e export de preferências usam a mesma fonte. */
export const OPEN_ORDERS_COLUMN_HELP: Record<TableColumnKey, string> = {
  nome_cliente: CM_HELP.openOrders.columns.nome_cliente,
  loja_cadastro: CM_HELP.openOrders.columns.loja_cadastro,
  filial: CM_HELP.openOrders.columns.filial,
  pedido: CM_HELP.openOrders.columns.pedido,
  pedido_cliente: CM_HELP.openOrders.columns.pedido_cliente,
  produto: CM_HELP.openOrders.columns.produto,
  codigo_cliente: CM_HELP.openOrders.columns.codigo_cliente,
  quantidade: CM_HELP.openOrders.columns.quantidade,
  entregue: CM_HELP.openOrders.columns.entregue,
  saldo: CM_HELP.openOrders.columns.saldo,
  no_estoque: CM_HELP.openOrders.columns.no_estoque,
  cobertura: CM_HELP.openOrders.columns.cobertura,
  data_entrega: CM_HELP.openOrders.columns.data_entrega,
  previsao_entrega_op: CM_HELP.openOrders.columns.previsao_entrega_op,
  data_despacho: CM_HELP.openOrders.columns.data_despacho,
  valor_aberto: CM_HELP.openOrders.columns.valor_aberto,
  status: CM_HELP.openOrders.columns.status,
  atraso_dias: CM_HELP.openOrders.columns.atraso_dias,
};

export function openOrdersColumnHelp(key: TableColumnKey): string {
  return OPEN_ORDERS_COLUMN_HELP[key];
}
