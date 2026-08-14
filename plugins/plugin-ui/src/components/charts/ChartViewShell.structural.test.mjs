#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "ChartViewShell.tsx"), "utf8");

describe("ChartViewShell (fonte)", () => {
  it("expõe slots de toolbar densificada", () => {
    assert.match(src, /granularity/);
    assert.match(src, /typeToggle/);
    assert.match(src, /overlays/);
    assert.match(src, /exportActions/);
    assert.match(src, /granularityLabel/);
    assert.match(src, /typeToggleLabel/);
    assert.match(src, /chartViewShellBemClasses/);
    assert.match(src, /__control/);
  });
});
