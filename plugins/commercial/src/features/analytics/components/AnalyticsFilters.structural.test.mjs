#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("AnalyticsFilters — competência", () => {
  it("usa DateField type=month (padrão dashboard), não select de meses", () => {
    const source = readFileSync(join(here, "AnalyticsFilters.tsx"), "utf8");
    assert.match(source, /CommercialDateField/);
    assert.match(source, /type="month"/);
    assert.doesNotMatch(source, /buildCompetenceOptions|emptyLabel=\"Livre\"/);
  });
});
