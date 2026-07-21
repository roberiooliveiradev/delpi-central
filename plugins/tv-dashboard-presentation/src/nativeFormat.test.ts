import { describe, expect, it } from "vitest";

import { formatCurrency, formatNumber, formatPct } from "./nativeFormat";

describe("nativeFormat (pt-BR)", () => {
  it("formatPct usa vírgula decimal", () => {
    expect(formatPct(0)).toBe("0,0%");
    expect(formatPct(80)).toBe("80,0%");
    expect(formatPct(12.5)).toBe("12,5%");
  });

  it("formatCurrency formata BRL", () => {
    expect(formatCurrency(4005.33)).toMatch(/R\$\s*4\.005,33/);
    expect(formatCurrency(0)).toMatch(/R\$\s*0,00/);
  });

  it("formatNumber usa vírgula decimal", () => {
    expect(formatNumber(315.47)).toBe("315,47");
  });
});
