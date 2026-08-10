import { describe, expect, it } from "vitest";

import type { OpenOrdersTotvsItem } from "../../types/openOrdersTotvs";
import {
  buildOpenOrderLineRouteIdentity,
  INITIAL_OPEN_ORDER_LINE_DETAIL_STATE,
  reduceOpenOrderLineDetailState,
  selectOpenOrderLineSnapshot,
} from "./openOrderLineDetailState";

const item = {
  filial: "01",
  pedido: "000123",
  linha: "01",
} as OpenOrdersTotvsItem;

const identity = buildOpenOrderLineRouteIdentity({
  branch: "01",
  orderNumber: "000123",
  lineItem: "01",
});
const nextIdentity = buildOpenOrderLineRouteIdentity({
  branch: "01",
  orderNumber: "000456",
  lineItem: "02",
});

describe("estado da página de detalhe da linha", () => {
  it("preserva o snapshot durante refresh e falha temporária", () => {
    const loading = reduceOpenOrderLineDetailState(INITIAL_OPEN_ORDER_LINE_DETAIL_STATE, {
      type: "request_started",
      identity,
    });
    const loaded = reduceOpenOrderLineDetailState(loading, {
      type: "request_succeeded",
      identity,
      item,
    });
    const refreshing = reduceOpenOrderLineDetailState(loaded, {
      type: "request_started",
      identity,
    });
    const failed = reduceOpenOrderLineDetailState(refreshing, {
      type: "request_failed",
      identity,
      message: "Falha temporária.",
    });

    expect(refreshing.status).toBe("refreshing");
    expect(selectOpenOrderLineSnapshot(failed, identity)).toBe(item);
    expect(failed.refreshNotice).toBe("Falha temporária.");
    expect(failed.blockingError).toBeNull();
  });

  it("expõe vazio bloqueante quando ainda não há snapshot", () => {
    const empty = reduceOpenOrderLineDetailState(
      reduceOpenOrderLineDetailState(INITIAL_OPEN_ORDER_LINE_DETAIL_STATE, {
        type: "request_started",
        identity,
      }),
      {
        type: "request_not_found",
        identity,
        message: "Linha não encontrada.",
      },
    );

    expect(empty.blockingEmpty).toBe("Linha não encontrada.");
    expect(selectOpenOrderLineSnapshot(empty, identity)).toBeNull();
  });

  it("descarta snapshot e conclusão tardia ao trocar de linha", () => {
    const loaded = reduceOpenOrderLineDetailState(
      reduceOpenOrderLineDetailState(INITIAL_OPEN_ORDER_LINE_DETAIL_STATE, {
        type: "request_started",
        identity,
      }),
      { type: "request_succeeded", identity, item },
    );
    const nextRoute = reduceOpenOrderLineDetailState(loaded, {
      type: "request_started",
      identity: nextIdentity,
    });
    const staleCompletion = reduceOpenOrderLineDetailState(nextRoute, {
      type: "request_succeeded",
      identity,
      item,
    });

    expect(nextRoute.status).toBe("loading");
    expect(selectOpenOrderLineSnapshot(nextRoute, identity)).toBeNull();
    expect(selectOpenOrderLineSnapshot(nextRoute, nextIdentity)).toBeNull();
    expect(staleCompletion).toBe(nextRoute);
  });
});
