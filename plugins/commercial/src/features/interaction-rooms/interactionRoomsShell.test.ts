import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("interaction room shell pages", () => {
  it("inbox e sala usam EmptyState do kit sem bubble local", () => {
    const inbox = readFileSync(join(dir, "InteractionRoomsInboxPage.tsx"), "utf8");
    const room = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    for (const source of [inbox, room]) {
      expect(source).not.toMatch(/CommercialPagePath/);
      expect(source).not.toMatch(/cm-message-bubble/);
    }
    expect(inbox).toMatch(/CommercialRoomInboxList/);
    expect(inbox).toMatch(/CommercialSectionCard/);
    expect(room).toMatch(/InteractionRoomMessageComposer/);
  });
});
