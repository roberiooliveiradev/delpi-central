import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Docker/MF: peer opcional `@delpi/plugin-ui` vira stub vazio no Rollup.
 * Specifier canônico: `@delpi/plugin-ui/index` (nunca bare).
 * Doc: docs/05-plugin-system/microfrontends.md § 23.1
 */
const BARE_PLUGIN_UI = /from\s+["']@delpi\/plugin-ui["']/;

function walkTs(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walkTs(full, out);
    else if (/\.(ts|tsx)$/.test(name) && !name.includes(".test.")) out.push(full);
  }
  return out;
}

describe("imports @delpi/plugin-ui (MF Docker)", () => {
  it("nenhum specifier bare — só /index", () => {
    const root = join(__dirname);
    const offenders: string[] = [];
    for (const file of walkTs(root)) {
      const text = readFileSync(file, "utf8");
      if (BARE_PLUGIN_UI.test(text)) offenders.push(relative(root, file));
    }
    expect(offenders).toEqual([]);
  });
});
