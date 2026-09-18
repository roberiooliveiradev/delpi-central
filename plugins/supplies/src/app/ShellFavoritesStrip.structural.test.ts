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
    expect(slots).toMatch(/SuppliesTopBarUtilityCluster/);
    expect(strip).toMatch(/SuppliesTopBarFavoritesStrip/);
    expect(strip).toMatch(/favoritesEmpty/);
    expect(strip).not.toMatch(/sp-shell-favorites__trigger/);
  });
});
