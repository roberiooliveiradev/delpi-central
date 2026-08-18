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
  });
});
