#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { filterCustomers } from "../features/customers/utils/customerFilters.ts";

function customer(overrides = {}) {
  return {
    key: "000001|01",
    codigo: "000001",
    loja: "01",
    nome: "ACME",
    quantidadePedidosAbertos: 1,
    quantidadeLinhasAbertas: 1,
    valorTotalAberto: 100,
    quantidadePedidosAtrasados: 0,
    maiorAtrasoDias: 0,
    proximaEntrega: null,
    quantidadePedidosParciais: 0,
    temAtraso: false,
    temPedidoParcial: false,
    lines: [],
    status: "ativo",
    lastPurchaseDate: new Date().toISOString().slice(0, 10),
    billingTrend: "stable",
    ...overrides,
  };
}

describe("filtros da lista de clientes", () => {
  it("separa status operacional e tendência de faturamento", () => {
    const customers = [
      customer({ key: "attention-up", status: "atencao", billingTrend: "up" }),
      customer({ key: "attention-stable", status: "atencao", billingTrend: "stable" }),
      customer({ key: "active-down", status: "ativo", billingTrend: "down" }),
      customer({ key: "active-up", status: "ativo", billingTrend: "up" }),
    ];
    assert.deepEqual(
      filterCustomers(customers, "", "attention").map((item) => item.key),
      ["attention-up", "attention-stable"],
    );
    assert.deepEqual(
      filterCustomers(customers, "", "active").map((item) => item.key),
      ["active-down", "active-up"],
    );
    assert.deepEqual(
      filterCustomers(customers, "", "all", "up").map((item) => item.key),
      ["attention-up", "active-up"],
    );
    assert.deepEqual(
      filterCustomers(customers, "", "attention", "up").map((item) => item.key),
      ["attention-up"],
    );
    assert.deepEqual(
      filterCustomers(customers, "", "all", "down").map((item) => item.key),
      ["active-down"],
    );
    assert.ok(
      !filterCustomers(customers, "", "all", "down").some((item) => item.billingTrend !== "down"),
    );
  });

  it("considera somente última compra conhecida em no_sale_60", () => {
    const customers = [
      customer({ key: "recent" }),
      customer({ key: "old", lastPurchaseDate: "2000-01-01" }),
      customer({ key: "unknown", lastPurchaseDate: null }),
    ];
    assert.deepEqual(
      filterCustomers(customers, "", "no_sale_60").map((item) => item.key),
      ["old"],
    );
  });
});
