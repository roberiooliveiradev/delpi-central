import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const appDir = join(dir, "../../");

describe("InteractionRoomWorkspace", () => {
  it("unifies inbox and thread with query P0 and kit conversation shell", () => {
    const workspace = readFileSync(join(dir, "InteractionRoomWorkspace.tsx"), "utf8");
    const app = readFileSync(join(appDir, "App.tsx"), "utf8");
    const thread = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    const commercialUi = readFileSync(join(appDir, "app/commercialUi.ts"), "utf8");
    expect(workspace).toMatch(/parseInteractionRoomSearch/);
    expect(workspace).toMatch(/buildInteractionRoomSearch/);
    expect(workspace).toMatch(/CommercialResizableColumns/);
    expect(workspace).toMatch(/max-width: 899px/);
    expect(workspace).toMatch(/inboxHref=\{stacked \? listHref : undefined\}/);
    expect(workspace).toMatch(/writeInboxWidthPx/);
    expect(workspace).not.toMatch(/CommercialPageHero/);
    expect(workspace).not.toMatch(/CommercialPagePath/);
    expect(workspace).not.toMatch(/CommercialUnderlineNav/);
    expect(workspace).not.toMatch(/selectRoomTitle/);
    expect(workspace).toMatch(/roomConnectionErrorBanner/);
    expect(workspace).toMatch(/CommercialStateBanner/);
    expect(workspace).toMatch(/inbox-full/);
    expect(workspace).toMatch(/transitionKey=\{/);
    expect(workspace).toMatch(/roomId \? "split" : "inbox-full"/);
    expect(workspace).not.toMatch(/split-\$\{roomId\}/);
    expect(workspace).not.toMatch(/split-\$\{/);
    expect(app).toMatch(/InteractionRoomWorkspace/);
    expect(app).toMatch(/interaction_room_detail/);
    expect(thread).toMatch(/CommercialRoomConversationShell/);
    expect(thread).toMatch(/CommercialRoomConversationChatColumn/);
    expect(commercialUi).toMatch(/createDashboardRoomConversationShell/);
  });
});
