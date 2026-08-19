import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const appDir = join(dir, "../../app");

describe("CommercialHostDrawer", () => {
  it("é createHostContainedDrawerShell no portal do MFE", () => {
    const source = readFileSync(join(appDir, "commercialUi.ts"), "utf8");
    expect(source).toMatch(/createHostContainedDrawerShell/);
    expect(source).toMatch(/CommercialHostDrawer/);
    expect(source).toMatch(/portalScopeClassName: CM_PORTAL_SCOPE/);
    const page = readFileSync(join(dir, "InteractionRoomPage.tsx"), "utf8");
    expect(page).toMatch(/CommercialHostDrawer/);
    expect(page).toMatch(/cm-room-context-drawer/);
    expect(page).toMatch(/portalTarget=\{threadHost\}/);
  });
});
