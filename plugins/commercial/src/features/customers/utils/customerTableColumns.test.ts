import { describe, expect, it } from "vitest";

import { createCustomerDefaultColumnVisibility } from "./customerTableColumns";

describe("createCustomerDefaultColumnVisibility", () => {
  it("mantém uma bancada enxuta no escopo individual", () => {
    expect(createCustomerDefaultColumnVisibility(false)).toEqual({
      nome: true,
      sellerName: false,
      city: false,
      lastPurchaseDate: false,
      billed12m: false,
      billingTrend: false,
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
