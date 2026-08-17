import type { OpenOrdersTotvsItem } from "../../types/openOrdersTotvs";
import {
  createInitialOpenOrderDetailState,
  reduceOpenOrderDetailState,
  selectOpenOrderDetailSnapshot,
  type OpenOrderDetailAction,
  type OpenOrderDetailState,
} from "./openOrderDetailState";

export type OpenOrderOpRouteIdentity = {
  branch: string;
  orderNumber: string;
  lineItem: string;
  productionOrder: string;
};

export type OpenOrderOpDetailState = OpenOrderDetailState<OpenOrdersTotvsItem>;
export type OpenOrderOpDetailAction = OpenOrderDetailAction<OpenOrdersTotvsItem>;

export const INITIAL_OPEN_ORDER_OP_DETAIL_STATE =
  createInitialOpenOrderDetailState<OpenOrdersTotvsItem>();

export function buildOpenOrderOpRouteIdentity(identity: OpenOrderOpRouteIdentity): string {
  return JSON.stringify([
    identity.branch.trim(),
    identity.orderNumber.trim(),
    identity.lineItem.trim(),
    identity.productionOrder.trim(),
  ]);
}

export function reduceOpenOrderOpDetailState(
  state: OpenOrderOpDetailState,
  action: OpenOrderOpDetailAction,
): OpenOrderOpDetailState {
  return reduceOpenOrderDetailState(state, action);
}

export function selectOpenOrderOpSnapshot(
  state: OpenOrderOpDetailState,
  identity: string,
): OpenOrdersTotvsItem | null {
  return selectOpenOrderDetailSnapshot(state, identity);
}
