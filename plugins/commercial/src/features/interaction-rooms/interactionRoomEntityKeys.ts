import {
  buildCustomerKey,
  buildOrderKey,
} from "../customers/utils/customerIdentity";

/** Chave estável OP: `filial|ordem` (mesma família pipe das outras entidades). */
export function buildProductionOrderEntityKey(
  branch: string | null | undefined,
  productionOrder: string | null | undefined,
): string | null {
  const key = buildOrderKey(branch, productionOrder);
  const [left, right] = key.split("|");
  if (!left || !right) return null;
  return key;
}

export function buildCustomerEntityKey(
  codigo: string | null | undefined,
  loja: string | null | undefined,
): string | null {
  return buildCustomerKey(codigo, loja);
}

export function buildOrderEntityKey(
  branch: string | null | undefined,
  orderNumber: string | null | undefined,
): string | null {
  const key = buildOrderKey(branch, orderNumber);
  const [left, right] = key.split("|");
  if (!left || !right) return null;
  return key;
}

export const INTERACTION_ENTITY_TYPES = {
  customer: "customer",
  order: "order",
  productionOrder: "production_order",
} as const;
