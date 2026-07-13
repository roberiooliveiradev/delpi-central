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
      /\.td-deck-ribbon--compact\.td-deck-ribbon--fit\s*\{[^}]*overflow-x:\s*auto/s,
    );
  });

  it("Posição e Organizar seguem na mesma faixa (depois de Eixos / último grupo)", () => {
    const css = readFileSync(resolve(__dirname, "../index.css"), "utf8");
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__groups\s*\{[^}]*flex-wrap:\s*nowrap/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon__group-cluster\s*\{[^}]*flex-wrap:\s*nowrap/s,
    );
  });

  it("abas e tiles da ribbon têm transição suave (e respeitam reduced-motion)", () => {
    const css = readFileSync(resolve(__dirname, "../index.css"), "utf8");
    expect(css).toMatch(
      /\.td-deck-chrome__tab\s*\{[^}]*transition:[^}]*border-bottom-color/s,
    );
    expect(css).toMatch(/\.td-ribbon-tile\s*\{[^}]*transition:/s);
    expect(css).toContain("td-deck-ribbon-panel-enter");
    expect(css).toContain("@media (prefers-reduced-motion: reduce)");
    expect(css).toContain(".td-deck-chrome__ribbon-panel {\n    animation: none;");
  });
});
