import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { deckSectionHeaderBemClasses, deckSectionListBemClasses } from "./index";

describe("deck section kit", () => {
  it("emite dual-class delpi-ui + prefix", () => {
    const header = deckSectionHeaderBemClasses("td");
    expect(header.root).toContain("td-deck-section-header");
    expect(header.root).toContain("delpi-ui-deck-section-header");
    const list = deckSectionListBemClasses("td");
    expect(list.section).toContain("delpi-ui-deck-section-list__section");
    expect(list.dropHint).toContain("delpi-ui-deck-section-list__drop-hint");
  });

  it("CSS do kit está no styles.css", () => {
    const stylesEntry = readFileSync(join(__dirname, "../../styles.css"), "utf8");
    expect(stylesEntry).toContain('import "./styles/deck-section.css"');
  });

  it("menu tem Nova tela nesta seção e CSS tem drop-hint", () => {
    const menu = readFileSync(join(__dirname, "./DeckSectionContextMenu.tsx"), "utf8");
    expect(menu).toContain('"add-slide"');
    expect(menu).toContain("Nova tela nesta seção");
    expect(menu).toContain("allowDelete");
    const css = readFileSync(join(__dirname, "../../styles/deck-section.css"), "utf8");
    expect(css).toContain("drop-hint");
  });
});
