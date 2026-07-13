import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("ribbon table style checks layout", () => {
  it("usa 4 colunas e classe style-check no CSS", () => {
    const css = readFileSync(resolve(__dirname, "../index.css"), "utf8");
    expect(css).toMatch(/\.td-deck-ribbon__style-checks\s*\{[^}]*grid-template-columns:\s*repeat\(4/);
    expect(css).toContain(".td-deck-ribbon__style-check");
  });

  it("Posição/tamanho ficam em faixa horizontal (não cortam Larg/Alt)", () => {
    const css = readFileSync(resolve(__dirname, "../index.css"), "utf8");
    expect(css).toMatch(
      /\.td-deck-ribbon__frame-grid\s*\{[^}]*flex-wrap:\s*nowrap/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon--compact\.td-deck-ribbon--fit\s*\{[^}]*overflow-y:\s*auto/s,
    );
  });
});
