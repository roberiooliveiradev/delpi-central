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
    expect(workspace).toMatch(/cm-room-workspace__grid/);
    expect(workspace).toMatch(/variant="pane"/);
    expect(app).toMatch(/InteractionRoomWorkspace/);
    expect(app).toMatch(/interaction_room_detail/);
    expect(thread).toMatch(/cm-room-thread__header/);
    expect(thread).toMatch(/cm-room-thread__msgs/);
    expect(thread).toMatch(/cm-room-thread__dock/);
  });
});
