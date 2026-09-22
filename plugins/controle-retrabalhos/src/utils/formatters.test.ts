import { describe, expect, it } from "vitest";

import { formatMonthLabel, formatMotivoLabel, formatObservacao } from "./formatters";

describe("formatMonthLabel", () => {
  it("uses abbreviated pt-BR month with year", () => {
    expect(
      formatMonthLabel({ mesNome: "Agosto", mesNumero: 8, ano: 2025, anoMes: "202508" }),
    ).toBe("Ago/2025");
    expect(formatMonthLabel({ mesNumero: 9, ano: 2025, anoMes: "202509" })).toBe("Set/2025");
    expect(formatMonthLabel({ anoMes: "202603" })).toBe("Mar/2026");
  });
});

describe("formatMotivoLabel", () => {
  it("joins code and full TOTVS description", () => {
    expect(formatMotivoLabel("RT", "RETRABALHO")).toBe("RT — RETRABALHO");
  });

  it("falls back to code or description alone", () => {
    expect(formatMotivoLabel("RT", "")).toBe("RT");
    expect(formatMotivoLabel("", "RETRABALHO")).toBe("RETRABALHO");
    expect(formatMotivoLabel("", null)).toBe("—");
  });
});

describe("formatObservacao", () => {
  it("returns observation text or placeholder", () => {
    expect(formatObservacao("cabos menores (9026369)")).toBe("cabos menores (9026369)");
    expect(formatObservacao("  ")).toBe("—");
  });
});
