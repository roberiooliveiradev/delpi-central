import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomConversationShell", () => {
  it("expõe drop + cm-room-thread com header, body, main, stage, msgs e dock", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomConversationShell.tsx"),
      "utf8",
    );
    expect(source).toMatch(/CommercialConversationFileDropLayer/);
    expect(source).toMatch(/cm-room-thread/);
    expect(source).toMatch(/cm-room-thread__header/);
    expect(source).toMatch(/cm-room-thread__body/);
    expect(source).toMatch(/cm-room-thread__main/);
    expect(source).toMatch(/cm-room-thread__stage/);
    expect(source).toMatch(/cm-room-thread__msgs/);
    expect(source).toMatch(/cm-room-thread__dock/);
    expect(source).toMatch(/InteractionRoomConversationChatColumn/);
    expect(source).toMatch(/export function InteractionRoomConversationShell/);
  });
});
