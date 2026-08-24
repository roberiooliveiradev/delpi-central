import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  TOP_BAR_COLLAPSE_MODE,
  TOP_BAR_COLLAPSE_STORAGE_KEY,
  TOP_BAR_COLLAPSE_TRIGGER,
} from "../content/topBarCollapseConfig";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PluginShell TopBar collapse", () => {
  it("liga collapsible responsivo via config (hamburger + overflow)", () => {
    const source = readFileSync(join(dir, "PluginShell.tsx"), "utf8");
    expect(source).toMatch(/from "\.\.\/content\/topBarCollapseConfig"/);
    expect(source).toMatch(/collapsible/);
    expect(source).toMatch(/collapseMode=\{TOP_BAR_COLLAPSE_MODE\}/);
    expect(source).toMatch(/collapseTrigger=\{TOP_BAR_COLLAPSE_TRIGGER\}/);
    expect(source).toMatch(/TOP_BAR_COLLAPSE_TRIGGER === "manual"/);
    expect(source).toMatch(/portalScopeClassName="dashboard-commercial"/);
    expect(source).toMatch(/SHELL_NAV_CONTENT\.menuLabel/);
  });

  it("exporta modo hamburger com trigger overflow", () => {
    expect(TOP_BAR_COLLAPSE_MODE).toBe("hamburger");
    expect(TOP_BAR_COLLAPSE_TRIGGER).toBe("overflow");
    expect(TOP_BAR_COLLAPSE_STORAGE_KEY).toBe("delpi.plugin-ui.topbar.collapsed");
  });
});
