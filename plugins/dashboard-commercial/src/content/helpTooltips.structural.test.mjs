#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("Ajuda — meta consolidada SI", () => {
  it("dashboard-commercial explica meta agregada pelo SI no consolidado", () => {
    const source = readFileSync(join(here, "helpTooltips.ts"), "utf8");
    assert.match(source, /meta agregam Santa Catarina/);
    assert.match(source, /META PARCIAL/);
    assert.doesNotMatch(source, /sem meta no consolidado/i);
  });
});
