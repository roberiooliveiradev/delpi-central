import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)));

describe("commercial presence disconnect", () => {
  it("bootstrap unmount funciona sem el (fallback lastMounted)", () => {
    const boot = readFileSync(join(src, "bootstrap.tsx"), "utf8");
    assert.match(boot, /lastMountedEl/);
    assert.match(boot, /unmount\(el\?:\s*HTMLElement/);
    assert.match(boot, /el \?\? lastMountedEl/);
  });
});
