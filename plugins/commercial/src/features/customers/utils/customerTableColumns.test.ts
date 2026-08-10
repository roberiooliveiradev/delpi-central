import { describe, expect, it } from "vitest";

import { createCustomerDefaultColumnVisibility } from "./customerTableColumns";

describe("createCustomerDefaultColumnVisibility", () => {
  it("segue as colunas default do WF-03R no escopo individual", () => {
    expect(createCustomerDefaultColumnVisibility(false)).toEqual({
      nome: true,
      sellerName: false,
      city: false,
      lastPurchaseDate: true,
      billed12m: true,
      billingTrend: true,
      status: true,
      valorTotalAberto: true,
      quantidadePedidosAtrasados: true,
      proximaEntrega: true,
    });
  });

  it("mostra vendedor por padrão somente para quem pode usar escopo de equipe", () => {
    expect(createCustomerDefaultColumnVisibility(true).sellerName).toBe(true);
    expect(createCustomerDefaultColumnVisibility(false).sellerName).toBe(false);
  });
});
