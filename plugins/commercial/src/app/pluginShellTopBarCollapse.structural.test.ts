import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  TOP_BAR_COLLAPSE_MODE,
  TOP_BAR_COLLAPSE_STORAGE_KEY,
} from "../content/topBarCollapseConfig";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PluginShell TopBar collapse", () => {
  it("liga collapsible com modo e storageKey do config", () => {
    const source = readFileSync(join(dir, "PluginShell.tsx"), "utf8");
    expect(source).toMatch(/from "\.\.\/content\/topBarCollapseConfig"/);
    expect(source).toMatch(/collapsible/);
    expect(source).toMatch(/collapseMode=\{TOP_BAR_COLLAPSE_MODE\}/);
    expect(source).toMatch(/storageKey=\{TOP_BAR_COLLAPSE_STORAGE_KEY\}/);
    expect(source).toMatch(/portalScopeClassName="dashboard-commercial"/);
    expect(source).toMatch(/SHELL_NAV_CONTENT\.collapseLabel/);
    expect(source).toMatch(/SHELL_NAV_CONTENT\.expandLabel/);
    expect(source).toMatch(/SHELL_NAV_CONTENT\.menuLabel/);
  });

  it("exporta modo e chave canônicos do config", () => {
    expect(TOP_BAR_COLLAPSE_MODE === "rail" || TOP_BAR_COLLAPSE_MODE === "hamburger").toBe(
      true,
    );
    expect(TOP_BAR_COLLAPSE_STORAGE_KEY).toBe("delpi.plugin-ui.topbar.collapsed");
  });
});
