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
    expect(source).toMatch(/useInteractionInboxSync/);
    expect(source).toMatch(/CommercialPageHero/);
    expect(source).toMatch(/cm-room-inbox-search/);
    expect(source).toMatch(/reloadLabel/);
    expect(source).not.toMatch(/actions=\{\s*<CommercialActionButton/);
    expect(source).toMatch(/CustomerAvatar/);
    expect(source).toMatch(/selectedRoomId/);
    expect(source).toMatch(/customer_name/);
    expect(source).toMatch(/stopPropagation/);
    expect(source).not.toMatch(/cm-message-bubble|<textarea/);
  });
});
