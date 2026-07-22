import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("ribbon table style checks layout", () => {
  it("usa 4 colunas e classe style-check no CSS", () => {
    const css = readFileSync(resolve(__dirname, "../index.css"), "utf8");
    expect(css).toMatch(/\.td-deck-ribbon__style-checks\s*\{[^}]*grid-template-columns:\s*repeat\(4/);
    expect(css).toContain(".td-deck-ribbon__style-check");
  });

  it("sidebar / painel usa grade 2 colunas e strip denso no kit (não vaza ribbon)", () => {
    const css = readFileSync(resolve(__dirname, "../index.css"), "utf8");
    const kitDensity = readFileSync(
      resolve(__dirname, "../../../plugin-ui/src/styles/host-density-compact.css"),
      "utf8",
    );
    const formatPane = readFileSync(
      resolve(__dirname, "../../../plugin-ui/src/styles/format-pane.css"),
      "utf8",
    );
    const sidePanelTsx = readFileSync(
      resolve(__dirname, "./deck/DeckElementSidePanel.tsx"),
      "utf8",
    );
    const ribbonShellTsx = readFileSync(
      resolve(__dirname, "./deck/DeckRibbonShell.tsx"),
      "utf8",
    );
    expect(css).toMatch(
      /\.td-deck-ribbon__style-checks--pane\s*\{[^}]*grid-template-columns:\s*repeat\(2/s,
    );
    /* Ribbon do MFE não redefine classes do kit (overrides de data-pq / preview ficam fora). */
    expect(css).not.toMatch(/\.td-deck-ribbon[^{]*\{[^}]*\.delpi-ui-/s);
    expect(kitDensity).toMatch(
      /\[data-delpi-ui-density="compact"\]\s*\.delpi-ui-table-style-strip\s*\{[^}]*flex-wrap:\s*wrap/s,
    );
    expect(formatPane).toContain(".delpi-ui-format-pane--compact");
    expect(sidePanelTsx).toContain('data-delpi-ui-density="compact"');
    expect(ribbonShellTsx).toContain('data-delpi-ui-density="compact"');
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
      /\.td-deck-ribbon--compact \.td-deck-ribbon__groups\s*\{[^}]*width:\s*100%/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon__group-cluster\s*\{[^}]*flex-wrap:\s*nowrap/s,
    );
    const shell = readFileSync(resolve(__dirname, "./deck/DeckRibbonGroups.tsx"), "utf8");
    expect(shell).toContain("RibbonGroupsRow");
    expect(shell).toContain("delpi-ui-ribbon-groups");
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

  it("colapso da ribbon resolve ícone pelo mapa de groupId", () => {
    const group = readFileSync(resolve(__dirname, "./deck/DeckRibbonGroup.tsx"), "utf8");
    const icons = readFileSync(resolve(__dirname, "./deck/deckRibbonCollapseIcons.ts"), "utf8");
    expect(group).toContain("resolveDeckRibbonCollapseIcon");
    expect(icons).toContain('"typo-font"');
    expect(icons).toContain('"organize-layers"');
    expect(icons).toContain('"slide-current"');
    expect(icons).toContain("Monitor");
    expect(icons).toContain("Clapperboard");
  });
});