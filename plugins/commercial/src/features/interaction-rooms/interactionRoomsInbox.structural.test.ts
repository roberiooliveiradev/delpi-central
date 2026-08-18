import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomsInboxPage", () => {
  it("compõe RoomInboxList do kit sem bubble/textarea local", () => {
    const source = readFileSync(join(dir, "InteractionRoomsInboxPage.tsx"), "utf8");
    expect(source).toMatch(/CommercialRoomInboxList/);
    expect(source).toMatch(/CommercialCatalogSearchBar/);
    expect(source).toMatch(/CommercialUnderlineNav/);
    expect(source).toMatch(/listInteractionRooms/);
    expect(source).not.toMatch(/cm-message-bubble|<textarea/);
  });
});
