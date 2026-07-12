import { describe, expect, it } from "vitest";

import {
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  type DelpiKpiColorRule,
} from "./DelpiKpiCard";

describe("resolveDelpiKpiTone", () => {
  const rules: DelpiKpiColorRule[] = [
    { op: "gte", value: 90, tone: "positive" },
    { op: "lt", value: 70, tone: "negative" },
    { op: "between", value: 70, valueTo: 89.99, tone: "warning" },
  ];

  it("aplica a primeira regra que casa", () => {
    expect(resolveDelpiKpiTone(95, rules).tone).toBe("positive");
    expect(resolveDelpiKpiTone(65, rules).tone).toBe("negative");
    expect(resolveDelpiKpiTone(80, rules).tone).toBe("warning");
  });

  it("usa fallback sem regras ou valor inválido", () => {
    expect(resolveDelpiKpiTone(null, rules).tone).toBe("default");
    expect(resolveDelpiKpiTone(50, undefined, "warning").tone).toBe("warning");
  });

  it("parseia valores percentuais e com milhar", () => {
    expect(parseKpiNumericValue("86,2%")).toBeCloseTo(86.2);
    expect(parseKpiNumericValue(42)).toBe(42);
  });
});
