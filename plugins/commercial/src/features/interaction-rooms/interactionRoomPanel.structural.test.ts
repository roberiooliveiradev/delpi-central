import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const featuresRoot = join(dir, "..");

describe("InteractionRoomPanel", () => {
  it("compõe SectionCard + kit e resolve lazy", () => {
    const source = readFileSync(join(dir, "InteractionRoomPanel.tsx"), "utf8");
    expect(source).toMatch(/CommercialSectionCard/);
    expect(source).toMatch(/CommercialRoomHeader/);
    expect(source).toMatch(/CommercialMessageThread/);
    expect(source).toMatch(/InteractionRoomMessageComposer/);
    expect(source).toMatch(/resolveInteractionRoom/);
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
