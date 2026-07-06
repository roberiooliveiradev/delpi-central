import { describe, expect, it } from "vitest";

import { formatMonthLabel } from "./formatters";

describe("formatMonthLabel", () => {
  it("uses abbreviated pt-BR month with year", () => {
    expect(
      formatMonthLabel({ mesNome: "Agosto", mesNumero: 8, ano: 2025, anoMes: "202508" }),
    ).toBe("Ago/2025");
    expect(formatMonthLabel({ mesNumero: 9, ano: 2025, anoMes: "202509" })).toBe("Set/2025");
    expect(formatMonthLabel({ anoMes: "202603" })).toBe("Mar/2026");
  });
});
