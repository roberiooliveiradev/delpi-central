import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { mergePortfolioCustomersWithOpenOrders } from "./mergePortfolioCustomersWithOpenOrders.ts";

describe("mergePortfolioCustomersWithOpenOrders", () => {
  it("mantem vinculado sem linhas de aberto", () => {
    const merged = mergePortfolioCustomersWithOpenOrders(
      [
        {
          customer_code: "000204",
          customer_store: "01",
          customer_name: "AHT",
          open_value: 0,
          has_overdue: false,
          has_open_orders: false,
        },
        {
          customer_code: "000100",
          customer_store: "01",
          customer_name: "Com aberto",
          open_value: 99,
          has_overdue: true,
          has_open_orders: true,
        },
      ],
      [
        {
          key: "000100|01",
          codigo: "000100",
          loja: "01",
          nome: "Com aberto",
          quantidadePedidosAbertos: 2,
          quantidadeLinhasAbertas: 3,
          valorTotalAberto: 99,
          quantidadePedidosAtrasados: 1,
          maiorAtrasoDias: 5,
          proximaEntrega: null,
          quantidadePedidosParciais: 0,
          temAtraso: true,
          temPedidoParcial: false,
          lines: [],
        },
      ],
    );
    assert.equal(merged.length, 2);
    const byCode = Object.fromEntries(merged.map((c) => [c.codigo, c]));
    assert.equal(byCode["000204"].quantidadePedidosAbertos, 0);
    assert.equal(byCode["000204"].valorTotalAberto, 0);
    assert.equal(byCode["000100"].quantidadePedidosAbertos, 2);
    assert.equal(byCode["000100"].temAtraso, true);
  });
});
