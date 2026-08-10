import { describe, expect, it } from "vitest";

import type { OpenOrdersTotvsItem } from "../../types/openOrdersTotvs";
import {
  buildOpenOrderOpRouteIdentity,
  INITIAL_OPEN_ORDER_OP_DETAIL_STATE,
  reduceOpenOrderOpDetailState,
  selectOpenOrderOpSnapshot,
} from "./openOrderOpDetailState";

function item(order = "000123"): OpenOrdersTotvsItem {
  return {
    nome_cliente: "Cliente",
    tipo_entidade: "cliente",
    tipo_pedido: "venda",
    pedido_cliente: "",
    filial: "01",
    pedido: order,
    linha: "01",
    produto: "PROD-1",
    codigo_cliente: "C-1",
    codigo_cadastro: "000001",
    loja_cadastro: "01",
    quantidade: 10,
    entregue: 0,
    saldo: 10,
    data_despacho: null,
    data_entrega: "2026-08-20",
    no_estoque: 0,
    preco_venda: 10,
    valor_aberto: 100,
  };
}

const firstIdentity = buildOpenOrderOpRouteIdentity({
  branch: "01",
  orderNumber: "000123",
  lineItem: "01",
  productionOrder: "OP-1",
});
const secondIdentity = buildOpenOrderOpRouteIdentity({
  branch: "01",
  orderNumber: "000456",
  lineItem: "01",
  productionOrder: "OP-2",
});

describe("estado da página de detalhe da OP", () => {
  it("preserva snapshot e sinaliza refreshing na mesma identidade", () => {
    const loading = reduceOpenOrderOpDetailState(INITIAL_OPEN_ORDER_OP_DETAIL_STATE, {
      type: "request_started",
      identity: firstIdentity,
    });
    const loaded = reduceOpenOrderOpDetailState(loading, {
      type: "request_succeeded",
      identity: firstIdentity,
      item: item(),
    });
    const refreshing = reduceOpenOrderOpDetailState(loaded, {
      type: "request_started",
      identity: firstIdentity,
    });

    expect(refreshing.status).toBe("refreshing");
    expect(selectOpenOrderOpSnapshot(refreshing, firstIdentity)?.pedido).toBe("000123");
  });

  it.each([
    { type: "request_not_found" as const, message: "A OP não foi encontrada." },
    { type: "request_failed" as const, message: "Falha temporária." },
  ])("preserva snapshot e expõe aviso após $type no refresh", (failure) => {
    const loaded = reduceOpenOrderOpDetailState(
      reduceOpenOrderOpDetailState(
        reduceOpenOrderOpDetailState(INITIAL_OPEN_ORDER_OP_DETAIL_STATE, {
          type: "request_started",
          identity: firstIdentity,
        }),
        {
          type: "request_succeeded",
          identity: firstIdentity,
          item: item(),
        },
      ),
      { type: "request_started", identity: firstIdentity },
    );
    const failed = reduceOpenOrderOpDetailState(loaded, {
      ...failure,
      identity: firstIdentity,
    });

    expect(selectOpenOrderOpSnapshot(failed, firstIdentity)).not.toBeNull();
    expect(failed.refreshNotice).toBe(failure.message);
    expect(failed.blockingError).toBeNull();
    expect(failed.blockingEmpty).toBeNull();
  });

  it("limpa imediatamente o snapshot ao mudar a identidade da rota", () => {
    const loaded = reduceOpenOrderOpDetailState(
      reduceOpenOrderOpDetailState(INITIAL_OPEN_ORDER_OP_DETAIL_STATE, {
        type: "request_started",
        identity: firstIdentity,
      }),
      {
        type: "request_succeeded",
        identity: firstIdentity,
        item: item(),
      },
    );
    const nextRoute = reduceOpenOrderOpDetailState(loaded, {
      type: "request_started",
      identity: secondIdentity,
    });

    expect(nextRoute.status).toBe("loading");
    expect(selectOpenOrderOpSnapshot(nextRoute, secondIdentity)).toBeNull();
    expect(selectOpenOrderOpSnapshot(nextRoute, firstIdentity)).toBeNull();
  });

  it("ignora conclusão tardia de request anterior", () => {
    const nextRoute = reduceOpenOrderOpDetailState(
      reduceOpenOrderOpDetailState(INITIAL_OPEN_ORDER_OP_DETAIL_STATE, {
        type: "request_started",
        identity: firstIdentity,
      }),
      { type: "request_started", identity: secondIdentity },
    );
    const staleCompletion = reduceOpenOrderOpDetailState(nextRoute, {
      type: "request_succeeded",
      identity: firstIdentity,
      item: item(),
    });

    expect(staleCompletion).toBe(nextRoute);
    expect(selectOpenOrderOpSnapshot(staleCompletion, secondIdentity)).toBeNull();
  });

  it("mantém erro inicial bloqueante sem snapshot", () => {
    const failed = reduceOpenOrderOpDetailState(
      reduceOpenOrderOpDetailState(INITIAL_OPEN_ORDER_OP_DETAIL_STATE, {
        type: "request_started",
        identity: firstIdentity,
      }),
      {
        type: "request_failed",
        identity: firstIdentity,
        message: "Falha inicial.",
      },
    );

    expect(failed.blockingError).toBe("Falha inicial.");
    expect(failed.refreshNotice).toBeNull();
  });
});
