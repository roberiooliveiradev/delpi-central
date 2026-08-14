#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(
  join(__dirname, "GroupedColumnSeriesChart.tsx"),
  "utf8",
);

describe("GroupedColumnSeriesChart (fonte)", () => {
  it("delega ao MultiTypeSeriesChart do kit", () => {
    assert.match(src, /MultiTypeSeriesChart/);
    assert.match(src, /chartType="column"/);
    assert.match(src, /bars/);
  });
});
