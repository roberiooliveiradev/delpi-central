import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Portais vão para `document.body` — fora de `.dashboard-tv-dashboard`.
 * Causa raiz: CSS do plugin fica sem ancestral e overlay/menus caem no fluxo.
 *
 * Correção canônica (anti-vazamento MFE): `portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}`
 * em ModalShell / AnchoredPanelPortal — não soltar `.td-*` globais no CSS.
 */
const PORTAL_SCOPE_SOURCES = [
  "../components/ui/Modal.tsx",
  "../components/ComunicadoShapeLibraryMenu.tsx",
  "../components/ComunicadoInsertRibbon.tsx",
  "../components/deck/DeckSettingsAccordion.tsx",
];

describe("portal CSS contract", () => {
  it("portais do editor passam portalScopeClassName do plugin", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    for (const relative of PORTAL_SCOPE_SOURCES) {
      const source = readFileSync(join(base, relative), "utf8");
      expect(source, relative).toMatch(/portalScopeClassName/);
      expect(source, relative).toMatch(/TV_DASHBOARD_ROOT_CLASS/);
    }
  });
});
