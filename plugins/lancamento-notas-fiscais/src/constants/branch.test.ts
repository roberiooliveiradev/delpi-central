import { describe, expect, it } from "vitest";
import { branchFromPathname, branchLabel } from "./branch";

describe("branchFromPathname", () => {
  it("resolve filial-01 e filial-02", () => {
    expect(branchFromPathname("/apps/lancamento-notas-fiscais/filial-01")).toBe(
      "01",
    );
    expect(branchFromPathname("/apps/lancamento-notas-fiscais/filial-02")).toBe(
      "02",
    );
  });

  it("retorna null para rota raiz ou desconhecida", () => {
    expect(branchFromPathname("/apps/lancamento-notas-fiscais")).toBeNull();
    expect(branchFromPathname(undefined)).toBeNull();
  });
});

describe("branchLabel", () => {
  it("rotula filiais conhecidas", () => {
    expect(branchLabel("01")).toMatch(/01/);
    expect(branchLabel("02")).toMatch(/02/);
  });
});
