import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("PpcLiquidLoading", () => {
  it("usa orbe voice com mesh fluido, respiração e mensagem com primeiro nome", () => {
    const component = readFileSync(join(root, "components/PpcLiquidLoading.tsx"), "utf8");
    const panel = readFileSync(join(root, "components/StockBalancesReportPanel.tsx"), "utf8");
    const css = readFileSync(join(root, "index.css"), "utf8");
    assert.match(component, /ppc-liquid-loading__orb/);
    assert.match(component, /ppc-liquid-loading__mesh/);
    assert.match(component, /blob--violet/);
    assert.match(component, /liquidLoadingNamed/);
    assert.match(component, /resolveUserFirstName/);
    assert.match(panel, /PpcLiquidLoading/);
    assert.doesNotMatch(panel, /LoadingCard|createDashboardLoadingActivityCard/);
    assert.match(css, /ppc-liquid-mesh-spin/);
    assert.match(css, /ppc-liquid-breathe/);
    assert.match(css, /#6c5ce7/);
    assert.match(css, /#003866/);
  });
});
