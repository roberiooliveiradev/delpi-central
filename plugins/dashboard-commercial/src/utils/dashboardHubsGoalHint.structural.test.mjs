#!/usr/bin/env node
/**
 * Gate: hubs dashboard-* não inventam hint «selecione unidade» no consolidado.
 * Hint só quando o SI devolve goal_scope_hint (consumido via goalDisplay do kit).
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const pluginsRoot = join(here, "../../..");

const FORBIDDEN =
  /BRANCH_GOALS_FILTER_HINT|Selecione uma unidade no filtro|Metas cadastradas apenas por unidade \(Santa Catarina/;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === "dist") continue;
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walk(full, out);
    else if (/\.(ts|tsx|js|jsx)$/.test(name) && !/\.test\./.test(name)) {
      out.push(full);
    }
  }
  return out;
}

describe("dashboard hubs — sem hint falso de meta consolidada", () => {
  it("nenhum dashboard-* inventa BRANCH_GOALS_FILTER / «selecione unidade»", () => {
    const hubs = readdirSync(pluginsRoot).filter((name) =>
      name.startsWith("dashboard-"),
    );
    assert.ok(hubs.length >= 5, `esperava vários hubs, got ${hubs.join(",")}`);

    const offenders = [];
    for (const hub of hubs) {
      const files = walk(join(pluginsRoot, hub));
      for (const file of files) {
        const source = readFileSync(file, "utf8");
        if (FORBIDDEN.test(source)) {
          offenders.push(relative(pluginsRoot, file));
        }
      }
    }

    assert.deepEqual(
      offenders,
      [],
      `hint inventado no MFE (use goal_scope_hint do SI):\n${offenders.join("\n")}`,
    );
  });
});
