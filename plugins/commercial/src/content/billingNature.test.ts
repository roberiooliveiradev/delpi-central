import { describe, expect, it } from "vitest";

import {
  BILLING_NATURE_CONTENT,
  appendBillingNatureContext,
  billingNatureHint,
  billingNatureShortLabel,
  isGrossBillingNatureAvailable,
} from "./billingNature";

describe("billingNature", () => {
  it("rótulo líquido para ROL (net) e valor aberto para carteira", () => {
    expect(billingNatureShortLabel("net")).toBe("Líquido");
    expect(billingNatureShortLabel("open_order_value")).toBe("Valor aberto");
    expect(billingNatureHint("net")).toMatch(/líquida/i);
    expect(billingNatureHint("open_order_value")).toMatch(/aberto/i);
  });

  it("não habilita toggle bruto sem nature=gross no contrato", () => {
    expect(isGrossBillingNatureAvailable(undefined)).toBe(false);
    expect(isGrossBillingNatureAvailable("net")).toBe(false);
    expect(isGrossBillingNatureAvailable("open_order_value")).toBe(false);
    expect(isGrossBillingNatureAvailable("gross")).toBe(true);
    expect(BILLING_NATURE_CONTENT.gross.hint).toContain("bloqueado");
  });

  it("acrescenta o rótulo de natureza no contexto do KPI", () => {
    expect(appendBillingNatureContext("SC", "net")).toBe("SC · Líquido");
    expect(appendBillingNatureContext("Líquido", "net")).toBe("Líquido");
  });
});
