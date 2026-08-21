import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMoreMenu", () => {
  it("usa AnchoredPanelPortal + ContextMenuItem destructive para excluir", () => {
    const source = readFileSync(join(dir, "InteractionRoomMoreMenu.tsx"), "utf8");
    expect(source).toMatch(/AnchoredPanelPortal/);
    expect(source).toMatch(/ContextMenuItem/);
    expect(source).toMatch(/destructive/);
    expect(source).toMatch(/MoreHorizontal/);
    expect(source).toMatch(/deleteRoomActionLabel/);
    expect(source).toMatch(/CM_PORTAL_SCOPE/);
    expect(source).not.toMatch(/window\.confirm/);
  });
});
