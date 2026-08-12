// Gate estrutural: MFE commercial nao chama api-delpi direto.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";
import assert from "node:assert/strict";

const SRC_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const FORBIDDEN = new RegExp(
  ["apiDelpiUrl", "API_DELPI_BASE", "/apps/" + "api-delpi"].join("|"),
);

function walk(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      out.push(...walk(full));
    } else if (/\.(ts|tsx|js)$/.test(name)) {
      out.push(full);
    }
  }
  return out;
}

describe("commercial MFE — sem api-delpi direto", () => {
  it("grep zero em src/ para helpers e path da api-delpi", () => {
    const hits = [];
    for (const file of walk(SRC_ROOT)) {
      const text = readFileSync(file, "utf8");
      if (FORBIDDEN.test(text)) {
        hits.push(file.slice(SRC_ROOT.length + 1));
      }
    }
    assert.deepEqual(hits, [], `chamadas proibidas: ${hits.join(", ")}`);
  });
});
