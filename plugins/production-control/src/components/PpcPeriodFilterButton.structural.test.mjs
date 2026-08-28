import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("PpcPeriodFilterButton", () => {
  it("abre filtro via AnchoredPanelPortal e não deixa inputs sempre expostos no header", () => {
    const button = readFileSync(join(root, "components/PpcPeriodFilterButton.tsx"), "utf8");
    const header = readFileSync(join(root, "components/PpcWorkspaceHeader.tsx"), "utf8");
    assert.match(button, /AnchoredPanelPortal/);
    assert.match(button, /portalScopeClassName="dashboard-production-control"/);
    assert.match(button, /type="date"/);
    assert.match(header, /PpcPeriodFilterButton/);
    assert.match(header, /periodEditable/);
    assert.doesNotMatch(header, /type="date"/);
  });
});
