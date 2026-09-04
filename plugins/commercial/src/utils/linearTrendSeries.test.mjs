#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("linearTrendSeries commercial", () => {
  it("reexporta o util canônico do plugin-ui sem cópia divergente", () => {
    const source = readFileSync(join(here, "linearTrendSeries.ts"), "utf8");
    assert.match(source, /from \"@delpi\/plugin-ui\/index\"/);
    assert.match(source, /buildLinearTrendValues/);
    assert.match(source, /IncompleteBucketMode/);
    assert.doesNotMatch(source, /function buildLinearTrendValues/);
  });
});
