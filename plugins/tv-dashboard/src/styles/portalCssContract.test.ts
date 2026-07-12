import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Portais vão para `document.body` — fora de `.dashboard-tv-dashboard`.
 * Causa raiz: CSS do plugin fica sem ancestral e overlay/menus caem no fluxo do documento.
 *
 * Correção canônica: `portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}` em
 * ModalShell / AnchoredPanelPortal (não soltar `.td-*` globais — anti-vazamento MFE).
 *
 * Defesa em profundidade: classes `--portal` também têm regras sem o host.
 */
const PORTAL_ROOT_SELECTORS = [
  ".td-shape-library--portal",
  ".td-icon-library-portal",
  ".td-deck-settings-accordion__body--portal",
];

const PORTAL_SCOPE_SOURCES = [
  "../components/ui/Modal.tsx",
  "../components/ComunicadoShapeLibraryMenu.tsx",
  "../components/ComunicadoInsertRibbon.tsx",
  "../components/deck/DeckSettingsAccordion.tsx",
];

describe("portal CSS contract", () => {
  it("estilos de portal não dependem só de .dashboard-tv-dashboard", () => {
    const cssPath = join(dirname(fileURLToPath(import.meta.url)), "../index.css");
    const css = readFileSync(cssPath, "utf8");

    for (const selector of PORTAL_ROOT_SELECTORS) {
      const escaped = selector.replace(/\./g, "\\.");
      const unscoped = new RegExp(`(^|,)\\s*${escaped}\\s*[,{]`, "m");
      expect(css, `${selector} deve existir fora do escopo do host`).toMatch(unscoped);
    }
  });

  it("portais do editor passam portalScopeClassName do plugin", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    for (const relative of PORTAL_SCOPE_SOURCES) {
      const source = readFileSync(join(base, relative), "utf8");
      expect(source, relative).toMatch(/portalScopeClassName/);
      expect(source, relative).toMatch(/TV_DASHBOARD_ROOT_CLASS/);
    }
  });
});
