import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PluginShell interaction rooms badge", () => {
  it("soma unread da inbox e atualiza no WS inbox.changed", () => {
    const source = readFileSync(join(dir, "PluginShell.tsx"), "utf8");
    expect(source).toMatch(/sumInboxUnreadCount/);
    expect(source).toMatch(/listInteractionRooms/);
    expect(source).toMatch(/useInteractionInboxSync/);
    expect(source).toMatch(/interaction_rooms/);
  });
});
