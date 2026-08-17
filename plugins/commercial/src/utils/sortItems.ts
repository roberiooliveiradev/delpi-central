import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { compareDeliveryDates, getDeliveryOverdueDays } from "./dates";
import { getLineOpForecast } from "./opAllocation";
import { getAllocatedStock } from "./stockAllocation";
import { getLineStatusSortRank } from "./statusBadges";

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
  | "cobertura"
  | "valor_aberto"
  | "previsao_entrega_op"
  | "atraso_dias"
  | "status";

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

function coverageRatio(item: OpenOrdersTotvsItem): number {
  if (item.saldo <= 0) return 1;
  return getAllocatedStock(item) / item.saldo;
}

export function sortPedidosItems(
  items: OpenOrdersTotvsItem[],
  key: SortKey,
  direction: SortDirection,
): OpenOrdersTotvsItem[] {
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
      case "cobertura":
        result = coverageRatio(a) - coverageRatio(b);
        break;
      case "valor_aberto":
        result = a.valor_aberto - b.valor_aberto;
        break;
      case "previsao_entrega_op": {
        const leftDate = getLineOpForecast(a).previsaoData;
        const rightDate = getLineOpForecast(b).previsaoData;
        result = compareNullableDate(leftDate, rightDate);
        break;
      }
      case "atraso_dias": {
        const left = getDeliveryOverdueDays(a.data_entrega) ?? 0;
        const right = getDeliveryOverdueDays(b.data_entrega) ?? 0;
        result = left - right;
        break;
      }
      case "status": {
        result = getLineStatusSortRank(a) - getLineStatusSortRank(b);
        if (result === 0) {
          result = compareStrings(a.pedido, b.pedido) || compareStrings(a.linha, b.linha);
        }
        break;
      }
      default:
        result = 0;
    }

    return direction === "asc" ? result : -result;
  });

  return sorted;
}
