import { describe, expect, it } from "vitest";

import {
  BILLING_NATURE_CONTENT,
  DEFAULT_PORTFOLIO_BILLING_NATURE,
  PORTFOLIO_SUPPORTED_BILLING_NATURES,
  appendBillingNatureContext,
  billingNatureHint,
  billingNatureShortLabel,
  isGrossBillingNatureAvailable,
  isPortfolioBillingNatureToggleAvailable,
  normalizePortfolioBillingNature,
} from "./billingNature";

describe("billingNature", () => {
  it("rótulo líquido para ROL (net) e valor aberto para carteira", () => {
    expect(billingNatureShortLabel("net")).toBe("Líquido");
    expect(billingNatureShortLabel("open_order_value")).toBe("Valor aberto");
    expect(billingNatureShortLabel("gross")).toBe("Bruto");
    expect(billingNatureHint("net")).toMatch(/líquida/i);
    expect(billingNatureHint("open_order_value")).toMatch(/aberto/i);
    expect(billingNatureHint("gross")).toMatch(/F2_VALBRUT/i);
  });

  it("habilita gross quando nature=gross ou supportedNatures inclui gross", () => {
    expect(isGrossBillingNatureAvailable(undefined)).toBe(false);
    expect(isGrossBillingNatureAvailable("net")).toBe(false);
    expect(isGrossBillingNatureAvailable("open_order_value")).toBe(false);
    expect(isGrossBillingNatureAvailable("gross")).toBe(true);
    expect(isGrossBillingNatureAvailable(["gross", "net"])).toBe(true);
    expect(BILLING_NATURE_CONTENT.gross.hint).toMatch(/F2_VALBRUT/i);
  });

  it("habilita toggle da carteira só com gross e net suportados", () => {
    expect(isPortfolioBillingNatureToggleAvailable(null)).toBe(false);
    expect(isPortfolioBillingNatureToggleAvailable(["net"])).toBe(false);
    expect(
      isPortfolioBillingNatureToggleAvailable(PORTFOLIO_SUPPORTED_BILLING_NATURES),
    ).toBe(true);
    expect(DEFAULT_PORTFOLIO_BILLING_NATURE).toBe("gross");
    expect(normalizePortfolioBillingNature("net")).toBe("net");
    expect(normalizePortfolioBillingNature("weird")).toBe("gross");
  });

  it("acrescenta o rótulo de natureza no contexto do KPI", () => {
    expect(appendBillingNatureContext("SC", "net")).toBe("SC · Líquido");
    expect(appendBillingNatureContext("Líquido", "net")).toBe("Líquido");
    expect(appendBillingNatureContext("Fat. 12 meses", "gross")).toBe(
      "Fat. 12 meses · Bruto",
    );
  });
});
