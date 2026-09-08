import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("ShellFavoritesStrip", () => {
  it("está na TopBar secondary e usa popover de favoritos", () => {
    const slots = readFileSync(join(dir, "ShellTopBarSlots.tsx"), "utf8");
    const strip = readFileSync(join(dir, "ShellFavoritesStrip.tsx"), "utf8");
    expect(slots).toMatch(/ShellFavoritesStrip/);
    expect(strip).toMatch(/sp-shell-favorites__trigger/);
    expect(strip).toMatch(/favoritesEmpty/);
    expect(strip).toMatch(/AnchoredPanelPortal/);
    expect(strip).toMatch(/delpi-ui-topbar-collapse-label/);
  });
});
