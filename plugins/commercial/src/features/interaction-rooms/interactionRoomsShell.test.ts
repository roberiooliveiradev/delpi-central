import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const dir = dirname(fileURLToPath(import.meta.url));

describe("interaction room shell pages", () => {
  it("usa EmptyState do kit e não monta bubble local", () => {
    const inbox = readFileSync(join(dir, "InteractionRoomsInboxPage.tsx"), "utf8");
    const room = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    for (const source of [inbox, room]) {
      expect(source).toMatch(/CommercialEmptyState/);
      expect(source).toMatch(/CommercialPageHero/);
      expect(source).not.toMatch(/textarea|cm-message-bubble|MentionComposer/);
    }
  });
});
