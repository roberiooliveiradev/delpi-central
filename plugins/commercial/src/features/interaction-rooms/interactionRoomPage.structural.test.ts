import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomPage", () => {
  it("compõe RoomHeader + MessageThread + composer com anexos", () => {
    const source = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(source).toMatch(/CommercialRoomHeader/);
    expect(source).toMatch(/CommercialMessageThread/);
    expect(source).toMatch(/resolveActions/);
    expect(source).toMatch(/createTaskFromInteractionMessage/);
    expect(source).toMatch(/InteractionRoomMessageComposer/);
    expect(source).toMatch(/useDirectoryUserLabels/);
    expect(source).toMatch(/useInteractionRoomSync/);
    expect(source).toMatch(/applyInteractionRoomRealtime/);
    expect(source).not.toMatch(/cm-message-bubble/);
    expect(source).not.toMatch(/<textarea/);
  });
});
