import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const cssPath = join(dirname(fileURLToPath(import.meta.url)), "../index.css");

describe("stage pan CSS", () => {
  it("desativa hit-test de toda a árvore sob o wrap em modo pan", () => {
    const css = readFileSync(cssPath, "utf8");
    expect(css).toMatch(
      /\.td-composer__canvas-wrap--pan\s+\*\s*\{[^}]*pointer-events:\s*none\s*!important/s,
    );
  });
});
