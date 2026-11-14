import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "PrcFlagsOpsPanel.tsx"), "utf8");

/*
 * EVA-ENGINEERING-POPOVER-ANCHOR-STANDARDIZATION-HML-01 — o modo
 * compacto deve renderizar o corpo via AnchoredPanelPortal oficial
 * (portal no document.body, flip/clamp na viewport, Escape e clique
 * externo), sem posicionamento absoluto sob o overflow do hero.
 */
describe("PrcFlagsOpsPanel — painel ancorado via portal oficial", () => {
  it("usa EngineeringAnchoredPanel (AnchoredPanelPortal do kit)", () => {
    expect(SRC).toContain("EngineeringAnchoredPanel");
    expect(SRC).toContain("anchorRef={anchorRef}");
    expect(SRC).toContain('variant="bare"');
  });

  it("painel compacto usa a variante portal e role=dialog", () => {
    expect(SRC).toContain("engineering-prc__flags-ops-body--portal");
    expect(SRC).toContain('role="dialog"');
    expect(SRC).toContain("onDismiss");
    expect(SRC).toContain("horizontalAlign");
  });

  it("modo não-compacto mantém renderização inline", () => {
    expect(SRC).toMatch(
      /compact \? \([\s\S]*EngineeringAnchoredPanel[\s\S]*\) : \([\s\S]*engineering-prc__flags-ops-body/,
    );
  });
});
