#!/usr/bin/env node
/**
 * Gate: Ajuda dos hubs dashboard-* cita agregação SI no consolidado (unidade Todas).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const pluginsRoot = join(here, "../../..");

const HUBS = [
  "dashboard-financial",
  "dashboard-quality",
  "dashboard-supplies",
  "dashboard-hr",
  "dashboard-engineering",
  "dashboard-lmps",
  "dashboard-production",
  "dashboard-commercial",
];

const REQUIRED = [
  /meta SI|pelo SI|agregam.*SI|SI agregam/i,
  /consolidado|unidade Todas|Vazio =/i,
];

describe("dashboard hubs — Ajuda meta consolidada SI", () => {
  it("helpTooltips cita agregação SI no filtro de unidade / KPIs", () => {
    const missing = [];
    for (const hub of HUBS) {
      const path = join(pluginsRoot, hub, "src/content/helpTooltips.ts");
      let source;
      try {
        source = readFileSync(path, "utf8");
      } catch {
        missing.push(`${hub}: arquivo ausente`);
        continue;
      }
      for (const pattern of REQUIRED) {
        if (!pattern.test(source)) {
          missing.push(`${hub}: falta ${pattern}`);
        }
      }
      if (!/Só aparece aviso|se o SI não puder agregar/i.test(source)) {
        missing.push(`${hub}: falta aviso só se SI não agregar`);
      }
    }
    assert.deepEqual(missing, [], missing.join("\n"));
  });
});
