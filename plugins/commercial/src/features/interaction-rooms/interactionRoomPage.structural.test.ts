import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomPage", () => {
  it("compõe RoomHeader + MessageThread + MentionComposer do kit", () => {
    const source = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(source).toMatch(/CommercialRoomHeader/);
    expect(source).toMatch(/CommercialMessageThread/);
    expect(source).toMatch(/CommercialMentionComposer/);
    expect(source).toMatch(/getInteractionRoom/);
    expect(source).toMatch(/postInteractionMessage/);
    expect(source).not.toMatch(/cm-message-bubble/);
    expect(source).not.toMatch(/<textarea/);
  });
});
