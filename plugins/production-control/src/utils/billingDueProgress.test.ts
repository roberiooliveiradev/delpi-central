import { describe, expect, it } from "vitest";

import { billingDueInvoicedPercent } from "./billingDueProgress";

describe("billingDueInvoicedPercent", () => {
  it("calcula o percentual faturado sobre o total do dia", () => {
    expect(billingDueInvoicedPercent(24, 30)).toBe(80);
  });

  it("retorna 0 sem linhas e 100 quando tudo foi faturado", () => {
    expect(billingDueInvoicedPercent(0, 0)).toBe(0);
    expect(billingDueInvoicedPercent(10, 10)).toBe(100);
  });

  it("não passa de 100%", () => {
    expect(billingDueInvoicedPercent(12, 10)).toBe(100);
  });
});
