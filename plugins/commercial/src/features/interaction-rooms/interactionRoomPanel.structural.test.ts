import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const featuresRoot = join(dir, "..");

describe("InteractionRoomPanel", () => {
  it("compõe SectionCard colapsável + RoomPanel do kit sem inbox", () => {
    const source = readFileSync(join(dir, "InteractionRoomPanel.tsx"), "utf8");
    expect(source).toMatch(/CommercialSectionCard/);
    expect(source).toMatch(/collapsible:\s*true/);
    expect(source).toMatch(/defaultOpen:\s*true/);
    expect(source).toMatch(/CM_HELP\.interactionRooms\.panel/);
    expect(source).toMatch(/hint:\s*CM_HELP\.interactionRooms\.panel/);
    expect(source).toMatch(/CommercialRoomPanel/);
    expect(source).toMatch(/cm-interaction-room-embed/);
    expect(source).toMatch(/InteractionRoomPage/);
    expect(source).toMatch(/variant=\"pane\"/);
    expect(source).toMatch(/resolveInteractionRoom/);
    expect(source).toMatch(/CommercialHostDrawer/);
    expect(source).toMatch(/INTERACTION_ROOM_NARROW_QUERY|max-width: 768px/);
    expect(source).toMatch(/panelOpenRoom/);
    expect(source).not.toMatch(/InteractionRoomWorkspace/);
    expect(source).not.toMatch(/InteractionRoomsInboxPage/);
    expect(source).not.toMatch(/className=\"cm-room-panel\"/);
    expect(source).not.toMatch(/CommercialMessageThread/);
    expect(source).not.toMatch(/<textarea/);
    expect(source).not.toMatch(/cm-message-bubble/);
  });

  it("está embutido nas quatro fichas (conta, pedido, OV, OP)", () => {
    const callSites = [
      join(featuresRoot, "customers/components/CustomerOverviewSection.tsx"),
      join(featuresRoot, "customers/pages/CustomerOrderDetailPage.tsx"),
      join(featuresRoot, "open-orders/OpenOrderLineDetailPage.tsx"),
      join(featuresRoot, "open-orders/OpenOrderOpDetailPage.tsx"),
    ];
    for (const path of callSites) {
      const source = readFileSync(path, "utf8");
      expect(source).toMatch(/InteractionRoomPanel/);
    }
  });
});
