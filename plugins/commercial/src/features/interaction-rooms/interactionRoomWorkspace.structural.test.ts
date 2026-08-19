import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const appDir = join(dir, "../../");

describe("InteractionRoomWorkspace", () => {
  it("unifies inbox and thread with query P0 and three thread containers", () => {
    const workspace = readFileSync(join(dir, "InteractionRoomWorkspace.tsx"), "utf8");
    const app = readFileSync(join(appDir, "App.tsx"), "utf8");
    const thread = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(workspace).toMatch(/parseInteractionRoomSearch/);
    expect(workspace).toMatch(/buildInteractionRoomSearch/);
    expect(workspace).toMatch(/CommercialResizableColumns/);
    expect(workspace).toMatch(/max-width: 899px/);
    expect(workspace).toMatch(/writeInboxWidthPx/);
    expect(workspace).toMatch(/density="compact"/);
    expect(workspace).toMatch(/CommercialScopeChipBar/);
    expect(workspace).not.toMatch(/CommercialUnderlineNav/);
    expect(workspace).toMatch(/onSelectedRoomTitle/);
    expect(workspace).toMatch(/pathCurrent/);
    expect(workspace).not.toMatch(/selectRoomTitle/);
    expect(workspace).toMatch(/roomId \? \(/);
    expect(app).toMatch(/InteractionRoomWorkspace/);
    expect(app).toMatch(/interaction_room_detail/);
    expect(thread).toMatch(/cm-room-thread__header/);
    expect(thread).toMatch(/cm-room-thread__body/);
    expect(thread).toMatch(/cm-room-thread__main/);
    expect(thread).toMatch(/cm-room-thread__msgs/);
    expect(thread).toMatch(/cm-room-thread__dock/);
  });
});
