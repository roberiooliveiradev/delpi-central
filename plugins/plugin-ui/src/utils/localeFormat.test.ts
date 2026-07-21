import { describe, expect, it } from "vitest";

import { formatCurrency, formatNumber, formatPct } from "./localeFormat";

describe("localeFormat (pt-BR)", () => {
  it("formatPct usa vírgula decimal", () => {
    expect(formatPct(0)).toBe("0,0%");
    expect(formatPct(80)).toBe("80,0%");
  });

  it("formatCurrency formata BRL", () => {
    expect(formatCurrency(1234.5)).toMatch(/R\$\s*1\.234,50/);
  });

  it("formatNumber usa vírgula", () => {
    expect(formatNumber(5.43)).toBe("5,43");
  });
});
