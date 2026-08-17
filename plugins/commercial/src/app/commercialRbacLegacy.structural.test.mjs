#!/usr/bin/env node
/**
 * Gate: zero codes/aliases RBAC legados no MFE commercial.
 */
import assert from "node:assert/strict";
import { execSync } from "node:child_process";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const pattern =
  "commercial\\.(accounts\\.view|worklist\\.view|followups\\.manage|analytics\\.view|proposals\\.(view|export)|audit\\.view|accounts\\.team\\.view|worklist\\.team\\.view|seller-portfolios\\.manage|propostas\\.)";

describe("commercial RBAC zero legado", () => {
  it("rg zero nos codes antigos sob plugins/commercial", () => {
    let out = "";
    try {
      out = execSync(`rg -n '${pattern}' . --glob '!**/node_modules/**' --glob '!**/dist/**'`, {
        cwd: root,
        encoding: "utf8",
      });
    } catch (err) {
      const status = /** @type {{ status?: number; stdout?: string }} */ (err).status;
      out = /** @type {{ stdout?: string }} */ (err).stdout || "";
      if (status === 1) {
        assert.equal((out || "").trim(), "");
        return;
      }
      throw err;
    }
    assert.equal((out || "").trim(), "", `hits legado:\n${out}`);
  });
});
