import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMoreMenu", () => {
  it("ancora o popover com gap e opções renomear/excluir", () => {
    const source = readFileSync(join(dir, "InteractionRoomMoreMenu.tsx"), "utf8");
    expect(source).toMatch(/AnchoredPanelPortal/);
    expect(source).toMatch(/horizontalAlign="end"/);
    expect(source).toMatch(/gap=\{10\}/);
    expect(source).toMatch(/renameRoomActionLabel/);
    expect(source).toMatch(/deleteRoomActionLabel/);
    expect(source).toMatch(/ContextMenuDivider/);
    expect(source).toMatch(/cm-room-more-menu/);
  });
});
