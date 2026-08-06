import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import { compareDeliveryDates } from "./dates";
import { getLineOpPrevisao } from "./opAllocation";

export type SortKey =
  | "nome_cliente"
  | "loja_cadastro"
  | "filial"
  | "pedido"
  | "pedido_cliente"
  | "produto"
  | "data_entrega"
  | "data_despacho"
  | "saldo"
  | "valor_aberto"
  | "previsao_entrega_op";

export type SortDirection = "asc" | "desc";

export const DEFAULT_SORT: { key: SortKey; direction: SortDirection } = {
  key: "data_entrega",
  direction: "asc",
};

function compareStrings(a: string | null, b: string | null): number {
  const left = (a ?? "").toLocaleLowerCase("pt-BR");
  const right = (b ?? "").toLocaleLowerCase("pt-BR");
  return left.localeCompare(right, "pt-BR");
}

function compareNullableDate(a: string | null, b: string | null): number {
  return compareDeliveryDates(a, b);
}

export function sortPedidosItems(
  items: PedidosVendaAbertosItem[],
  key: SortKey,
  direction: SortDirection,
): PedidosVendaAbertosItem[] {
  const sorted = [...items].sort((a, b) => {
    let result = 0;

    switch (key) {
      case "nome_cliente":
        result = compareStrings(a.nome_cliente, b.nome_cliente);
        break;
      case "loja_cadastro":
        result = compareStrings(a.loja_cadastro, b.loja_cadastro);
        break;
      case "filial":
        result = compareStrings(a.filial, b.filial);
        break;
      case "pedido":
        result = compareStrings(a.pedido, b.pedido);
        break;
      case "pedido_cliente":
        result = compareStrings(a.pedido_cliente, b.pedido_cliente);
        break;
      case "produto":
        result = compareStrings(a.produto, b.produto);
        break;
      case "data_entrega":
        result = compareNullableDate(a.data_entrega, b.data_entrega);
        break;
      case "data_despacho":
        result = compareNullableDate(a.data_despacho, b.data_despacho);
        break;
      case "saldo":
        result = a.saldo - b.saldo;
        break;
      case "valor_aberto":
        result = a.valor_aberto - b.valor_aberto;
        break;
      case "previsao_entrega_op": {
        const leftDate = getLineOpPrevisao(a).previsaoData;
        const rightDate = getLineOpPrevisao(b).previsaoData;
        result = compareNullableDate(leftDate, rightDate);
        break;
      }
      default:
        result = 0;
    }

    return direction === "asc" ? result : -result;
  });

  return sorted;
}
