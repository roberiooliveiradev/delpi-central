import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const appDir = join(dir, "../../app");

describe("CommercialHostDrawer", () => {
  it("é createHostContainedDrawerShell no portal do MFE e na ficha, não na página da thread", () => {
    const source = readFileSync(join(appDir, "commercialUi.ts"), "utf8");
    expect(source).toMatch(/createHostContainedDrawerShell/);
    expect(source).toMatch(/CommercialHostDrawer/);
    expect(source).toMatch(/portalScopeClassName: CM_PORTAL_SCOPE/);
    expect(source).toMatch(/createDashboardRoomConversationShell/);
    expect(source).toMatch(/CommercialRoomConversationShell/);
    expect(source).toMatch(/CommercialRoomPanel/);
    const panel = readFileSync(join(dir, "InteractionRoomPanel.tsx"), "utf8");
    expect(panel).toMatch(/CommercialHostDrawer/);
    expect(panel).toMatch(/InteractionRoomPage/);
    expect(panel).toMatch(/CommercialRoomPanel/);
    expect(panel).not.toMatch(/InteractionRoomWorkspace/);
    const page = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(page).not.toMatch(/CommercialHostDrawer/);
    expect(page).toMatch(/CommercialRoomConversationShell/);
    expect(page).toMatch(/CommercialRoomConversationChatColumn/);
    expect(page).toMatch(/CommercialRoomSidePanel/);
  });
});
