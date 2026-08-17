export type OpenOrderDetailState<T> = {
  requestIdentity: string | null;
  snapshot: { identity: string; item: T } | null;
  status: "idle" | "loading" | "refreshing";
  blockingError: string | null;
  blockingEmpty: string | null;
  refreshNotice: string | null;
};

export type OpenOrderDetailAction<T> =
  | { type: "request_started"; identity: string }
  | { type: "request_succeeded"; identity: string; item: T }
  | { type: "request_not_found"; identity: string; message: string }
  | { type: "request_failed"; identity: string; message: string };

export function createInitialOpenOrderDetailState<T>(): OpenOrderDetailState<T> {
  return {
    requestIdentity: null,
    snapshot: null,
    status: "idle",
    blockingError: null,
    blockingEmpty: null,
    refreshNotice: null,
  };
}

export function reduceOpenOrderDetailState<T>(
  state: OpenOrderDetailState<T>,
  action: OpenOrderDetailAction<T>,
): OpenOrderDetailState<T> {
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
  const isEmpty = action.type === "request_not_found";
  return {
    ...state,
    status: "idle",
    blockingError: !hasCurrentSnapshot && !isEmpty ? action.message : null,
    blockingEmpty: !hasCurrentSnapshot && isEmpty ? action.message : null,
    refreshNotice: hasCurrentSnapshot ? action.message : null,
  };
}

export function selectOpenOrderDetailSnapshot<T>(
  state: OpenOrderDetailState<T>,
  identity: string,
): T | null {
  return state.snapshot?.identity === identity ? state.snapshot.item : null;
}
