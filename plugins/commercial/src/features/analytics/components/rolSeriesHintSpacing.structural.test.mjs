#!/usr/bin/env node
/**
 * Regressão: hint do gráfico ROL/conversão não pode reservar flex-basis alto (espaçamento fantasma).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(here, "../../../index.css"), "utf8");

describe("cm-rol-series hint spacing", () => {
  it("hint não usa flex-basis 12rem (altura fantasma ~192px)", () => {
    const block = css.split(".dashboard-commercial .cm-rol-series__hint")[1]?.split(
      ".dashboard-commercial .cm-rol-series",
    )[0];
    assert.ok(block, "bloco __hint ausente");
    assert.doesNotMatch(block, /flex:\s*1\s+1\s+12rem/);
    assert.match(block, /flex:\s*0\s+0\s+auto/);
  });
});
