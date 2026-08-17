import type { OpenOrdersTotvsItem } from "../../types/openOrdersTotvs";
import {
  createInitialOpenOrderDetailState,
  reduceOpenOrderDetailState,
  selectOpenOrderDetailSnapshot,
  type OpenOrderDetailAction,
  type OpenOrderDetailState,
} from "./openOrderDetailState";

export type OpenOrderLineRouteIdentity = {
  branch: string;
  orderNumber: string;
  lineItem: string;
};

export type OpenOrderLineDetailState = OpenOrderDetailState<OpenOrdersTotvsItem>;
export type OpenOrderLineDetailAction = OpenOrderDetailAction<OpenOrdersTotvsItem>;

export const INITIAL_OPEN_ORDER_LINE_DETAIL_STATE =
  createInitialOpenOrderDetailState<OpenOrdersTotvsItem>();

export function buildOpenOrderLineRouteIdentity(identity: OpenOrderLineRouteIdentity): string {
  return JSON.stringify([
    identity.branch.trim(),
    identity.orderNumber.trim(),
    identity.lineItem.trim(),
  ]);
}

export function reduceOpenOrderLineDetailState(
  state: OpenOrderLineDetailState,
  action: OpenOrderLineDetailAction,
): OpenOrderLineDetailState {
  return reduceOpenOrderDetailState(state, action);
}

export function selectOpenOrderLineSnapshot(
  state: OpenOrderLineDetailState,
  identity: string,
): OpenOrdersTotvsItem | null {
  return selectOpenOrderDetailSnapshot(state, identity);
}
