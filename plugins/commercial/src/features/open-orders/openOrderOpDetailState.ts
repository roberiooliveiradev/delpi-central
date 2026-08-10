import type { OpenOrdersTotvsItem } from "../../types/openOrdersTotvs";

export type OpenOrderOpRouteIdentity = {
  branch: string;
  orderNumber: string;
  lineItem: string;
  productionOrder: string;
};

type OpenOrderOpSnapshot = {
  identity: string;
  item: OpenOrdersTotvsItem;
};

export type OpenOrderOpDetailState = {
  requestIdentity: string | null;
  snapshot: OpenOrderOpSnapshot | null;
  status: "idle" | "loading" | "refreshing";
  blockingError: string | null;
  blockingEmpty: string | null;
  refreshNotice: string | null;
};

export type OpenOrderOpDetailAction =
  | { type: "request_started"; identity: string }
  | { type: "request_succeeded"; identity: string; item: OpenOrdersTotvsItem }
  | { type: "request_not_found"; identity: string; message: string }
  | { type: "request_failed"; identity: string; message: string };

export const INITIAL_OPEN_ORDER_OP_DETAIL_STATE: OpenOrderOpDetailState = {
  requestIdentity: null,
  snapshot: null,
  status: "idle",
  blockingError: null,
  blockingEmpty: null,
  refreshNotice: null,
};

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
  if (action.type === "request_started") {
    const canRefreshSnapshot = state.snapshot?.identity === action.identity;
    return {
      requestIdentity: action.identity,
      snapshot: canRefreshSnapshot ? state.snapshot : null,
      status: canRefreshSnapshot ? "refreshing" : "loading",
      blockingError: null,
      blockingEmpty: null,
      refreshNotice: null,
    };
  }

  if (state.requestIdentity !== action.identity) return state;

  if (action.type === "request_succeeded") {
    return {
      requestIdentity: action.identity,
      snapshot: { identity: action.identity, item: action.item },
      status: "idle",
      blockingError: null,
      blockingEmpty: null,
      refreshNotice: null,
    };
  }

  const hasCurrentSnapshot = state.snapshot?.identity === action.identity;
  if (action.type === "request_not_found") {
    return {
      ...state,
      status: "idle",
      blockingEmpty: hasCurrentSnapshot ? null : action.message,
      refreshNotice: hasCurrentSnapshot ? action.message : null,
    };
  }

  return {
    ...state,
    status: "idle",
    blockingError: hasCurrentSnapshot ? null : action.message,
    refreshNotice: hasCurrentSnapshot ? action.message : null,
  };
}

export function selectOpenOrderOpSnapshot(
  state: OpenOrderOpDetailState,
  identity: string,
): OpenOrdersTotvsItem | null {
  return state.snapshot?.identity === identity ? state.snapshot.item : null;
}
