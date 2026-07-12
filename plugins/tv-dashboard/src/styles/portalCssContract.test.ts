import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Portais AnchoredPanelPortal vão para `document.body` — fora de
 * `.dashboard-tv-dashboard`. Seletores só aninhados no host do plugin
 * não aplicam e o menu explode (formas soltas na tela).
 */
const PORTAL_ROOT_SELECTORS = [
  ".td-shape-library--portal",
  ".td-icon-library-portal",
  ".td-deck-settings-accordion__body--portal",
];

describe("portal CSS contract", () => {
  it("estilos de portal não dependem só de .dashboard-tv-dashboard", () => {
    const cssPath = join(dirname(fileURLToPath(import.meta.url)), "../index.css");
    const css = readFileSync(cssPath, "utf8");

    for (const selector of PORTAL_ROOT_SELECTORS) {
      const escaped = selector.replace(/\./g, "\\.");
      // Aceita: ".foo," ou ".foo {" no início de regra (não só ".dashboard … .foo").
      const unscoped = new RegExp(`(^|,)\\s*${escaped}\\s*[,{]`, "m");
      expect(css, `${selector} deve existir fora do escopo do host`).toMatch(unscoped);
    }
  });
});
