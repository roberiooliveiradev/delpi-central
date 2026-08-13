import type { OpsAbertasData } from "../types/openOps";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import {
  allocateOpsToOrders,
  buildOpsProductIndex,
  getLineOpForecast,
} from "./opAllocation";
import { allocateStockToOrders } from "./stockAllocation";
import {
  findOpenOrderLine,
  type OpenOrdersLineDeepLink,
} from "./openOrdersDeepLink";

/**
 * Mesma cadeia da lista (estoque → OPs): detalhe de linha/OP precisa disso
 * porque a API TOTVS não entrega `previsao_op` pronto.
 */
export function enrichOpenOrdersWithOpForecast(
  items: OpenOrdersTotvsItem[],
  opsData: OpsAbertasData | null | undefined,
): OpenOrdersTotvsItem[] {
  return allocateOpsToOrders(
    allocateStockToOrders(items),
    buildOpsProductIndex(opsData),
  );
}

export function lineHasAllocatedOp(
  item: OpenOrdersTotvsItem,
  productionOrder: string,
): boolean {
  const target = productionOrder.trim();
  if (!target) return false;
  return getLineOpForecast(item).opsUtilizadas.some(
    (op) => op.numero_op.trim() === target,
  );
}

/**
 * Localiza a linha no escopo e exige que a OP esteja na alocação FIFO da linha
 * (mesmo critério do link na tabela).
 */
export function resolveOpenOrderOpDetailItem(
  items: OpenOrdersTotvsItem[],
  opsData: OpsAbertasData | null | undefined,
  link: OpenOrdersLineDeepLink & { productionOrder: string },
): OpenOrdersTotvsItem | null {
  const enriched = enrichOpenOrdersWithOpForecast(items, opsData);
  const matched = findOpenOrderLine(enriched, link);
  if (!matched) return null;
  if (!lineHasAllocatedOp(matched, link.productionOrder)) return null;
  return matched;
}
