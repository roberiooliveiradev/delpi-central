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
  it("usa status e tendência comerciais existentes", () => {
    const customers = [
      customer({ key: "attention", status: "atencao" }),
      customer({ key: "inactive", status: "inativo" }),
      customer({ key: "growth", billingTrend: "up" }),
    ];
    assert.deepEqual(
      filterCustomers(customers, "", "attention").map((item) => item.key),
      ["attention"],
    );
    assert.deepEqual(
      filterCustomers(customers, "", "inactive").map((item) => item.key),
      ["inactive"],
    );
    assert.deepEqual(
      filterCustomers(customers, "", "growth").map((item) => item.key),
      ["growth"],
    );
  });

  it("considera última compra real e ausência de registro em no_sale_60", () => {
    const customers = [
      customer({ key: "recent" }),
      customer({ key: "old", lastPurchaseDate: "2000-01-01" }),
      customer({ key: "unknown", lastPurchaseDate: null }),
    ];
    assert.deepEqual(
      filterCustomers(customers, "", "no_sale_60").map((item) => item.key),
      ["old", "unknown"],
    );
  });
});
