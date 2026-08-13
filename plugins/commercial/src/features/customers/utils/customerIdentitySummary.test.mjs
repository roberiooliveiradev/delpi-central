import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildIdentityCustomerSummary,
  mergeCustomerIdentity,
} from "./customerIdentitySummary.ts";

describe("customerIdentitySummary", () => {
  it("monta shell sem pedidos", () => {
    const shell = buildIdentityCustomerSummary({
      codigo: "0001",
      loja: "01",
      nome: "Acme",
      enrichment: {
        customer_code: "0001",
        customer_store: "01",
        city: "Caxias",
        state: "RS",
        last_purchase_date: null,
        billed_12m: 10,
        has_avatar: false,
        avatar_url: null,
      },
    });
    assert.equal(shell?.nome, "Acme");
    assert.equal(shell?.quantidadePedidosAbertos, 0);
    assert.equal(shell?.city, "Caxias");
  });

  it("merge prefere pedidos e completa identidade", () => {
    const identity = buildIdentityCustomerSummary({
      codigo: "0001",
      loja: "01",
      nome: "Acme",
    });
    const fromOrders = {
      ...identity,
      nome: "",
      quantidadePedidosAbertos: 2,
      lines: [],
    };
    const merged = mergeCustomerIdentity(fromOrders, identity);
    assert.equal(merged?.nome, "Acme");
    assert.equal(merged?.quantidadePedidosAbertos, 2);
  });
});
