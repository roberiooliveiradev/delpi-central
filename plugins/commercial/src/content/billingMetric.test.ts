import { describe, expect, it } from "vitest";

import {
  BILLING_METRIC_CONTENT,
  DEFAULT_PORTFOLIO_BILLING_METRIC,
  apiBillingMetric,
  billingMetricShortLabel,
  formatQuantityWithUnit,
  includesQuantityMetric,
  includesValueMetric,
  normalizePortfolioBillingMetric,
  quantitySeriesName,
} from "./billingMetric";

describe("billingMetric", () => {
  it("normaliza quantity e both; inválido cai em value", () => {
    expect(normalizePortfolioBillingMetric("quantity")).toBe("quantity");
    expect(normalizePortfolioBillingMetric("both")).toBe("both");
    expect(normalizePortfolioBillingMetric("weird")).toBe(
      DEFAULT_PORTFOLIO_BILLING_METRIC,
    );
    expect(DEFAULT_PORTFOLIO_BILLING_METRIC).toBe("value");
  });

  it("ambos inclui valor e quantidade; a API de série recebe value", () => {
    expect(includesValueMetric("both")).toBe(true);
    expect(includesQuantityMetric("both")).toBe(true);
    expect(includesValueMetric("quantity")).toBe(false);
    expect(includesQuantityMetric("value")).toBe(false);
    expect(apiBillingMetric("both")).toBe("value");
    expect(apiBillingMetric("quantity")).toBe("quantity");
    expect(billingMetricShortLabel("both")).toBe(BILLING_METRIC_CONTENT.both.shortLabel);
  });

  it("formata quantidade com UM e marca recorte misto", () => {
    expect(formatQuantityWithUnit(12.5, "MI")).toBe("12,500 MI");
    expect(formatQuantityWithUnit(12.5, "PC")).toBe("12,500 PC");
    expect(formatQuantityWithUnit(12.5, null)).toBe("12,500");
    expect(formatQuantityWithUnit(12.5, "MI", true)).toBe("12,500");
    expect(quantitySeriesName("MI")).toBe("Quantidade fornecida (MI)");
    expect(quantitySeriesName(null, true)).toBe("Quantidade fornecida");
    expect(quantitySeriesName("MI", true)).toBe("Quantidade fornecida");
    expect(quantitySeriesName("mi")).toBe("Quantidade fornecida (MI)");
  });
});
